from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lpdatasets.core_build import write_core
from lpdatasets.corrections import (
    approve_corrections,
    check_corrections,
    corrections_report,
    render,
    simulate,
)
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
    document = {"redactor": "prueba", "fecha": "2026-01-01", "correcciones": [correction()]}
    text = render(document)
    assert "sin aprobar" in text and "No están aplicadas" in text and OLD in text
    assert "Para tu criterio" not in text
    document["correcciones"] = [correction(duda="puede ser fácil")]
    assert "**Para tu criterio:** puede ser fácil." in render(document)


def publish(tmp_path: Path, rows: list[dict]) -> tuple[Path, Path, Path]:
    nucleo = tmp_path / "nucleo"
    folder = nucleo / "demo" / "1-basico"
    coverage = {"catalogo": 1, "representadas": 1, "excluidas": []}
    write_core(folder, ENTITIES, {"cobertura": coverage})
    (folder / "limpieza").mkdir()
    (folder / "limpieza" / "propuestas.jsonl").write_text(json.dumps(PROPOSALS[0]), encoding="utf-8")
    path = folder / "limpieza" / "correcciones.json"
    document = {"redactor": "prueba", "fecha": "2026-01-01", "correcciones": rows}
    path.write_text(json.dumps(document), encoding="utf-8")
    doc = tmp_path / "correcciones.md"
    assert corrections_report(nucleo, doc) == []
    return nucleo, doc, path


def saved(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))["correcciones"][0]


def test_approval_skips_open_doubts_unless_named(tmp_path: Path):
    nucleo, doc, path = publish(tmp_path, [correction(duda="puede ser fácil")])
    assert approve_corrections(nucleo, doc, "revisora") == 0
    assert "aprobacion" not in saved(path)
    assert approve_corrections(nucleo, doc, "revisora", ["a"]) == 1
    assert saved(path)["aprobacion"]["por"] == "revisora"
    assert "1 de 1 aprobadas por revisora" in doc.read_text(encoding="utf-8")


def test_changed_text_loses_its_approval(tmp_path: Path):
    nucleo, doc, path = publish(tmp_path, [correction()])
    assert approve_corrections(nucleo, doc, "revisora") == 1
    row = saved(path)
    row["despues"]["enunciado"] = "Otra pregunta distinta, ¿metal o tela?"
    assert any("después de aprobarse" in p for p in problems(row))


@pytest.mark.parametrize(("approver", "include"), [(" ", []), ("r", ["zzz"])])
def test_corrections_approval_is_refused(tmp_path: Path, approver: str, include: list[str]):
    nucleo, doc, path = publish(tmp_path, [correction()])
    with pytest.raises(SystemExit):
        approve_corrections(nucleo, doc, approver, include)
    assert "aprobacion" not in saved(path)
