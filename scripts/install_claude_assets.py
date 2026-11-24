"""Instala las skills y los agentes de este repositorio en una carpeta de configuración de Claude Code.

    python scripts/install_claude_assets.py                 # a ~/.claude (disponibles en todos los proyectos)
    python scripts/install_claude_assets.py --dest ~/.claude --dry-run
    python scripts/install_claude_assets.py --force         # reemplaza copias distintas (deja un .bak)

No toca nada que no sea de este repositorio y nunca sobrescribe una copia distinta sin `--force`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def same(a: Path, b: Path) -> bool:
    return b.exists() and a.read_bytes() == b.read_bytes()


def plan(dest: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for src in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        pairs.append((src, dest / "skills" / src.parent.name / "SKILL.md"))
    for src in sorted((ROOT / ".claude" / "agents").glob("*.md")):
        pairs.append((src, dest / "agents" / src.name))
    return pairs


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default="~/.claude")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    dest = Path(args.dest).expanduser()
    blocked = 0
    for src, target in plan(dest):
        if same(src, target):
            print(f"= igual      {target}")
            continue
        if target.exists() and not args.force:
            print(f"! distinto   {target}  (usa --force para reemplazar; se guardará un .bak)")
            blocked += 1
            continue
        verb = "reemplaza" if target.exists() else "instala"
        print(f"+ {verb:<10} {target}")
        if args.dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.copy2(target, target.with_name(target.name + ".bak"))
        shutil.copy2(src, target)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
