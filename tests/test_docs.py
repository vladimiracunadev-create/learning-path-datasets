from __future__ import annotations

import json
import shutil
from pathlib import Path
from xml.etree import ElementTree

import pytest

from tests.conftest import ROOT
from tests.test_assets import load

verify = load("verify_docs")
diagram = load("docs_diagram")


@pytest.fixture()
def docs_copy(tmp_path: Path) -> Path:
    """Copia del repositorio sin entornos ni datos, para estropear documentos sin tocar los reales."""
    shutil.copytree(
        ROOT,
        tmp_path / "repo",
        ignore=shutil.ignore_patterns(".git", ".venv", ".vector*", "datasets", "nucleo", "*cache*"),
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


def test_diagram_is_up_to_date_and_well_formed():
    assert diagram.main(["--check"]) == 0
    root = ElementTree.fromstring(diagram.render())
    words = " ".join(root.itertext())
    registry = json.loads((ROOT / "docs" / "lineas" / "lineas.json").read_text(encoding="utf-8"))
    for line in registry["lineas"]:
        assert f"{line['id']} · " in words


def test_diagram_follows_progress_and_accepts_new_lines(docs_copy: Path):
    path = docs_copy / "docs" / "lineas" / "lineas.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["lineas"].append({"id": "L11", "titulo": "Fichas <A4>", "estado": "PLANIFICADO", "fase": 4})
    path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    assert diagram.main(["--check"], docs_copy) == 1
    assert diagram.main(["--write"], docs_copy) == 0
    assert diagram.main(["--check"], docs_copy) == 0
    drawing = (docs_copy / diagram.OUTPUT).read_text(encoding="utf-8")
    assert "L11 · Fichas &lt;A4&gt;" in drawing
    ElementTree.fromstring(drawing)
