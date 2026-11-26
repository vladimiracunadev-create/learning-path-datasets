from __future__ import annotations

import json
from pathlib import Path

import pytest

from lpdatasets.build import read_jsonl
from lpdatasets.cleaning import report
from lpdatasets.core_build import write_core
from lpdatasets.corrections import corrections_report
from lpdatasets.doubts import Docs, check_doubts, doubts_report, render, resolve_doubts
from lpdatasets.proposals import proposals_report
from tests.test_cleaning import item
from tests.test_core import CLASS
from tests.test_proposals import text_resource

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
        ([KEEP, KEEP | {"hallazgo": "h9"}], "ya no está abierto"),
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
    assert "nada está decidido" in text.lower() and "¿Qué?" in text


def test_decided_and_resolved_doubts_stay_as_history():
    assert check_doubts(PROPOSALS, [KEEP, KEEP | {"hallazgo": "h3"}], []) == []
    assert check_doubts(PROPOSALS, [KEEP, KEEP | {"hallazgo": "h7"}], [], resolved={"h7"}) == []


def publish(tmp_path: Path) -> tuple[Path, Path, Path, Docs, list[str]]:
    """Dos dudas reales: un enunciado que se mantiene y otro que se reescribe."""
    nucleo = tmp_path / "nucleo"
    folder = nucleo / "demo" / "1-basico"
    other = CLASS | {"id": "demo:clase:2", "numero": 2}
    questions = {"keep": "¿De qué material es un vaso de vidrio?", "fix": "¿De qué material es una mesa de madera?"}
    entities = [CLASS, other]
    for n, (ident, question) in enumerate(questions.items()):
        clase = (CLASS, other)[n]
        guide = text_resource("guia_docente") | {"id": f"g:{ident}", "clase_id": clase["id"]}
        notebook = text_resource("cuaderno_estudiante") | {"id": f"c:{ident}", "clase_id": clase["id"]}
        answer = "Vidrio" if ident == "keep" else "Madera"
        task = item(ident, question, answer, clase_id=clase["id"])
        task["contenido"]["razon"] = "Es lo que lo forma."
        entities += [guide, notebook, task]
    coverage = {"catalogo": 2, "representadas": 2, "excluidas": []}
    write_core(folder, entities, {"pack": "demo", "nivel": "1-basico", "commit_fuente": "a", "cobertura": coverage})
    cleaning = folder / "limpieza"
    cleaning.mkdir()
    judged = {i: {"veredicto": "decidir", "motivo": "dudoso"} for i in questions}
    review = {"revisor": "p", "fecha": "f", "items": {"solucion_en_enunciado": judged}, "hallazgos": {}}
    (cleaning / "revision.json").write_text(json.dumps(review), encoding="utf-8")
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    docs = Docs(*(tmp_path / f"{name}.md" for name in Docs._fields))
    report(nucleo, datasets, docs.clean)
    proposals_report(nucleo, docs.proposals)
    findings = {f["entidades"][0]: f["id"] for f in read_jsonl(cleaning / "hallazgos.jsonl") if f["regla"] == RULE}
    row = {
        "item": "fix",
        "hallazgo": findings["fix"],
        "antes": next(e["contenido"] for e in entities if e["id"] == "fix"),
        "despues": {"enunciado": "Es dura y viene de los árboles. ¿Qué es?", "respuesta": "La madera", "razon": "R."},
        "cambio": "ya no nombra el material",
    }
    corrections = {"redactor": "p", "fecha": "f", "correcciones": [row]}
    (cleaning / "correcciones.json").write_text(json.dumps(corrections), encoding="utf-8")
    advice = [
        {"hallazgo": findings["keep"], "recomendacion": "mantener", "motivo": "es adecuado", "items": []},
        {"hallazgo": findings["fix"], "recomendacion": "reescribir", "motivo": "ver texto", "items": ["fix"]},
    ]
    (cleaning / "dudas.json").write_text(json.dumps({"redactor": "p", "fecha": "f", "dudas": advice}), "utf-8")
    assert corrections_report(nucleo, docs.corrections) == []
    assert doubts_report(nucleo, docs.doubts) == []
    return nucleo, datasets, cleaning, docs, [findings["keep"], findings["fix"]]


RULE = "solucion_en_enunciado"


def test_resolution_records_both_kinds_without_changing_content(tmp_path: Path):
    nucleo, datasets, cleaning, docs, _ = publish(tmp_path)
    content = (cleaning.parent / "items.jsonl").read_bytes()
    assert resolve_doubts(nucleo, datasets, "revisora", docs) == (1, 1)
    assert (cleaning.parent / "items.jsonl").read_bytes() == content
    [decision] = json.loads((cleaning / "decisiones.json").read_text(encoding="utf-8"))["decisiones"]
    assert decision["estado"] == "aceptado" and decision["aprobado_por"] == "revisora"
    sheet = docs.doubts.read_text(encoding="utf-8")
    assert "2 de 2 decididas" in sheet and "sin aplicar" in sheet
    assert doubts_report(nucleo, docs.doubts, check=True) == []
    assert resolve_doubts(nucleo, datasets, "otra", docs) == (0, 0)


def test_excluded_doubts_stay_open(tmp_path: Path):
    nucleo, datasets, cleaning, docs, (keep, _) = publish(tmp_path)
    assert resolve_doubts(nucleo, datasets, "revisora", docs, [keep]) == (0, 1)
    assert not (cleaning / "decisiones.json").exists()


@pytest.mark.parametrize(("approver", "exclude"), [(" ", []), ("r", ["inventado"])])
def test_resolution_is_refused(tmp_path: Path, approver: str, exclude: list[str]):
    nucleo, datasets, cleaning, docs, _ = publish(tmp_path)
    with pytest.raises(SystemExit):
        resolve_doubts(nucleo, datasets, approver, docs, exclude)
    assert not (cleaning / "decisiones.json").exists()
