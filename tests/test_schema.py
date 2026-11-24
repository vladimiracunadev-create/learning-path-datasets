from __future__ import annotations

import copy
import json

import pytest

from lpdatasets.schema import SCHEMA_VERSION, partition_for, text_for_embedding, validate_record
from tests.conftest import ROOT

VALID = {
    "schema": SCHEMA_VERSION,
    "id": "demo:1",
    "pack": "demo",
    "dominio": "demo",
    "nivel": "1-basico",
    "asignatura": "matematica",
    "unidad": "MA01 OA 01",
    "clase": 1,
    "tipo": "ejercicio_cerrado",
    "dificultad": 2,
    "entrada": "¿Cuánto es 1 + 1?",
    "salida": "2",
    "razon": "Uno más uno es dos.",
    "idioma": "es",
    "habilidades": [],
    "verificable": True,
    "fuente": {"repo": "demo/repo", "commit": "abc123", "ruta": "a/b.md"},
    "licencia": "CC-BY-NC-SA-4.0",
    "revision": "ia_asistida_sin_revision_humana",
    "particion": "train",
}


def test_valid_record_passes():
    assert validate_record(VALID) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tipo", "inventado"),
        ("particion", "test"),
        ("revision", "aprobado"),
        ("dificultad", 9),
        ("clase", 0),
        ("verificable", "si"),
        ("entrada", "  "),
        ("fuente", {"repo": "x"}),
        ("razon", ""),
    ],
)
def test_invalid_values_are_rejected(field, value):
    rec = copy.deepcopy(VALID)
    rec[field] = value
    assert validate_record(rec)


def test_missing_fields_are_reported():
    rec = copy.deepcopy(VALID)
    del rec["licencia"]
    assert any("licencia" in p for p in validate_record(rec))


def test_partition_is_deterministic_and_roughly_ten_percent():
    assert partition_for("p", "k") == partition_for("p", "k")
    share = sum(partition_for("p", f"clase-{i}") == "eval" for i in range(2000)) / 2000
    assert 0.06 < share < 0.14


def test_embedding_text_includes_reason_when_present():
    assert "uno más uno" in text_for_embedding(VALID).lower()


def test_json_schema_file_agrees_with_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schema" / "record.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(VALID, schema)
    bad = copy.deepcopy(VALID)
    bad["tipo"] = "inventado"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
