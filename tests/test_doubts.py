from __future__ import annotations

import pytest

from lpdatasets.doubts import check_doubts, render

PROPOSALS = [
    {"id": "h1", "estado": "pendiente", "veredicto": "decidir", "lote": "enunciado-decidir"},
    {"id": "h2", "estado": "pendiente", "veredicto": "corregir", "lote": "etiquetas"},
    {"id": "h3", "estado": "aceptado", "veredicto": "decidir", "lote": "enunciado-decidir"},
]
KEEP = {"hallazgo": "h1", "recomendacion": "mantener", "motivo": "es un apoyo", "items": []}


def test_every_open_doubt_has_one_recommendation():
    assert check_doubts(PROPOSALS, [KEEP], []) == []


@pytest.mark.parametrize(
    ("doubts", "message"),
    [
        ([], "sin recomendación"),
        ([KEEP, KEEP], "dos veces"),
        ([KEEP, KEEP | {"hallazgo": "h3"}], "ya no está abierto"),
        ([KEEP | {"motivo": " "}], "motivo"),
        ([KEEP | {"recomendacion": "quizás"}], "motivo"),
        ([KEEP | {"recomendacion": "reescribir", "items": ["a"]}], "falta el texto"),
    ],
)
def test_incomplete_advice_is_rejected(doubts: list[dict], message: str):
    assert any(message in p for p in check_doubts(PROPOSALS, doubts, []))


def test_sheet_says_nothing_is_decided():
    document = {"redactor": "prueba", "fecha": "2026-01-01", "dudas": [KEEP]}
    text = render(document, {"a": {"enunciado": "¿Qué?", "respuesta": "Eso"}}, {"h1": ["a"]}, [])
    assert "nada está decidido" in text and "¿Qué?" in text
