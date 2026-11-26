from __future__ import annotations

from pathlib import Path

import pytest

from lpdatasets import modalities
from tests.test_core import EXAMPLES


@pytest.fixture()
def registry(monkeypatch):
    monkeypatch.setattr(modalities, "REGISTRY", {})
    return modalities.REGISTRY


def test_new_modality_receives_only_filtered_data(registry, tmp_path: Path):
    received = []

    @modalities.register("ficticia")
    class Fake:
        linea = "L10"

        def build(self, entities, out):
            received.extend(entities)
            return len(entities)

    count = modalities.run(
        "ficticia", EXAMPLES, tmp_path, uso="educativo", publico="estudiante", marcos={"cl-bases-1-6"}
    )
    assert count == 3
    item = next(e for e in received if e["entidad"] == "item")
    assert "respuesta" not in item["contenido"]


def test_modality_without_documented_line_is_rejected(registry):
    with pytest.raises(ValueError, match="línea"):

        @modalities.register("sin-linea")
        class NoLine:
            def build(self, entities, out):
                return 0


def test_duplicate_and_unknown_modalities_are_rejected(registry, tmp_path: Path):
    class Fake:
        linea = "L10"

        def build(self, entities, out):
            return 0

    modalities.register("a")(Fake)
    with pytest.raises(ValueError):
        modalities.register("a")(Fake)
    with pytest.raises(ValueError):
        modalities.run("b", [], tmp_path, uso="educativo", publico="docente", marcos={"cl-bases-1-6"})
