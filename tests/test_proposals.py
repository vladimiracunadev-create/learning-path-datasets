from __future__ import annotations

import json
from pathlib import Path

import pytest

from lpdatasets.cleaning import core_findings, report
from lpdatasets.core_build import write_core
from lpdatasets.proposals import LOTS, approve, proposals_report, propose, statement_kind
from tests.test_cleaning import item
from tests.test_core import CLASS, RESOURCE


@pytest.mark.parametrize(
    ("question", "answer", "kind"),
    [
        ("¿Es rojo o azul?", "rojo", "eleccion"),
        ("¿Miras al público o al piso?", "Al público", "eleccion"),
        ("A) un perro B) un gato. ¿Cuál maúlla?", "un gato", "alternativas"),
        ("Lee: «La luna sale de noche». ¿Cuándo sale?", "De noche", "texto_citado"),
        ("De esta lista: familia, curso, nube. ¿Cuál no es un grupo?", "nube", "lista"),
        ("¿De qué material es un vaso de vidrio?", "Vidrio", "otro"),
        ("El vaso es transparente. ¿Es transparente u opaco?", "Transparente", "otro"),
    ],
)
def test_statement_kinds(question: str, answer: str, kind: str):
    assert statement_kind(item("a", question, answer)) == kind


def review(items: dict | None = None, findings: dict | None = None) -> dict:
    tables = {"solucion_en_enunciado": items or {}}
    return {"revisor": "prueba", "fecha": "2026-01-01", "items": tables, "hallazgos": findings or {}}


GLASS = item("a", "¿De qué material es un vaso de vidrio?", "Vidrio")


def only(entities, rule="solucion_en_enunciado", data=None):
    findings = [f for f in core_findings(entities) if f["regla"] == rule]
    return propose(findings, entities, data or review())[0]


def test_what_needs_reading_is_never_accepted_without_it():
    proposal = only([GLASS])
    assert (proposal["lote"], proposal["veredicto"]) == ("sin-revisar", "decidir")


@pytest.mark.parametrize(
    ("verdict", "lot"),
    [("ok", "enunciado-comprension"), ("corregir", "enunciado-corregir"), ("decidir", "enunciado-decidir")],
)
def test_individual_judgement_sets_the_lot(verdict: str, lot: str):
    proposal = only([GLASS], data=review({"a": {"veredicto": verdict, "motivo": "porque sí"}}))
    assert proposal["lote"] == lot and proposal["lectura"] == "individual"


def test_rule_based_lot_says_so():
    proposal = only([item("a", "¿Es rojo o azul?", "rojo")])
    assert (proposal["lote"], proposal["lectura"]) == ("enunciado-opciones", "regla")


def test_stale_review_is_rejected():
    with pytest.raises(SystemExit, match="ya no existen"):
        propose([], [GLASS], review(findings={"duplicado_exacto:000000000000": {"lote": "duplicado-repaso"}}))


def text_resource(role: str) -> dict:
    entity = {k: v for k, v in RESOURCE.items() if k not in ("uri", "sha256", "descripcion")}
    entity.update(id=f"r:{role}", medio="text/markdown", clase_id=CLASS["id"], texto=role, extra={"rol": role})
    return entity


@pytest.mark.parametrize(
    ("notebook", "lot"),
    [
        ("Recuerda: tocar cada ficha una vez y sin saltar.", "cuaderno-ensenanza"),
        ("**Ejemplos resueltos** Respuesta: tocar cada ficha una vez y sin saltar.", "sin-revisar"),
    ],
)
def test_worked_example_with_the_answer_needs_reading(notebook: str, lot: str):
    resource = text_resource("cuaderno_estudiante") | {"texto": notebook}
    task = item("a", "¿Cómo se cuenta?", "tocar cada ficha una vez y sin saltar", clase_id=CLASS["id"])
    assert only([resource, task], rule="solucion_en_cuaderno")["lote"] == lot


def publish(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Núcleo mínimo publicado, con un duplicado aceptable y un enunciado que habría que corregir."""
    nucleo = tmp_path / "nucleo"
    folder = nucleo / "demo" / "1-basico"
    entities = [
        CLASS,
        text_resource("guia_docente"),
        text_resource("cuaderno_estudiante"),
        item("a", "Cuenta", "tres", tipo="vocabulario"),
        item("b", "cuenta", "Tres", tipo="vocabulario"),
        GLASS | {"id": "g"},
    ]
    coverage = {"catalogo": 1, "representadas": 1, "excluidas": []}
    info = {"pack": "demo", "nivel": "1-basico", "commit_fuente": "abc", "cobertura": coverage}
    write_core(folder, entities, info)
    (folder / "limpieza").mkdir()
    data = review({"g": {"veredicto": "corregir", "motivo": "se responde sola"}})
    (folder / "limpieza" / "revision.json").write_text(json.dumps(data), encoding="utf-8")
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    report(nucleo, datasets, tmp_path / "limpieza.md")
    proposals_report(nucleo, tmp_path / "propuestas.md")
    return nucleo, datasets, folder


def test_approval_records_only_accepting_lots(tmp_path: Path):
    nucleo, datasets, folder = publish(tmp_path)
    docs = (tmp_path / "limpieza.md", tmp_path / "propuestas.md")
    assert approve(nucleo, datasets, ["duplicado-glosario"], "revisora", *docs) == 1
    decisions = json.loads((folder / "limpieza" / "decisiones.json").read_text(encoding="utf-8"))["decisiones"]
    assert [d["aprobado_por"] for d in decisions] == ["revisora"]
    assert proposals_report(nucleo, docs[1], check=True) == []
    assert report(nucleo, datasets, docs[0], check=True) == []
    assert approve(nucleo, datasets, ["duplicado-glosario"], "otra", *docs) == 0


@pytest.mark.parametrize(
    ("lots", "approver"),
    [(["enunciado-corregir"], "r"), (["inventado"], "r"), ([], "r"), (["duplicado-glosario"], "  ")],
)
def test_approval_is_refused(tmp_path: Path, lots: list[str], approver: str):
    nucleo, datasets, folder = publish(tmp_path)
    with pytest.raises(SystemExit):
        approve(nucleo, datasets, lots, approver, tmp_path / "limpieza.md", tmp_path / "propuestas.md")
    assert not (folder / "limpieza" / "decisiones.json").exists()


def test_report_lists_what_must_change(tmp_path: Path):
    publish(tmp_path)
    text = (tmp_path / "propuestas.md").read_text(encoding="utf-8")
    assert "¿De qué material es un vaso de vidrio?" in text and "se responde sola" in text
    assert all(lot in LOTS for lot in ("duplicado-glosario", "enunciado-corregir"))
