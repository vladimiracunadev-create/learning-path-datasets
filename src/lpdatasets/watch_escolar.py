"""Adaptador del vigía para los objetivos de aprendizaje de chilean-school-learning-path y Currículum Nacional.

La línea base sale de la instantánea oficial que guarda la fuente y conserva solo códigos y huellas, no el texto de
los objetivos. La lectura de las páginas repite la forma en que la fuente construye esa instantánea, para que ambas
huellas sean comparables.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .build import read_jsonl
from .core_build import core_folders
from .core_escolar import _git
from .watch import Adapter, fingerprints

SNAPSHOT = "sources/mineduc-curriculum-snapshot.json"
REPO = "vladimiracunadev-create/chilean-school-learning-path"
CODE = re.compile(r"(?:de (?:Actitud|Habilidad) )?[A-Z]{2}\d{2} OA[A-Z]? (?:[A-Z]{2})?[0-9A-Za-z]{1,2}")
BLOCK = re.compile(
    r'<div class="item-wrapper[^"]*">(?P<body>.*?)'
    r'(?=<div class="item-wrapper|</div>\s*</div>\s*</div>\s*<div class="sidebar|$)',
    re.S | re.I,
)
TITLE = re.compile(r'<span class="oa-title">Objetivo de aprendizaje\s+([^<]+)</span>', re.I)
DESCRIPTION = re.compile(r'field--name-description.*?field__item">(.*?)(?:<a href=|$)', re.S | re.I)


def _plain(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", fragment, flags=re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def extract(page: str) -> dict[str, str]:
    """Objetivos de una página de asignatura: {código: texto}."""
    found: dict[str, str] = {}
    unknown = 0
    for block in BLOCK.finditer(page):
        title, description = TITLE.search(block["body"]), DESCRIPTION.search(block["body"])
        if not title or not description or not _plain(description[1]):
            continue
        code = _plain(title[1])
        if CODE.fullmatch(code):
            found[code] = _plain(description[1])
        else:
            unknown += 1  # no se copia: un texto inesperado de la página no llega al informe
    if unknown:
        raise ValueError(f"{unknown} códigos con una forma desconocida")
    return found


def mentions(code: str, shown: str) -> bool:
    short = re.sub(r"^de (?:Actitud|Habilidad) ", "", code)
    return re.search(rf"\b{re.escape(short)}\b", shown) is not None


ADAPTER = Adapter(extract, mentions)


def baseline(source: Path, nivel: str) -> dict[str, Any]:
    """Línea base de un nivel, desde la instantánea confirmada en la fuente."""
    path = source / SNAPSHOT
    if not path.exists():
        raise SystemExit(f"{source} no tiene {SNAPSHOT}")
    if _git(source, "status", "--porcelain", "--untracked-files=no", "--", SNAPSHOT):
        raise SystemExit("la instantánea de la fuente tiene cambios sin confirmar")
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    records = [r for r in snapshot["records"] if r["course_slug"] == nivel]
    if not records:
        raise SystemExit(f"la instantánea no tiene objetivos de {nivel}")
    pages = []
    for record in sorted(records, key=lambda r: r["subject_slug"]):
        objectives = [{"codigo": o["code"]} | fingerprints(o["description"]) for o in record["objectives"]]
        odd = [o["codigo"] for o in objectives if not CODE.fullmatch(o["codigo"])]
        if odd:
            raise SystemExit(f"{record['subject_slug']}: códigos con una forma no prevista: {', '.join(odd[:5])}")
        pages.append(
            {
                "id": f"oa:{record['subject_slug']}",
                "titulo": f"Objetivos · {record['subject']}",
                "tipo": "oficial",
                "asignatura": record["subject_slug"],
                "url": record["subject_url"],
                "objetivos": sorted(objectives, key=lambda o: o["codigo"]),
            }
        )
    origin = {
        "repo": REPO,
        "commit": _git(source, "rev-parse", "HEAD"),
        "ruta": SNAPSHOT,
        "verificado": snapshot["verified_at"],
    }
    return {"origen": origin, "fuentes": pages}


def write_baseline(source: Path, folder: Path, nivel: str) -> int:
    """Escribe `linea-base.json` y devuelve cuántos objetivos tiene."""
    data = baseline(source, nivel)
    folder.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    (folder / "linea-base.json").write_text(text, encoding="utf-8", newline="\n")
    return sum(len(p["objetivos"]) for p in data["fuentes"])


def affected_classes(nucleo: Path) -> Counter[tuple[str, str]]:
    """Cuántas clases del núcleo dependen de cada objetivo."""
    folder = core_folders(nucleo)[0]
    return Counter((c["asignatura"], c["oa"]) for c in read_jsonl(folder / "clases.jsonl"))
