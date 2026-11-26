from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.conftest import ROOT
from tests.test_assets import load

verify = load("verify_docs")


@pytest.fixture()
def docs_copy(tmp_path: Path) -> Path:
    """Copia del repositorio sin entornos ni datos, para estropear documentos sin tocar los reales."""
    shutil.copytree(
        ROOT, tmp_path / "repo", ignore=shutil.ignore_patterns(".git", ".venv", ".vector*", "datasets", "*cache*")
    )
    return tmp_path / "repo"


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def test_repository_lines_are_documented():
    assert verify.main() == 0


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("## Métricas", "## Otra cosa", "Métricas"),
        ("`PLANIFICADO`", "`OPERATIVO`", "estado"),
        ("## Límites", "<!-- completar -->\n\n## Límites", "completar"),
        ("(../PLAN_1_BASICO.md)", "(../NO_EXISTE.md)", "enlace local roto"),
    ],
)
def test_defects_are_detected(docs_copy: Path, old: str, new: str, message: str):
    edit(docs_copy / "docs" / "lineas" / "L03-vacios-creacion.md", old, new)
    assert any(message in p for p in verify.check(docs_copy))


def test_missing_and_unregistered_documents_are_detected(docs_copy: Path):
    folder = docs_copy / "docs" / "lineas"
    (folder / "L05-rag.md").rename(folder / "L11-otra.md")
    problems = verify.check(docs_copy)
    assert any("falta el documento L05-rag.md" in p for p in problems)
    assert any("L11-otra.md: documento sin registrar" in p for p in problems)


def test_modality_pointing_to_unknown_line_is_detected():
    assert any("L99" in p for p in verify.check(modality_lines={"x": "L99"}))
