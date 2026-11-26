"""Adaptador de chilean-school-learning-path al núcleo, por ahora solo para 1.º básico.

Clases desde el catálogo; guía docente, cuaderno del estudiante y orientación por OA desde las fichas; ítems desde
el mismo lector que genera el dataset v1.0, de modo que ambos concilian por identificador.

El texto oficial de los OA no se copia: las experiencias integradas lo citan literalmente en la fuente, y aquí se
sustituye por su código. En el resto, una coincidencia larga se marca para revisión sin alterar el contenido.
"""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from .core import AUDIENCES, CONTRACT, Entity
from .core_build import write_core
from .packs import escolar_chile as pack

SUPPORTED = ("1-basico",)
NOTEBOOK = "### Cuaderno del estudiante"
ANSWERS = "**Solucionario razonado**"
ORIENTATION = "**Explicación pedagógica.**"
HIDDEN_SOLUTION = ("ejercicio_cerrado", "autoevaluacion", "actividad_abierta")
EXCLUSION_REASON = "requiere un educador tradicional y no debe usarse sin su participación"
REDACT_WORDS = 6  # tramo mínimo que se omite en las experiencias integradas
MATCH_WORDS = 8  # tramo mínimo que se considera coincidencia con texto oficial
SECTION = re.compile(r"^(### .*?\{#(cl-\d+)\})[ \t]*$", re.M)
TITLE = re.compile(r"^### Clase \d+ de \d+: (.+?) \{#cl-\d+\}$")
WORD = re.compile(r"\w+")
RIGHTS = {
    "licencia": pack.LICENCIA,
    "titular": "Vladimir Acuña",
    "origen": "propio",
    "atribucion": "«Trayectoria Escolar Chile», por Vladimir Acuña (vladimiracunadev-create), CC BY-NC-SA 4.0. "
    "https://github.com/vladimiracunadev-create/chilean-school-learning-path. "
    "Reestructurado por learning-path-datasets.",
}


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group().lower(), m.start(), m.end()) for m in WORD.finditer(text)]


def _grams(words: list[str], size: int) -> set[tuple[str, ...]]:
    return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}


def redact(text: str, official: str, code: str) -> tuple[str, int]:
    """Sustituye cada tramo copiado del texto oficial por su código; devuelve el texto y cuántos tramos omitió."""
    source = [w for w, _, _ in _tokens(unicodedata.normalize("NFC", official))]
    size = min(REDACT_WORDS, len(source))
    if size < 3:
        return text, 0
    grams = _grams(source, size)
    tokens = _tokens(text)
    covered: set[int] = set()
    for i in range(len(tokens) - size + 1):
        if tuple(t[0] for t in tokens[i : i + size]) in grams:
            covered.update(range(i, i + size))
    spans: list[list[int]] = []
    for i in sorted(covered):
        if spans and i == spans[-1][1] + 1:
            spans[-1][1] = i
        else:
            spans.append([i, i])
    for first, last in reversed(spans):
        text = text[: tokens[first][1]] + f"[texto oficial no incluido: {code}]" + text[tokens[last][2] :]
    return text, len(spans)


class OfficialIndex:
    """Reconoce tramos largos tomados de la redacción oficial de cualquier OA del nivel."""

    def __init__(self, objectives: dict[str, str]) -> None:
        self.grams: dict[tuple[str, ...], str] = {}
        for code, official in sorted(objectives.items()):
            words = [w for w, _, _ in _tokens(unicodedata.normalize("NFC", official))]
            for gram in _grams(words, MATCH_WORDS):
                self.grams.setdefault(gram, code)

    def match(self, text: str) -> str | None:
        words = [w for w, _, _ in _tokens(unicodedata.normalize("NFC", text))]
        for i in range(len(words) - MATCH_WORDS + 1):
            code = self.grams.get(tuple(words[i : i + MATCH_WORDS]))
            if code:
                return code
        return None


def _git(source: Path, *args: str) -> str:
    done = subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True, check=False)
    if done.returncode:
        raise SystemExit(f"git falló en {source}: {done.stderr.strip()}")
    return done.stdout.strip()


def _sections(text: str) -> dict[str, tuple[str, str]]:
    """Encabezado y cuerpo de cada clase de una ficha; el cuerpo termina en el siguiente «## »."""
    parts = SECTION.split(text)
    return {
        parts[i + 1]: (parts[i], re.split(r"^## ", parts[i + 2], maxsplit=1, flags=re.M)[0].strip())
        for i in range(1, len(parts), 3)
    }


def split_class(body: str, code: str) -> tuple[str, str]:
    """Separa la sección de una clase desarrollada en guía docente y cuaderno del estudiante.

    La guía reúne la planificación y todo lo que sigue al solucionario; el cuaderno queda entre ambos.
    """
    if body.count(NOTEBOOK) != 1 or body.count(ANSWERS) != 1 or body.index(NOTEBOOK) > body.index(ANSWERS):
        raise SystemExit(f"{code}: no se puede separar el cuaderno del solucionario sin riesgo de revelar respuestas")
    plan, rest = body.split(NOTEBOOK)
    notebook, answers = rest.split(ANSWERS)
    return f"{plan.strip()}\n\n{ANSWERS}{answers.rstrip()}", f"{NOTEBOOK}{notebook.rstrip()}"


def _marco(subject: str) -> str:
    if subject == "ingles-propuesta":
        return "cl-propuesta-ingles-1b"
    if subject in ("lengua-es", "lengua-en"):
        return "sin-marco-oficial"
    return "cl-bases-1-6"


def class_id(nivel: str, code: str, number: int) -> str:
    return f"{pack.PACK_ID}:{nivel}:{pack._slug(code)}:c{number:02d}"


def _base(entity: str, ident: str, nivel: str, subject: str, commit: str, path: str) -> Entity:
    return {
        "contrato": CONTRACT,
        "entidad": entity,
        "id": ident,
        "marco": _marco(subject),
        "nivel": nivel,
        "idioma": "es",
        "procedencia": {"repo": pack.SOURCE_REPO, "commit": commit, "ruta": path},
        "derechos": dict(RIGHTS),
        "revision": pack.REVISION,
    }


def _resource(base: Entity, text: str, audience: list[str], role: str, clase: str | None, **extra: Any) -> Entity:
    return {
        **base,
        "medio": "text/markdown",
        "publico": audience,
        "clase_id": clase,
        "texto": text,
        "extra": {"rol": role, **extra},
    }


def _item(record: dict[str, Any], nivel: str, official: OfficialIndex) -> Entity:
    number = record["clase"]
    content = {"enunciado": record["entrada"], "respuesta": record["salida"]}
    if record.get("razon"):
        content["razon"] = record["razon"]
    extra = {**record.get("extra", {}), "verificable": record["verificable"], "unidad": record["unidad"]}
    found = official.match(" ".join(content.values()))
    if found:
        extra["coincide_texto_oficial"] = found
    subject = record["asignatura"]
    return {
        **_base("item", record["id"], nivel, subject, record["fuente"]["commit"], record["fuente"]["ruta"]),
        "idioma": record["idioma"],
        "asignatura": subject,
        "tipo": record["tipo"],
        "publico": list(AUDIENCES),
        "publico_solucion": ["docente"] if record["tipo"] in HIDDEN_SOLUTION else list(AUDIENCES),
        "contenido": content,
        "clase_id": None if number is None else class_id(nivel, record["unidad"], number),
        "habilidades": list(record["habilidades"]),
        "dificultad": record["dificultad"],
        "extra": extra,
    }


def entities(source: Path, nivel: str = "1-basico") -> tuple[list[Entity], dict[str, Any]]:
    """Entidades del núcleo y los datos de cobertura para el manifiesto."""
    if nivel not in SUPPORTED:
        raise SystemExit(f"el núcleo solo cubre {', '.join(SUPPORTED)}")
    source = Path(source).resolve()
    catalog_file = source / "curriculum" / "catalog.json"
    if not catalog_file.exists():
        raise SystemExit(f"{source} no parece ser chilean-school-learning-path")
    if _git(source, "status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("la fuente tiene cambios sin confirmar: la exportación no sería reproducible")
    commit = _git(source, "rev-parse", "HEAD")
    catalog = [c for c in json.loads(catalog_file.read_text(encoding="utf-8"))["classes"] if c["course_slug"] == nivel]
    objectives = {c["oa_code"]: c["oa_text"] for c in catalog}
    official = OfficialIndex(objectives)
    included = [c for c in catalog if c["subject_slug"] not in pack.EXCLUDED_SUBJECTS]
    result: list[Entity] = []
    fichas: dict[str, tuple[str, dict[str, tuple[str, str]]]] = {}
    omitted: dict[str, int] = {}

    def clean(ident: str, text: str, code: str, integrated: bool) -> tuple[str, dict[str, Any]]:
        if integrated:
            text, count = redact(text, objectives[code], code)
            if official.match(text):
                raise SystemExit(f"{ident}: queda texto oficial después de omitirlo")
            if count:
                omitted[ident] = omitted.get(ident, 0) + count
                return text, {"texto_oficial_omitido": count}
            return text, {}
        found = official.match(text)
        return text, {"coincide_texto_oficial": found} if found else {}

    for row in included:
        path, anchor = row["path"].split("#")
        if path not in fichas:
            text = (source / path).read_text(encoding="utf-8")
            fichas[path] = (text, _sections(text))
        if anchor not in fichas[path][1]:
            raise SystemExit(f"{path}: falta la clase {anchor} del catálogo")
        heading, body = fichas[path][1][anchor]
        match = TITLE.match(heading)
        if not match:
            raise SystemExit(f"{path}: encabezado de clase inesperado: {heading}")
        code, number, subject = row["oa_code"], row["lesson"], row["subject_slug"]
        integrated = row["editorial_status"] == "integrada"
        ident = class_id(nivel, code, number)
        title, title_notes = clean(ident, match.group(1), code, integrated)
        result.append(
            {
                **_base("clase", ident, nivel, subject, commit, path),
                "asignatura": subject,
                "oa": code,
                "numero": number,
                "estado_editorial": row["editorial_status"],
                "titulo": title,
                "extra": {"codigo_clase": row["class_code"], "eje": row["axis"], "fase": row["phase"], **title_notes},
            }
        )
        guide, notebook = (body, None) if integrated else split_class(body, ident)
        guide, notes = clean(f"{ident}:guia", guide, code, integrated)
        base = _base("recurso", f"{ident}:guia", nivel, subject, commit, path)
        result.append(_resource(base, guide, ["docente"], "guia_docente", ident, oa=code, **notes))
        if notebook:
            notebook, notes = clean(f"{ident}:cuaderno", notebook, code, integrated)
            base = _base("recurso", f"{ident}:cuaderno", nivel, subject, commit, path)
            result.append(_resource(base, notebook, list(AUDIENCES), "cuaderno_estudiante", ident, oa=code, **notes))

    by_path = {c["path"].split("#")[0]: c for c in included}
    for path, (text, _) in sorted(fichas.items()):
        if ORIENTATION not in text:
            continue
        row = by_path[path]
        code = row["oa_code"]
        ident = f"{pack.PACK_ID}:{nivel}:{pack._slug(code)}:orientacion"
        block = ORIENTATION + re.split(r"^## ", text.split(ORIENTATION, 1)[1], maxsplit=1, flags=re.M)[0].rstrip()
        block, notes = clean(ident, block, code, row["editorial_status"] == "integrada")
        base = _base("recurso", ident, nivel, row["subject_slug"], commit, path)
        result.append(_resource(base, block, ["docente"], "orientacion_oa", None, oa=code, **notes))

    items = [_item(r, nivel, official) for r in pack.records(source, nivel)]
    result += items
    excluded = [
        {"asignatura": s, "clases": sum(c["subject_slug"] == s for c in catalog), "motivo": EXCLUSION_REASON}
        for s in sorted({c["subject_slug"] for c in catalog} & pack.EXCLUDED_SUBJECTS)
    ]
    states = {s: sum(c["editorial_status"] == s for c in included) for s in ("desarrollada", "integrada")}
    info = {
        "pack": pack.PACK_ID,
        "nivel": nivel,
        "fuente": pack.SOURCE_REPO,
        "commit_fuente": commit,
        "cobertura": {
            "catalogo": len(catalog),
            "representadas": len(included),
            "por_estado_editorial": states,
            "excluidas": excluded,
            "oa_catalogo": len(objectives),
            "oa_representados": len({c["oa_code"] for c in included}),
        },
        "texto_oficial_omitido": {"entidades": len(omitted), "tramos": sum(omitted.values())},
    }
    return result, info


def export(source: Path, out: Path, nivel: str = "1-basico") -> Path:
    """Escribe el núcleo del nivel en `out/<pack>/<nivel>/` y devuelve la carpeta."""
    result, info = entities(source, nivel)
    folder = out / pack.PACK_ID / nivel
    write_core(folder, result, info)
    return folder
