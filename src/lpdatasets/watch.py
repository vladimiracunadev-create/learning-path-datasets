"""Línea L04: vigía de cambios. Compara fuentes registradas con una línea base de huellas y deja un informe fechado.

No cambia contenido ni marcos. No guarda texto de las páginas: solo códigos, huellas y direcciones. Lo que no se
puede leer o interpretar se declara; nunca cuenta como «sin cambios». Una fuente que rechaza la lectura no se
vuelve a solicitar.

Cada tipo de contenido aporta un `Adapter`: cómo sacar de una página sus objetivos y cómo reconocer un código en
ella.
"""

from __future__ import annotations

import hashlib
import html
import http.client
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable, Mapping
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from .build import dumps, read_jsonl

AGENT = "curriculum-monitor/0.1"  # genérico: no lleva datos de una persona ni del proyecto
LIMIT = 3_000_000
PAUSE = 2.0  # segundos entre solicitudes
REJECTED = (401, 403, 451)
METHODS = ("pagina", "canal", "manual")  # además de los objetivos, que vienen en la línea base
STATES = {
    "cambio": "Con cambios",
    "ilegible": "Ilegibles: respondieron, pero no se pudo interpretar",
    "no_leida": "No leídas",
    "manual": "Revisión manual por una persona",
    "pendiente": "Registradas, aún sin comprobación automática",
    "sin_cambios": "Sin cambios",
}


class Page(NamedTuple):
    status: int  # 0 si no hubo respuesta utilizable
    text: str = ""
    url: str = ""  # dirección final


class Adapter(NamedTuple):
    extract: Callable[[str], dict[str, str]]  # página → {código: texto}; ValueError si no la entiende
    mentions: Callable[[str, str], bool]  # (código, texto visible de la página) → aparece


Fetch = Callable[[str], Page]


def fingerprints(text: str) -> dict[str, str]:
    """Huella exacta y huella sin forma (ignora mayúsculas, espacios y puntuación)."""
    exact = " ".join(unicodedata.normalize("NFC", text).split())
    return {"huella": _hash(exact), "huella_sin_forma": _hash(re.sub(r"\W+", "", exact.lower()))}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def visible(page: str) -> str:
    """Texto visible de una página, sin programas ni estilos."""
    clean = re.sub(r"<(script|style)\b[\s\S]*?</\1>", " ", page, flags=re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", clean)).split())


def http_fetch(url: str) -> Page:
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(LIMIT + 1)
            if len(raw) > LIMIT:
                return Page(0, "", response.geturl())
            return Page(response.status, raw.decode("utf-8", errors="replace"), response.geturl())
    except urllib.error.HTTPError as error:
        return Page(error.code, "", url)
    except (OSError, http.client.HTTPException):
        return Page(0, "", url)


class Reader:
    """Lee direcciones registradas respetando `robots.txt` y los rechazos anteriores."""

    def __init__(self, fetch: Fetch, refused: set[str], pause: float = PAUSE) -> None:
        self.fetch, self.refused, self.pause = fetch, set(refused), pause
        self.robots: dict[str, RobotFileParser | None] = {}
        self.asked = 0

    def _get(self, url: str) -> Page:
        if self.asked:
            time.sleep(self.pause)
        self.asked += 1
        return self.fetch(url)

    def read(self, url: str) -> dict[str, Any]:
        """`{"texto": …}` si se leyó; si no, `estado`, `detalle` y, cuando lo hubo, `codigo_http`."""
        parts = urlsplit(url)
        host = parts.netloc
        if parts.scheme != "https":
            return _unread("solo se leen direcciones https")
        if host in self.refused:
            return {"estado": "manual", "detalle": "el sitio no admite lectura automatizada; no se solicitó"}
        if host not in self.robots:
            rules = self._get(f"https://{host}/robots.txt")
            if rules.status in REJECTED:
                self.refused.add(host)
                return _unread("el sitio rechazó la lectura de robots.txt", rules.status)
            if rules.status not in (200, 404):
                return _unread("no se pudo leer robots.txt", rules.status)
            parser = RobotFileParser()
            parser.parse(rules.text.splitlines() if rules.status == 200 else [])
            self.robots[host] = parser
        if not self.robots[host].can_fetch(AGENT, url):
            return _unread("robots.txt no permite leerla")
        page = self._get(url)
        if page.status in REJECTED:
            self.refused.add(host)
            return _unread("el sitio rechazó la lectura", page.status)
        if page.status != 200:
            return _unread("no hubo una respuesta utilizable", page.status)
        if urlsplit(page.url).netloc != host:
            return _unread("redirigió a otro sitio")
        return {"texto": page.text}


def _unread(detail: str, status: int = 0) -> dict[str, Any]:
    return {"estado": "no_leida", "detalle": detail} | ({"codigo_http": status} if status else {})


def compare(expected: list[dict[str, str]], page: str, adapter: Adapter) -> dict[str, Any]:
    """Estado de una página de objetivos frente a la línea base."""
    base = {o["codigo"]: o for o in expected}
    try:
        found = adapter.extract(page)
    except ValueError as error:
        return {"estado": "ilegible", "detalle": str(error)}
    missing = sorted(set(base) - set(found))
    shown = visible(page)
    unparsed = [code for code in missing if adapter.mentions(code, shown)]
    if not found or unparsed or len(missing) * 2 > len(base):
        detail = f"se interpretaron {len(set(base) & set(found))} de {len(base)} objetivos esperados"
        return {"estado": "ilegible", "detalle": detail + "; la página pudo cambiar de forma"}
    changes = [{"codigo": code, "cambio": "quitado"} for code in missing]
    for code, text in found.items():
        new = fingerprints(text)
        if code not in base:
            changes.append({"codigo": code, "cambio": "nuevo"} | new)
        elif new["huella"] != base[code]["huella"]:
            kind = "forma" if new["huella_sin_forma"] == base[code]["huella_sin_forma"] else "texto"
            changes.append({"codigo": code, "cambio": kind} | new)
    result: dict[str, Any] = {"estado": "cambio" if changes else "sin_cambios", "objetivos": len(base)}
    if changes:
        result["cambios"] = sorted(changes, key=lambda c: c["codigo"])
    return result


def review(
    registry: list[dict[str, str]],
    baseline: dict[str, Any],
    adapter: Adapter,
    reader: Reader,
    classes: Mapping[tuple[str, str], int],
    today: str,
) -> dict[str, Any]:
    """Una revisión fechada: compara las páginas de objetivos y declara el resto de las fuentes."""
    results = []
    for source in baseline["fuentes"]:
        outcome = reader.read(source["url"])
        if "texto" in outcome:
            outcome = compare(source["objetivos"], outcome["texto"], adapter)
        for change in outcome.get("cambios", []):
            change["clases_afectadas"] = classes.get((source["asignatura"], change["codigo"]), 0)
        results.append(_entry(source, outcome))
    for source in registry:
        if source["metodo"] not in METHODS:
            raise SystemExit(f"{source['id']}: método desconocido {source['metodo']!r}")
        if source["metodo"] == "manual":
            outcome = {"estado": "manual", "detalle": source.get("nota", "")}
        else:
            outcome = {"estado": "pendiente", "detalle": source.get("nota", "")}
        results.append(_entry(source, outcome))
    origin = {k: baseline["origen"][k] for k in ("commit", "verificado")}
    return {"fecha": today, "linea_base": origin, "resultados": results}


def _entry(source: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    read = outcome["estado"] in ("sin_cambios", "cambio")
    checked = "pagina_oficial_leida" if read and source["tipo"] == "oficial" else "pagina_leida" if read else "sin_leer"
    return {k: source[k] for k in ("id", "titulo", "tipo", "url")} | {"verificacion": checked} | outcome


def check_review(record: dict[str, Any]) -> list[str]:
    """Una revisión sin fecha o con una fuente sin dirección no se acepta."""
    problems = []
    try:
        date.fromisoformat(str(record.get("fecha")))
    except ValueError:
        problems.append("la revisión no tiene una fecha válida")
    if not record.get("resultados"):
        problems.append("la revisión no tiene resultados")
    for r in record.get("resultados", []):
        if urlsplit(str(r.get("url", ""))).scheme != "https":
            problems.append(f"{r.get('id')}: falta una dirección https")
        if r.get("estado") not in STATES:
            problems.append(f"{r.get('id')}: estado desconocido {r.get('estado')!r}")
    return problems


def render(record: dict[str, Any]) -> str:
    results = record["resultados"]
    compared = sum(r.get("objetivos", 0) for r in results)
    out = [
        "# Vigía curricular · 1.º básico",
        "",
        "Generado con `lpdatasets watch-report` desde la última revisión; no se edita a mano. El vigía **informa**: "
        "no cambia contenido ni marcos curriculares.",
        "",
        f"- Revisión: {record['fecha']}.",
        f"- Línea base: instantánea oficial de la fuente verificada el {record['linea_base']['verificado']} "
        f"(commit `{record['linea_base']['commit'][:12]}`).",
        f"- Objetivos comparados: {compared}.",
        f"- Fuentes comprobadas: {sum(r['estado'] in ('sin_cambios', 'cambio') for r in results)} de {len(results)}.",
        "",
        "| Resultado | Fuentes |",
        "|---|---:|",
        *(f"| {label} | {sum(r['estado'] == state for r in results)} |" for state, label in STATES.items()),
        "",
        "«Sin cambios» significa que los códigos y textos de los objetivos coinciden con la línea base; no revisa "
        "otras partes de la página. «Clases afectadas» cuenta las del núcleo: una asignatura excluida cuenta 0.",
        "",
        "## Objetivos que cambiaron",
        "",
    ]
    changes = [(r, c) for r in results for c in r.get("cambios", [])]
    if changes:
        out += ["| Fuente | Objetivo | Cambio | Clases afectadas |", "|---|---|---|---:|"]
        out += [
            f"| [{r['titulo']}]({r['url']}) | {c['codigo']} | {c['cambio']} | {c['clases_afectadas']} |"
            for r, c in changes
        ]
    else:
        out.append("Ninguno entre las páginas que se pudieron comparar.")
    for state, label in STATES.items():
        group = [r for r in results if r["estado"] == state]
        if not group:
            continue
        out += ["", f"## {label}", "", "| Fuente | Tipo | Verificación | Detalle |", "|---|---|---|---|"]
        out += [
            f"| [{r['titulo']}]({r['url']}) | {r['tipo']} | {r['verificacion']} | {_detail(r).replace('|', '/')} |"
            for r in group
        ]
    return "\n".join(out) + "\n"


def _detail(result: dict[str, Any]) -> str:
    if "objetivos" in result:
        return f"{result['objetivos']} objetivos"
    code = f" (HTTP {result['codigo_http']})" if "codigo_http" in result else ""
    return result.get("detalle", "") + code


def history(folder: Path) -> list[dict[str, Any]]:
    path = folder / "revisiones.jsonl"
    return read_jsonl(path) if path.exists() else []


def refused_hosts(registry: list[dict[str, str]], past: list[dict[str, Any]]) -> set[str]:
    """Sitios que no se solicitan: los de revisión manual y los que ya rechazaron la lectura."""
    manual = {urlsplit(s["url"]).netloc for s in registry if s["metodo"] == "manual"}
    return manual | {
        urlsplit(r["url"]).netloc for record in past for r in record["resultados"] if r.get("codigo_http") in REJECTED
    }


def report(folder: Path, doc: Path, check: bool = False) -> list[str]:
    """Escribe el informe de la última revisión; con `check` no escribe y devuelve lo que esté mal."""
    past = history(folder)
    if not past:
        return [f"{folder}: no hay ninguna revisión (ejecuta lpdatasets watch)"]
    problems = [p for record in past for p in check_review(record)]
    if problems:
        return problems
    text = render(past[-1])
    if check:
        current = doc.read_text(encoding="utf-8") if doc.exists() else None
        return [] if current == text else [f"{doc}: desactualizado (ejecuta lpdatasets watch-report)"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(text, encoding="utf-8", newline="\n")
    return []


def run(
    folder: Path,
    classes: Mapping[tuple[str, str], int],
    adapter: Adapter,
    doc: Path,
    fetch: Fetch = http_fetch,
    today: str | None = None,
    pause: float = PAUSE,
) -> dict[str, Any]:
    """Revisa las fuentes de `folder`, añade la revisión a su historial y escribe el informe."""
    registry = json.loads((folder / "fuentes.json").read_text(encoding="utf-8"))["fuentes"]
    baseline = json.loads((folder / "linea-base.json").read_text(encoding="utf-8"))
    past = history(folder)
    reader = Reader(fetch, refused_hosts(registry, past), pause)
    record = review(registry, baseline, adapter, reader, classes, today or date.today().isoformat())
    problems = check_review(record)
    if problems:
        raise SystemExit("\n".join(problems))
    lines = "".join(dumps(r) + "\n" for r in [*past, record])
    (folder / "revisiones.jsonl").write_text(lines, encoding="utf-8", newline="\n")
    report(folder, doc)
    return record


def summary(record: dict[str, Any]) -> tuple[str, int]:
    """Resumen de una línea y código de salida: 0 solo si cada página de objetivos se leyó y sigue igual."""
    states = Counter(r["estado"] for r in record["resultados"])
    clean = all(r["estado"] == "sin_cambios" for r in record["resultados"] if r["id"].startswith("oa:"))
    text = ", ".join(f"{STATES[s].split(':')[0].lower()}: {states[s]}" for s in STATES if states[s])
    return f"Revisión {record['fecha']} · {text}", 0 if clean else 1
