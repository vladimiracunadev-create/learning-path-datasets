from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lpdatasets.cleaning import RULES, apply_decisions, core_findings, dataset_findings
from tests.test_core import CLASS, ITEM


def item(ident: str, question: str, answer: str, **values) -> dict:
    entity = copy.deepcopy(ITEM)
    entity.update(id=ident, habilidades=["contar"], dificultad=1, extra={})
    entity["contenido"] = {"enunciado": question, "respuesta": answer}
    entity.update(values)
    return entity


def resource(role: str, text: str) -> dict:
    return {"entidad": "recurso", "id": f"r:{role}", "clase_id": CLASS["id"], "texto": text, "extra": {"rol": role}}


LONG = "Contar tocando cada ficha una sola vez"
COMPLETE = [
    copy.deepcopy(CLASS),
    resource("guia_docente", "guía"),
    resource("cuaderno_estudiante", "preguntas"),
    item("ok", "¿Cuánto es dos más dos?", "cuatro"),
]
CASES = {
    "clase_incompleta": [copy.deepcopy(CLASS)],
    "duplicado_exacto": [item("a", "Cuenta", "tres"), item("b", "cuenta ", "Tres")],
    "respuestas_en_conflicto": [item("a", "Cuenta", "tres"), item("b", "Cuenta", "cinco")],
    "recurso_ausente": [item("a", "Observa la imagen y di cuántos hay.", "tres")],
    "solucion_en_enunciado": [item("a", "¿Es rojo o azul?", "rojo")],
    "solucion_en_cuaderno": [
        resource("cuaderno_estudiante", f"Recuerda: {LONG}."),
        item("a", "¿Cómo se cuenta?", LONG),
    ],
    "texto_oficial": [item("a", "Pregunta", "Respuesta", extra={"coincide_texto_oficial": "MA01 OA 01"})],
    "sin_habilidades": [item("a", "Pregunta", "Respuesta", habilidades=[])],
    "sin_dificultad": [item("a", "Pregunta", "Respuesta", dificultad=None)],
}


def test_complete_class_has_no_findings():
    assert core_findings(COMPLETE) == []


@pytest.mark.parametrize("rule", sorted(CASES))
def test_each_core_rule_is_detected_without_touching_the_data(rule: str):
    entities = CASES[rule]
    original = copy.deepcopy(entities)
    found = [f for f in core_findings(entities) if f["regla"] == rule]
    assert found, rule
    assert found[0]["estado"] == "pendiente" and found[0]["aprobado_por"] is None
    assert entities == original


def test_dataset_crossings_are_detected_and_every_rule_has_a_case():
    row = {"asignatura": "matematica", "entrada": "Cuenta", "salida": "3"}
    records = [
        {**row, "id": "t", "particion": "train"},
        {**row, "id": "e1", "particion": "eval"},
        {**row, "id": "e2", "salida": "4", "particion": "eval"},
    ]
    found = {f["regla"]: f for f in dataset_findings(records)}
    assert found["cruce_identico"]["entidades"] == ["e1"]
    assert found["cruce_por_entrada"]["entidades"] == ["e1", "e2"]
    assert set(CASES) | set(found) == set(RULES)


def test_findings_are_deterministic_regardless_of_order():
    entities = CASES["respuestas_en_conflicto"]
    ids = lambda rows: sorted(f["id"] for f in core_findings(rows))  # noqa: E731
    assert ids(entities) == ids(list(reversed(entities)))


def decisions(path: Path, *rows: dict) -> Path:
    path.write_text(json.dumps({"decisiones": list(rows)}), encoding="utf-8")
    return path


def test_complete_decision_is_recorded(tmp_path: Path):
    findings = core_findings(CASES["duplicado_exacto"])
    decision = {"id": findings[0]["id"], "estado": "aceptado", "motivo": "repaso", "aprobado_por": "revisor"}
    result = apply_decisions(findings, decisions(tmp_path / "d.json", decision))
    assert (result[0]["estado"], result[0]["aprobado_por"]) == ("aceptado", "revisor")


@pytest.mark.parametrize(
    "change", [{"id": "duplicado_exacto:000000000000"}, {"motivo": ""}, {"aprobado_por": ""}, {"estado": "ok"}]
)
def test_stale_or_incomplete_decisions_are_rejected(tmp_path: Path, change: dict):
    findings = core_findings(CASES["duplicado_exacto"])
    decision = {"id": findings[0]["id"], "estado": "aceptado", "motivo": "m", "aprobado_por": "r", **change}
    with pytest.raises(SystemExit):
        apply_decisions(findings, decisions(tmp_path / "d.json", decision))
