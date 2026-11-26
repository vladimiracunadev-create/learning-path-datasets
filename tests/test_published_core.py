"""Comprueba el núcleo publicado en el repositorio, tal como está, no una copia generada al vuelo."""

from __future__ import annotations

import json

import pytest

from lpdatasets.build import read_jsonl
from lpdatasets.cleaning import HIDDEN_TYPES, report
from lpdatasets.core import load_marcos, select
from lpdatasets.core_build import read_core, validate_core
from lpdatasets.proposals import proposals_report
from tests.conftest import ROOT

NUCLEO = ROOT / "nucleo"
FOLDER = NUCLEO / "escolar-chile" / "1-basico"
MARCOS = set(load_marcos())


@pytest.fixture(scope="module")
def entities():
    return read_core(FOLDER)


def test_published_core_is_valid():
    assert validate_core(NUCLEO) == []


def test_coverage_reconciles_with_the_source_catalog(entities):
    coverage = json.loads((FOLDER / "manifest.json").read_text(encoding="utf-8"))["cobertura"]
    assert coverage["catalogo"] == 1034
    assert coverage["representadas"] == 887
    assert coverage["por_estado_editorial"] == {"desarrollada": 562, "integrada": 325}
    assert sum(x["clases"] for x in coverage["excluidas"]) == 147
    assert sum(e["entidad"] == "clase" for e in entities) == 887


def test_items_match_the_published_dataset_one_to_one(entities):
    folder = ROOT / "datasets" / "escolar-chile" / "1-basico"
    records = {r["id"] for name in ("train", "eval") for r in read_jsonl(folder / f"{name}.jsonl")}
    assert {e["id"] for e in entities if e["entidad"] == "item"} == records


def test_student_view_has_no_teacher_material_or_hidden_answers(entities):
    seen = list(select(entities, uso="educativo", publico="estudiante", marcos=MARCOS))
    roles = {e["extra"]["rol"] for e in seen if e["entidad"] == "recurso"}
    assert roles == {"cuaderno_estudiante"}
    assert not any("**Solucionario razonado**" in e.get("texto", "") for e in seen)
    hidden = [e for e in seen if e["entidad"] == "item" and e["tipo"] in HIDDEN_TYPES]
    assert hidden
    assert all(set(e["contenido"]) == {"enunciado"} and "extra" not in e for e in hidden)


def test_commercial_use_is_not_allowed_without_authorization(entities):
    assert list(select(entities, uso="comercial", publico="docente", marcos=MARCOS)) == []


def test_cleaning_report_is_up_to_date():
    doc = ROOT / "docs" / "informes" / "limpieza-1-basico.md"
    assert report(NUCLEO, ROOT / "datasets", doc, check=True) == []


def test_cleaning_proposals_cover_every_finding_and_are_up_to_date():
    folder = FOLDER / "limpieza"
    findings = [f["id"] for f in read_jsonl(folder / "hallazgos.jsonl")]
    proposals = read_jsonl(folder / "propuestas.jsonl")
    assert [p["id"] for p in proposals] == findings
    assert not [p for p in proposals if p["lote"] == "sin-revisar"]
    doc = ROOT / "docs" / "informes" / "propuestas-limpieza-1-basico.md"
    assert proposals_report(NUCLEO, doc, check=True) == []
