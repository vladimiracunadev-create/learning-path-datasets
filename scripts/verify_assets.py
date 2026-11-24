"""Verifica las skills y los agentes de `.claude/`: frontmatter, nombres, descripciones y enlaces.

python scripts/verify_assets.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".claude" / "skills"
AGENTS = ROOT / ".claude" / "agents"
BLOB = "https://github.com/vladimiracunadev-create/learning-path-datasets/blob/main/"
LINK = re.compile(r"\]\((https://github\.com/vladimiracunadev-create/learning-path-datasets/blob/main/[^)#\s]+)")
MIN_DESCRIPTION = 120


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        return {}, text
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        head = re.match(r"^([a-z_-]+):\s*(.*)$", line)
        if head and not line.startswith(" "):
            key = head.group(1)
            value = head.group(2).strip()
            fields[key] = "" if value in (">", ">-", "|", "|-") else value
        elif key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields, match.group(2)


def check(path: Path, expected_name: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    fields, body = frontmatter(text)
    problems = []
    if not fields:
        return [f"{rel}: falta el frontmatter"]
    if fields.get("name") != expected_name:
        problems.append(f"{rel}: name {fields.get('name')!r} debería ser {expected_name!r}")
    if len(fields.get("description", "")) < MIN_DESCRIPTION:
        problems.append(f"{rel}: la descripción es demasiado corta para activarse bien")
    if len(body.split()) < 80:
        problems.append(f"{rel}: el cuerpo es demasiado corto")
    if "TODO" in text:
        problems.append(f"{rel}: contiene TODO")
    for url in LINK.findall(text):
        target = ROOT / url.removeprefix(BLOB)
        if not target.exists():
            problems.append(f"{rel}: enlace roto a {url.removeprefix(BLOB)}")
    return problems


def main() -> int:
    problems: list[str] = []
    skills = sorted(p for p in SKILLS.glob("*/SKILL.md"))
    agents = sorted(AGENTS.glob("*.md"))
    if not skills or not agents:
        problems.append("faltan skills o agentes en .claude/")
    for path in skills:
        problems += check(path, path.parent.name)
    for path in agents:
        problems += check(path, path.stem)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(skills)} skills y {len(agents)} agentes válidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
