from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from lpdatasets.schema import TIPOS, validate_record
from tests.conftest import ROOT
from tests.test_schema import VALID


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skills_and_agents_are_valid():
    assert load("verify_assets").main() == 0


def test_expected_skills_and_agents_exist():
    skills = {p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    agents = {p.stem for p in (ROOT / ".claude" / "agents").glob("*.md")}
    assert skills == {
        "dataset-conocimiento-extraer",
        "dataset-verificar",
        "dataset-construir-publicar",
        "dataset-pack-nuevo",
    }
    assert agents == {
        "extractor-conocimiento",
        "verificador-independiente",
        "curador-datasets",
        "auditor-derechos-datos",
        "limpiador-datos",
    }


@pytest.mark.parametrize("tipo", ["hecho", "definicion", "relacion", "procedimiento", "concepcion_erronea"])
def test_knowledge_types_are_valid_records(tipo):
    assert tipo in TIPOS
    rec = {**VALID, "tipo": tipo, "extra": {"sujeto": "x", "confianza": "alta"}}
    assert validate_record(rec) == []


def test_installer_copies_without_overwriting_different_files(tmp_path: Path):
    installer = load("install_claude_assets")
    assert installer.main(["--dest", str(tmp_path)]) == 0
    assert (tmp_path / "skills" / "dataset-verificar" / "SKILL.md").exists()
    assert (tmp_path / "agents" / "curador-datasets.md").exists()
    target = tmp_path / "agents" / "curador-datasets.md"
    target.write_text("otra cosa", encoding="utf-8")
    assert installer.main(["--dest", str(tmp_path)]) == 1
    assert target.read_text(encoding="utf-8") == "otra cosa"
    assert installer.main(["--dest", str(tmp_path), "--force"]) == 0
    assert target.with_name(target.name + ".bak").read_text(encoding="utf-8") == "otra cosa"
