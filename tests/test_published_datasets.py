"""Comprueba los datasets publicados en `datasets/` tal como están en el repositorio."""

from __future__ import annotations

import json

import pytest

from lpdatasets.build import manifests, read_jsonl, validate_datasets
from tests.conftest import ROOT

DATASETS = ROOT / "datasets"


def test_published_datasets_are_valid():
    assert validate_datasets(DATASETS) == []


def test_every_dataset_declares_license_provenance_and_review_status():
    for mpath in manifests(DATASETS):
        m = json.loads(mpath.read_text(encoding="utf-8"))
        assert m["licencia"] and m["commit_fuente"] != "desconocido" and m["revision"]
        assert m["clases_eval"] > 0, "debe existir un conjunto de evaluación"


def test_evaluation_split_is_about_ten_percent_of_classes():
    for mpath in manifests(DATASETS):
        m = json.loads(mpath.read_text(encoding="utf-8"))
        share = m["clases_eval"] / (m["clases_eval"] + m["clases_train"])
        assert 0.05 < share < 0.2


def test_records_do_not_embed_official_oa_text_and_keep_no_empty_answers():
    for mpath in manifests(DATASETS):
        for name in json.loads(mpath.read_text(encoding="utf-8"))["archivos"]:
            for rec in read_jsonl(mpath.parent / name):
                assert rec["salida"].strip() and rec["entrada"].strip()
                assert "Objetivo de Aprendizaje oficial" not in rec["entrada"]


def test_json_schema_accepts_every_published_record():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schema" / "record.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for mpath in manifests(DATASETS):
        for name in json.loads(mpath.read_text(encoding="utf-8"))["archivos"]:
            for i, rec in enumerate(read_jsonl(mpath.parent / name)):
                if i % 25 == 0:  # muestra: la validación completa la hace validate_datasets
                    validator.validate(rec)
