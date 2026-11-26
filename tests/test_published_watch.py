"""La línea base y el informe publicados del vigía corresponden al núcleo."""

from __future__ import annotations

import json
from urllib.parse import urlsplit

from lpdatasets.watch import history, report
from lpdatasets.watch_escolar import affected_classes
from tests.conftest import ROOT

FOLDER = ROOT / "vigia" / "escolar-chile" / "1-basico"


def test_baseline_covers_every_objective_in_the_core():
    data = json.loads((FOLDER / "linea-base.json").read_text(encoding="utf-8"))
    known = {(s["asignatura"], o["codigo"]) for s in data["fuentes"] for o in s["objetivos"]}
    assert len(data["fuentes"]) == 11 and len(known) == 237
    assert set(affected_classes(ROOT / "nucleo")) <= known
    assert all(set(o) == {"codigo", "huella", "huella_sin_forma"} for s in data["fuentes"] for o in s["objetivos"])


def test_manual_sources_were_never_read():
    registry = json.loads((FOLDER / "fuentes.json").read_text(encoding="utf-8"))["fuentes"]
    manual = {urlsplit(s["url"]).netloc for s in registry if s["metodo"] == "manual"}
    for record in history(FOLDER):
        read = {urlsplit(r["url"]).netloc for r in record["resultados"] if r["verificacion"] != "sin_leer"}
        assert not manual & read


def test_published_report_is_up_to_date():
    assert report(FOLDER, ROOT / "docs" / "informes" / "vigia-1-basico.md", check=True) == []
