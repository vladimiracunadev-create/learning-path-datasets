"""Humo de extremo a extremo: programa de ejemplo -> JSONL -> validación -> índice -> búsqueda."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from lpdatasets.build import build, validate_datasets
from lpdatasets.vector import build_index, search

SAMPLE = {
    "redes.md": "# Redes\n\n## Puertos\n\n"
    + "Un puerto es un número que indica qué servicio de un equipo debe recibir una conexión de red. " * 3,
    "finanzas.md": "# Finanzas\n\n## Interés compuesto\n\n"
    + "El interés compuesto calcula los intereses sobre el capital y sobre los intereses acumulados. " * 3,
}


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        course = base / "curso"
        course.mkdir()
        for name, text in SAMPLE.items():
            (course / name).write_text(text, encoding="utf-8")
        build("markdown-course", base / "datasets", source=course, pack_id="smoke", dominio="demo")
        problems = validate_datasets(base / "datasets")
        if problems:
            print("\n".join(problems))
            return 1
        count = build_index(base / "datasets", base / "index")
        top = search(base / "index", "qué es un puerto", k=1)[0]
        if "Puertos" not in top["entrada"]:
            print(f"búsqueda inesperada: {top['entrada']}")
            return 1
        print(f"OK: humo extremo a extremo ({count} registros indexados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
