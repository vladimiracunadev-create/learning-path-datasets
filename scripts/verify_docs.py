"""Comprueba que cada línea de implementación esté documentada según la plantilla.

python scripts/verify_docs.py
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = (
    "Propósito",
    "Casos",
    "Entradas y salidas",
    "Contrato de datos",
    "Derechos",
    "Cómo se ejecuta",
    "Pruebas",
    "Métricas",
    "Listo cuando",
    "Límites",
    "Decisiones",
)
STATES = ("PLANIFICADO", "EXPERIMENTAL", "OPERATIVO")
PENDING = "<!-- completar"
LINE_FILE = re.compile(r"^L\d{2}-[a-z0-9-]+\.md$")
LOCAL_LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)#\s]+)")
FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def sections(text: str) -> dict[str, str]:
    """Texto de cada encabezado de segundo nivel, sin contar los que estén dentro de bloques de código."""
    plain = FENCE.sub("(código)", text)
    parts = re.split(r"^## +(.+?)\s*$", plain, flags=re.M)
    return {title: body.strip() for title, body in zip(parts[1::2], parts[2::2], strict=True)}


def broken_links(path: Path) -> list[str]:
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    return [f"{path.name}: enlace local roto a {t}" for t in LOCAL_LINK.findall(text) if not (path.parent / t).exists()]


def check_line(folder: Path, line: dict[str, str]) -> list[str]:
    name = line["archivo"]
    path = folder / name
    if not path.exists():
        return [f"{line['id']}: falta el documento {name}"]
    text = path.read_text(encoding="utf-8")
    problems = []
    if not LINE_FILE.match(name) or not name.startswith(line["id"] + "-"):
        problems.append(f"{name}: el nombre debe empezar por {line['id']}-")
    if not text.startswith(f"# {line['id']} · {line['titulo']}\n"):
        problems.append(f"{name}: el título debe ser «# {line['id']} · {line['titulo']}»")
    if line["estado"] not in STATES:
        problems.append(f"{name}: estado desconocido {line['estado']!r}")
    if f"- **Estado:** `{line['estado']}`" not in text:
        problems.append(f"{name}: el estado no coincide con lineas.json ({line['estado']})")
    if PENDING in text:
        problems.append(f"{name}: quedan marcas por completar")
    found = sections(text)
    for title in SECTIONS:
        if not found.get(title):
            problems.append(f"{name}: falta o está vacía la sección «{title}»")
    return problems


def check(root: Path = ROOT, modality_lines: dict[str, str] | None = None) -> list[str]:
    """Problemas de la documentación de líneas; `modality_lines` asocia cada modalidad registrada con su línea."""
    folder = root / "docs" / "lineas"
    lines = json.loads((folder / "lineas.json").read_text(encoding="utf-8"))["lineas"]
    ids = [line["id"] for line in lines]
    problems = [f"{i}: identificador repetido" for i in sorted(set(ids)) if ids.count(i) > 1]
    index = (folder / "README.md").read_text(encoding="utf-8")
    for line in lines:
        problems += check_line(folder, line)
        if f"]({line['archivo']})" not in index:
            problems.append(f"{line['id']}: no está enlazada en docs/lineas/README.md")
    registered = {line["archivo"] for line in lines}
    problems += [
        f"{p.name}: documento sin registrar en lineas.json"
        for p in sorted(folder.glob("L*.md"))
        if LINE_FILE.match(p.name) and p.name not in registered
    ]
    missing = [t for t in SECTIONS if t not in sections((folder / "_PLANTILLA.md").read_text(encoding="utf-8"))]
    problems += [f"_PLANTILLA.md: falta la sección «{t}»" for t in missing]
    for path in [*sorted(folder.glob("*.md")), root / "docs" / "PLAN_1_BASICO.md", root / "docs" / "CORE_CONTRACT.md"]:
        problems += broken_links(path)
    for name, line_id in sorted((modality_lines or {}).items()):
        if line_id not in ids:
            problems.append(f"modalidad {name}: su línea {line_id} no está documentada")
    return problems


def registered_modalities() -> dict[str, str]:
    """Importa todo el paquete para que cada modalidad se registre; devuelve nombre y línea."""
    import lpdatasets
    from lpdatasets.modalities import REGISTRY

    for module in pkgutil.walk_packages(lpdatasets.__path__, "lpdatasets."):
        importlib.import_module(module.name)
    return {name: cls.linea for name, cls in REGISTRY.items()}


def main() -> int:
    problems = check(modality_lines=registered_modalities())
    if problems:
        print("\n".join(problems))
        return 1
    count = len(json.loads((ROOT / "docs" / "lineas" / "lineas.json").read_text(encoding="utf-8"))["lineas"])
    print(f"OK: {count} líneas documentadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
