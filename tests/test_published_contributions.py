"""Los aportes publicados son válidos y su combinación no altera el núcleo publicado."""

from __future__ import annotations

from pathlib import Path

from lpdatasets.build import read_jsonl
from lpdatasets.contributions import export, read_pieces, report, state, vocabulary
from lpdatasets.core_build import read_core, validate_core
from tests.conftest import ROOT

NUCLEO = ROOT / "nucleo"
APORTES = ROOT / "aportes"
CORE = NUCLEO / "escolar-chile" / "1-basico"
FOLDER = APORTES / "escolar-chile" / "1-basico"


def test_published_report_is_up_to_date():
    doc = ROOT / "docs" / "informes" / "aportes-1-basico.md"
    assert report(NUCLEO, APORTES, doc, check=True) == []


def test_vocabulary_is_the_official_skill_objectives_in_the_core():
    expected: dict[str, set[str]] = {}
    for c in read_jsonl(CORE / "clases.jsonl"):
        if c["oa"].startswith("de Habilidad "):
            expected.setdefault(c["asignatura"], set()).add(c["oa"])
    found = vocabulary(FOLDER)["habilidades"]
    assert {k: set(v) for k, v in found.items()} == expected
    assert {k: len(v) for k, v in found.items()} == {
        "ciencias-naturales": 4,
        "historia-geografia-ciencias-sociales": 7,
        "matematica": 10,
    }


def test_composing_the_published_core_is_valid_and_leaves_it_untouched(tmp_path: Path):
    before = {p.name: p.read_bytes() for p in sorted(CORE.glob("*.json*"))}
    used = export(NUCLEO, APORTES, tmp_path)
    assert validate_core(tmp_path) == []
    entities = read_core(CORE)
    pieces = [p for rows in read_pieces(FOLDER).values() for p in rows]
    assert used == sum(state(entities, p) == "aprobada" for p in pieces)
    assert {p.name: p.read_bytes() for p in sorted(CORE.glob("*.json*"))} == before
    if not used:
        composed = tmp_path / "escolar-chile" / "1-basico"
        assert {n: (composed / n).read_bytes() for n in before} == before
