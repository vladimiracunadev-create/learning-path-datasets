from __future__ import annotations

import copy

import pytest

from lpdatasets.corrections import check_corrections, render, simulate
from tests.test_cleaning import item
from tests.test_core import CLASS
from tests.test_proposals import text_resource

OLD = "¿De qué material es un vaso de vidrio?"
GLASS = item("a", OLD, "Vidrio", clase_id=CLASS["id"])
NOTEBOOK = text_resource("cuaderno_estudiante") | {
    "texto": f"**Ejemplos resueltos** Respuesta: la madera de los árboles. **Ejercicios** - {OLD}"
}
OTHER = item("b", "¿Qué es un objeto?", "Una cosa que se puede tocar", clase_id=CLASS["id"])
ENTITIES = [CLASS, NOTEBOOK, GLASS, OTHER]
PROPOSALS = [{"id": "h1", "veredicto": "corregir", "items_a_cambiar": ["a"]}]


def correction(question: str = "Una llave, ¿es de metal o de tela?", answer: str = "De metal", **values) -> dict:
    return {
        "item": "a",
        "hallazgo": "h1",
        "antes": copy.deepcopy(GLASS["contenido"]),
        "despues": {"enunciado": question, "respuesta": answer, "razon": "Es dura y fría."},
        "cambio": "ya no nombra el material",
    } | values


def problems(*rows: dict) -> list[str]:
    return check_corrections(ENTITIES, PROPOSALS, list(rows))


def test_valid_correction_passes_and_leaves_the_core_untouched():
    original = copy.deepcopy(ENTITIES)
    assert problems(correction()) == []
    changed = simulate(ENTITIES, [correction()])
    assert "Una llave" in changed[1]["texto"] and OLD not in changed[1]["texto"]
    assert ENTITIES == original


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (correction(item="x"), "no existe"),
        (correction(antes={"enunciado": "otra", "respuesta": "x"}), "ya no coincide"),
        (correction(question=OLD), "no cambia"),
        (correction(hallazgo="h2"), "no corresponde"),
        (correction(cambio=" "), "qué cambia"),
        (correction(despues={"enunciado": "Nueva"}), "necesita"),
        (correction(question="¿Qué es un objeto?"), "respuestas_en_conflicto"),
        (correction(answer="La madera de los árboles"), "ejemplo del cuaderno"),
    ],
)
def test_defective_corrections_are_rejected(row: dict, message: str):
    assert any(message in p for p in problems(row))


def test_every_item_to_fix_needs_a_text():
    assert any("no tiene redacción" in p for p in problems())


def test_report_states_that_nothing_is_approved_or_applied():
    document = {"redactor": "prueba", "fecha": "2026-01-01", "aprobado_por": None, "correcciones": [correction()]}
    text = render(document)
    assert "sin aprobar" in text and "No están aplicadas" in text and OLD in text
    assert "Para tu criterio" not in text
    document["correcciones"] = [correction(duda="puede ser fácil")]
    assert "**Para tu criterio:** puede ser fácil." in render(document)
