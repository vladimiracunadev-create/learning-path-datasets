from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lpdatasets.build import read_jsonl
from lpdatasets.cleaning import report
from lpdatasets.core_build import write_core
from lpdatasets.corrections import (
    approve_corrections,
    check_corrections,
    corrections_report,
    mark_applied,
    render,
    simulate,
)
from tests.test_cleaning import item
from tests.test_core import CLASS
from tests.test_proposals import text_resource

OLD = "¿De qué material es un vaso de vidrio?"
GLASS = item("a", OLD, "Vidrio", clase_id=CLASS["id"])
GLASS["contenido"]["razon"] = "Es lo que lo forma."
NOTEBOOK = text_resource("cuaderno_estudiante") | {
    "texto": f"**Ejemplos resueltos** Respuesta: la madera de los árboles. **Ejercicios** - {OLD}"
}
OTHER = item("b", "¿Qué es un objeto?", "Una cosa que se puede tocar", clase_id=CLASS["id"])
ENTITIES = [CLASS, NOTEBOOK, GLASS, OTHER]
PROPOSALS = [{"id": "h1", "veredicto": "corregir", "items_a_cambiar": ["a"]}]
FINDINGS = [{"id": "h1", "regla": "solucion_en_enunciado", "total": 1, "entidades": ["a"]}]


def correction(question: str = "Una llave, ¿es de metal o de tela?", answer: str = "De metal", **values) -> dict:
    return {
        "item": "a",
        "hallazgo": "h1",
        "antes": copy.deepcopy(GLASS["contenido"]),
        "despues": {"enunciado": question, "respuesta": answer, "razon": "Es dura y fría."},
        "cambio": "ya no nombra el material",
    } | values


def problems(*rows: dict) -> list[str]:
    return check_corrections(ENTITIES, PROPOSALS, list(rows), FINDINGS)


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
    assert "sin aprobar" in text and "ninguna aplicada" in text and OLD in text
    assert "Para tu criterio" not in text
    document["correcciones"] = [correction(duda="puede ser fácil")]
    assert "**Para tu criterio:** puede ser fácil." in render(document)


def publish(tmp_path: Path, rows: list[dict]) -> tuple[Path, Path, Path]:
    nucleo = tmp_path / "nucleo"
    folder = nucleo / "demo" / "1-basico"
    coverage = {"catalogo": 1, "representadas": 1, "excluidas": []}
    info = {"pack": "demo", "nivel": "1-basico", "commit_fuente": "viejo", "cobertura": coverage}
    write_core(folder, ENTITIES, info)
    (folder / "limpieza").mkdir()
    (folder / "limpieza" / "propuestas.jsonl").write_text(json.dumps(PROPOSALS[0]), encoding="utf-8")
    review = {"items": {"r": {"a": {"veredicto": "corregir"}}}, "hallazgos": {}}
    (folder / "limpieza" / "revision.json").write_text(json.dumps(review), encoding="utf-8")
    (folder / "limpieza" / "hallazgos.jsonl").write_text(json.dumps(FINDINGS[0]), encoding="utf-8")
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


SOLVED = "Una llave que abre una puerta, ¿de qué material es?"


def apply_in_source(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Publica el núcleo, aprueba la corrección y vuelve a «exportar» con el texto nuevo."""
    row = correction(question=SOLVED)
    nucleo, doc, path = publish(tmp_path, [row])
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    assert approve_corrections(nucleo, doc, "revisora") == 1
    report(nucleo, datasets, tmp_path / "limpieza.md")  # los hallazgos anteriores al cambio
    coverage = {"catalogo": 1, "representadas": 1, "excluidas": []}
    info = {"pack": "demo", "nivel": "1-basico", "commit_fuente": "nuevo", "cobertura": coverage}
    write_core(nucleo / "demo" / "1-basico", simulate(ENTITIES, [row]), info)
    return nucleo, datasets, path


def test_applied_corrections_archive_the_findings_they_solve(tmp_path: Path):
    nucleo, datasets, path = apply_in_source(tmp_path)
    folder = path.parent
    before = {f["id"] for f in read_jsonl(folder / "hallazgos.jsonl") if "a" in f["entidades"]}
    applied, resolved = mark_applied(nucleo, datasets)
    assert applied == 1 and resolved >= 1
    assert saved(path)["aplicada"] == "nuevo"
    assert {f["id"] for f in read_jsonl(folder / "resueltos.jsonl")} <= before
    assert "a" not in json.loads((folder / "revision.json").read_text(encoding="utf-8"))["items"]["r"]
    report(nucleo, datasets, tmp_path / "limpieza.md")
    assert "## Resueltos" in (tmp_path / "limpieza.md").read_text(encoding="utf-8")
    assert corrections_report(nucleo, tmp_path / "correcciones.md") == []
    with pytest.raises(SystemExit, match="ninguna"):
        mark_applied(nucleo, datasets)


def test_unexpected_text_stops_the_registration(tmp_path: Path):
    nucleo, datasets, path = apply_in_source(tmp_path)
    other = correction(question="Texto que nadie aprobó, ¿sí o no?")
    coverage = {"catalogo": 1, "representadas": 1, "excluidas": []}
    info = {"pack": "demo", "nivel": "1-basico", "commit_fuente": "otro", "cobertura": coverage}
    write_core(nucleo / "demo" / "1-basico", simulate(ENTITIES, [other]), info)
    with pytest.raises(SystemExit, match="ni el texto anterior"):
        mark_applied(nucleo, datasets)
    assert "aplicada" not in saved(path)


def test_a_glossary_definition_can_change_without_changing_the_word():
    word = item("v", "madera", "palo", tipo="vocabulario", publico_solucion=["estudiante", "docente"])
    word["contenido"] = {"enunciado": "madera", "respuesta": "palo"}
    word["clase_id"] = CLASS["id"]
    notebook = NOTEBOOK | {"texto": "| madera | palo |"}
    row = {
        "item": "v",
        "hallazgo": "h9",
        "antes": dict(word["contenido"]),
        "despues": {"enunciado": "madera", "respuesta": "material que viene de los árboles"},
        "cambio": "definición más precisa",
    }
    proposals = [{"id": "h9", "veredicto": "decidir", "items_a_cambiar": []}]
    findings = [{"id": "h9", "entidades": ["v"]}]
    entities = [CLASS, notebook, word]
    assert check_corrections(entities, proposals, [row], findings) == []
    assert "| madera | material que viene de los árboles |" in simulate(entities, [row])[1]["texto"]
    assert "Razón" not in render({"redactor": "p", "fecha": "f", "correcciones": [row]})
