"""Pack «markdown-course»: adaptador genérico para cualquier programa escrito en Markdown.

Divide cada archivo `.md` por encabezados (## y ###) y emite un registro «concepto» por sección,
con el recorrido de encabezados como entrada y el texto de la sección como salida. Sirve como punto
de partida para sumar otros programas de aprendizaje; es experimental y no ha sido probado sobre
los repositorios reales de cada programa.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..schema import SCHEMA_VERSION, partition_for
from . import Record, register

HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
MIN_WORDS = 25


def _git_commit(source: Path) -> str:
    out = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return out.stdout.strip() or "desconocido"


def _sections(text: str) -> Iterator[tuple[str, str]]:
    stack: list[tuple[int, str]] = []
    body: list[str] = []
    in_code = False

    def flush() -> tuple[str, str] | None:
        content = " ".join(" ".join(body).split())
        if stack and len(content.split()) >= MIN_WORDS:
            return " > ".join(title for _, title in stack), content
        return None

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING.match(line)
        if match:
            done = flush()
            if done:
                yield done
            body = []
            level, title = len(match.group(1)), match.group(2)
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        else:
            body.append(line)
    done = flush()
    if done:
        yield done


@register("markdown-course")
def records(
    source: str | Path,
    nivel: str = "general",
    pack_id: str = "markdown-course",
    dominio: str = "general",
    licencia: str = "no-declarada",
    idioma: str = "es",
    repo: str = "local",
    **_: Any,
) -> Iterator[Record]:
    source = Path(source).resolve()
    commit = _git_commit(source)
    for path in sorted(source.rglob("*.md")):
        rel = path.relative_to(source).as_posix()
        if any(part.startswith(".") for part in path.relative_to(source).parts):
            continue
        for title, content in _sections(path.read_text(encoding="utf-8")):
            digest = hashlib.sha1(f"{rel}|{title}".encode()).hexdigest()[:10]  # noqa: S324 - solo identificador
            yield {
                "schema": SCHEMA_VERSION,
                "id": f"{pack_id}:{digest}",
                "pack": pack_id,
                "dominio": dominio,
                "nivel": nivel,
                "asignatura": path.stem.lower(),
                "unidad": rel,
                "clase": None,
                "tipo": "concepto",
                "dificultad": None,
                "entrada": title,
                "salida": content,
                "razon": None,
                "idioma": idioma,
                "habilidades": [],
                "verificable": False,
                "fuente": {"repo": repo, "commit": commit, "ruta": rel},
                "licencia": licencia,
                "revision": "ia_asistida_sin_revision_humana",
                "particion": partition_for(pack_id, rel),
            }
