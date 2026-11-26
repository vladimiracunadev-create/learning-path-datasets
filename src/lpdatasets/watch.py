"""Línea L04: vigía de cambios. Compara fuentes registradas con una línea base de huellas y deja un informe fechado.

No cambia contenido ni marcos. No guarda texto de las páginas: solo códigos, huellas y direcciones. Lo que no se
puede leer o interpretar se declara; nunca cuenta como «sin cambios». Una fuente que rechaza la lectura no se
vuelve a solicitar.

Cada tipo de contenido aporta un `Adapter`: cómo sacar de una página sus objetivos y cómo reconocer un código en
ella. Las demás páginas se resumen con `watch_pages` y lo revisado a mano se registra con `watch_manual`. La
referencia de una página es la última lectura que una persona aceptó o, si no hay, la primera: un cambio se sigue
informando hasta que alguien lo acepta.
"""

from __future__ import annotations

import http.client
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from .build import dumps, read_jsonl
from .watch_manual import check_manual, check_marcos
from .watch_pages import comparable, compare_page, fingerprints, snapshot, visible

AGENT = "curriculum-monitor/0.1"  # genérico: no lleva datos de una persona ni del proyecto
LIMIT = 3_000_000
PAUSE = 2.0  # segundos entre solicitudes
REJECTED = (401, 403, 451)
METHODS = ("pagina", "manual")  # además de los objetivos, que vienen en la línea base
STATES = {
    "cambio": "Con cambios",
    "ilegible": "Ilegibles: respondieron, pero no se pudo interpretar",
    "no_leida": "No leídas",
    "manual": "Revisión manual por una persona",
    "primera_lectura": "Primera lectura: sin referencia anterior",
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
READ = ("sin_cambios", "cambio", "primera_lectura")


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
    registry: list[dict[str, Any]],
    baseline: dict[str, Any],
    adapter: Adapter,
    reader: Reader,
    classes: Mapping[tuple[str, str], int],
    today: str,
    past: Sequence[dict[str, Any]] = (),
    accepted: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Una revisión fechada: compara objetivos y páginas y declara las fuentes de revisión manual."""
    results = []
    for source in baseline["fuentes"]:
        outcome = reader.read(source["url"])
        if "texto" in outcome:
            outcome = compare(source["objetivos"], outcome["texto"], adapter)
        for change in outcome.get("cambios", []):
            change["clases_afectadas"] = classes.get((source["asignatura"], change["codigo"]), 0)
        results.append(_entry(source, "objetivos", outcome))
    for source in registry:
        method = source["metodo"]
        if method not in METHODS:
            raise SystemExit(f"{source['id']}: método desconocido {method!r}")
        if method == "manual":
            outcome = {"estado": "manual", "detalle": source.get("nota", "")}
        else:
            outcome = reader.read(source["url"])
            if "texto" in outcome:
                try:
                    current = snapshot(source, outcome["texto"])
                    outcome = compare_page(reference(source, past, accepted or {}), current)
                except ValueError as error:
                    outcome = {"estado": "ilegible", "detalle": str(error)}
        results.append(_entry(source, method, outcome))
    origin = {k: baseline["origen"][k] for k in ("commit", "verificado")}
    return {"fecha": today, "linea_base": origin, "resultados": results}


def reference(
    source: dict[str, Any], past: Sequence[dict[str, Any]], accepted: Mapping[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """La lectura aceptada de una página o, si no hay, la primera que se pudo comparar."""
    chosen = accepted.get(source["id"], {}).get("pagina")
    if chosen and comparable(chosen, source):
        return chosen
    for record in past:
        for result in record["resultados"]:
            if result["id"] == source["id"] and "pagina" in result and comparable(result["pagina"], source):
                return result["pagina"]
    return None


def _entry(source: dict[str, Any], method: str, outcome: dict[str, Any]) -> dict[str, Any]:
    read = outcome["estado"] in READ
    checked = "pagina_oficial_leida" if read and source["tipo"] == "oficial" else "pagina_leida" if read else "sin_leer"
    base = {k: source[k] for k in ("id", "titulo", "tipo", "url")}
    return base | {"metodo": method, "verificacion": checked} | outcome


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


def render(record: dict[str, Any], manual: Sequence[dict[str, Any]] = ()) -> str:
    results = record["resultados"]
    compared = sum(r.get("objetivos", 0) for r in results)
    out = [
        "# Vigía curricular · 1.º básico",
        "",
        "Generado con `lpdatasets watch-report` desde la última revisión; no se edita a mano. El vigía **informa**: "
        "no cambia contenido ni marcos curriculares.",
        "",
        f"- Revisión: {record['fecha']}.",
        f"- Línea base de objetivos: instantánea oficial de la fuente verificada el "
        f"{record['linea_base']['verificado']} (commit `{record['linea_base']['commit'][:12]}`).",
        f"- Objetivos comparados: {compared}.",
        f"- Fuentes leídas: {sum(r['estado'] in READ for r in results)} de {len(results)}.",
        "",
        "| Resultado | Fuentes |",
        "|---|---:|",
        *(
            f"| {label} | {sum(r['estado'] == state for r in results)} |"
            for state, label in STATES.items()
            if state != "pendiente" or any(r["estado"] == state for r in results)
        ),
        "",
        "«Sin cambios» se limita a lo que se compara: en las páginas de objetivos, sus códigos y textos; en las demás, "
        "el texto principal o los documentos enlazados. Una primera lectura no compara nada todavía. «Clases "
        "afectadas» cuenta las del núcleo: una asignatura excluida cuenta 0.",
        "",
        "## Objetivos que cambiaron",
        "",
    ]
    changes = [(r, c) for r in results for c in r.get("cambios", [])]
    objectives = [(r, c) for r, c in changes if "codigo" in c]
    if objectives:
        out += ["| Fuente | Objetivo | Cambio | Clases afectadas |", "|---|---|---|---:|"]
        out += [
            f"| [{r['titulo']}]({r['url']}) | {c['codigo']} | {c['cambio']} | {c['clases_afectadas']} |"
            for r, c in objectives
        ]
    else:
        out.append("Ninguno entre las páginas que se pudieron comparar.")
    pages = [(r, c) for r, c in changes if "codigo" not in c]
    out += ["", "## Otras páginas que cambiaron", ""]
    if pages:
        out += ["| Fuente | Cambio | Documento |", "|---|---|---|"]
        out += [
            f"| [{r['titulo']}]({r['url']}) | {c['cambio']} | "
            f"{'<' + c['documento'] + '>' if 'documento' in c else '—'} |"
            for r, c in pages
        ]
    else:
        out.append("Ninguna entre las páginas que se pudieron comparar.")
    for state, label in STATES.items():
        group = [r for r in results if r["estado"] == state]
        if not group:
            continue
        if state == "manual":
            out += ["", f"## {label}", "", "| Fuente | Tipo | Por qué | Última revisión por una persona |"]
            out += ["|---|---|---|---|"]
            out += [
                f"| [{r['titulo']}]({r['url']}) | {r['tipo']} | {_cell(r.get('detalle', ''))} | "
                f"{_last(r['id'], manual)} |"
                for r in group
            ]
            continue
        out += ["", f"## {label}", "", "| Fuente | Tipo | Verificación | Detalle |", "|---|---|---|---|"]
        out += [
            f"| [{r['titulo']}]({r['url']}) | {r['tipo']} | {r['verificacion']} | {_cell(_detail(r))} |" for r in group
        ]
    if manual:
        out += ["", "## Registros de revisión manual", ""]
        out += ["| Fecha | Fuente | Quién | Resultado | Nota | Propuesta sobre un marco |", "|---|---|---|---|---|---|"]
        out += [
            f"| {m['fecha']} | [{m['fuente']}]({m['url']}) | {_cell(m['revisado_por'])} | {m['resultado']} | "
            f"{_cell(m['nota'])} | {_proposal(m)} |"
            for m in sorted(manual, key=lambda m: (m["fecha"], m["fuente"]))
        ]
    return "\n".join(out) + "\n"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "/").replace("[", "(").replace("]", ")")


def _last(source: str, manual: Sequence[dict[str, Any]]) -> str:
    mine = [m for m in manual if m["fuente"] == source]
    if not mine:
        return "sin revisar"
    last = max(mine, key=lambda m: m["fecha"])
    return f"{last['fecha']}, {_cell(last['revisado_por'])}: {last['resultado']}"


def _proposal(entry: dict[str, Any]) -> str:
    return f"{entry['marco']}: {entry['estado_marco']} (sin aplicar)" if entry.get("marco") else "—"


def _detail(result: dict[str, Any]) -> str:
    if "objetivos" in result:
        return f"{result['objetivos']} objetivos"
    if "pagina" in result:
        page = result["pagina"]
        parts = ["texto"] if "huella" in page else []
        parts += [f"{len(page['documentos'])} documentos"] if "documentos" in page else []
        return " y ".join(parts)
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


def _load(folder: Path, name: str, default: Any = None) -> Any:
    path = folder / name
    if default is not None and not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sources(folder: Path) -> dict[str, dict[str, Any]]:
    """Todas las fuentes registradas: las páginas de objetivos y las demás."""
    listed = _load(folder, "linea-base.json")["fuentes"] + _load(folder, "fuentes.json")["fuentes"]
    return {s["id"]: s for s in listed}


def manual_records(folder: Path) -> list[dict[str, Any]]:
    path = folder / "revisiones-manuales.jsonl"
    return read_jsonl(path) if path.exists() else []


def _write_lines(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.write_text("".join(dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def report(
    folder: Path, doc: Path, check: bool = False, marcos: Mapping[str, Mapping[str, Any]] | None = None
) -> list[str]:
    """Escribe el informe de la última revisión; con `check` no escribe y devuelve lo que esté mal.

    Con `marcos`, comprueba además los registros manuales y que ningún marco figure vigente sin fuente oficial.
    """
    past = history(folder)
    if not past:
        return [f"{folder}: no hay ninguna revisión (ejecuta lpdatasets watch)"]
    manual = manual_records(folder)
    problems = [p for record in past for p in check_review(record)]
    if marcos is not None:
        known = sources(folder)
        problems += [p for entry in manual for p in check_manual(entry, known, marcos)]
        problems += check_marcos(marcos, known)
    if problems:
        return problems
    text = render(past[-1], manual)
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
    registry = _load(folder, "fuentes.json")["fuentes"]
    past = history(folder)
    reader = Reader(fetch, refused_hosts(registry, past), pause)
    record = review(
        registry,
        _load(folder, "linea-base.json"),
        adapter,
        reader,
        classes,
        today or date.today().isoformat(),
        past,
        _load(folder, "aceptadas.json", {}),
    )
    problems = check_review(record)
    if problems:
        raise SystemExit("\n".join(problems))
    _write_lines(folder / "revisiones.jsonl", [*past, record])
    report(folder, doc)
    return record


def add_manual(folder: Path, doc: Path, entry: dict[str, Any], marcos: Mapping[str, Any]) -> dict[str, Any]:
    """Registra lo que una persona revisó; no cambia marcos ni contenido."""
    known = sources(folder)
    entry = {k: v for k, v in entry.items() if v is not None}
    if "url" not in entry and entry.get("fuente") in known:
        entry["url"] = known[entry["fuente"]]["url"]
    problems = check_manual(entry, known, marcos)
    if problems:
        raise SystemExit("\n".join(problems))
    _write_lines(folder / "revisiones-manuales.jsonl", [*manual_records(folder), entry])
    report(folder, doc)
    return entry


def accept(folder: Path, source_id: str, approver: str) -> None:
    """Una persona acepta la última lectura de una página como nueva referencia."""
    if not approver.strip():
        raise SystemExit("falta el nombre de quien aprueba")
    source = sources(folder).get(source_id)
    if source is None or source.get("metodo") != "pagina":
        raise SystemExit(
            f"{source_id}: solo se aceptan páginas sin objetivos; los objetivos cambian con `watch-baseline`"
        )
    past = history(folder)
    last = {r["id"]: r for r in past[-1]["resultados"]} if past else {}
    result = last.get(source_id, {})
    if "pagina" not in result:
        raise SystemExit(f"{source_id}: la última revisión no pudo leerla")
    accepted = _load(folder, "aceptadas.json", {})
    accepted[source_id] = {"revision": past[-1]["fecha"], "aprobado_por": approver.strip(), "pagina": result["pagina"]}
    text = json.dumps(accepted, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    (folder / "aceptadas.json").write_text(text, encoding="utf-8", newline="\n")


def summary(record: dict[str, Any]) -> tuple[str, int]:
    """Resumen de una línea y código de salida: 0 solo si cada fuente automática se leyó y no cambió."""
    states = Counter(r["estado"] for r in record["resultados"])
    clean = all(
        r["estado"] in ("sin_cambios", "primera_lectura") for r in record["resultados"] if r["metodo"] != "manual"
    )
    text = ", ".join(f"{STATES[s].split(':')[0].lower()}: {states[s]}" for s in STATES if states[s])
    return f"Revisión {record['fecha']} · {text}", 0 if clean else 1
