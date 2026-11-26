"""El documento de método debe nombrar cada pieza del repositorio, para que nada quede sin explicar."""

from __future__ import annotations

import re

import pytest

from tests.conftest import ROOT

METHOD = (ROOT / "docs" / "METODO.md").read_text(encoding="utf-8")
MODULES = sorted(p.name for p in (ROOT / "src" / "lpdatasets").rglob("*.py") if p.name != "__init__.py")
SCRIPTS = sorted(p.name for p in (ROOT / "scripts").glob("*.py"))
COMMANDS = re.findall(r'add_parser\(\s*"([a-z-]+)"', (ROOT / "src" / "lpdatasets" / "cli.py").read_text("utf-8"))
ASSETS = sorted(
    [p.stem for p in (ROOT / ".claude" / "agents").glob("*.md")]
    + [p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md")]
)


def test_inventory_is_not_empty():
    assert len(MODULES) > 5 and SCRIPTS and len(COMMANDS) > 5 and ASSETS


@pytest.mark.parametrize("name", [*MODULES, *SCRIPTS, *ASSETS])
def test_every_piece_is_mentioned(name: str):
    assert f"`{name}`" in METHOD, f"falta explicar {name} en docs/METODO.md"


@pytest.mark.parametrize("command", COMMANDS)
def test_every_command_is_mentioned(command: str):
    assert re.search(rf"`(lpdatasets )?{command}`", METHOD), f"falta la orden {command} en docs/METODO.md"
