"""La capa de aportes: qué entra, qué no y que el núcleo publicado nunca cambia."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from lpdatasets.build import read_jsonl
from lpdatasets.contributions import approve, check_pieces, compose, export, report, verify
from lpdatasets.core import select
from lpdatasets.core_build import read_core, validate_core, write_core
from tests.test_cleaning import item
from tests.test_core import CLASS

PREFIX = "aporte:demo:1-basico:"
CODE = "de Habilidad MA01 OAH a"
RIGHTS = {"licencia": "CC-BY-NC-SA-4.0", "titular": "Prueba", "origen": "propio", "atribucion": "Prueba"}
SOURCE = {"ref": CLASS["id"], "uso": "derivado", "licencia": "CC-BY-NC-SA-4.0"}
OK = {"por": "lector", "tipo": "ia", "veredicto": "aprobado", "nota": "contrastado con la clase"}


def exercise(ident: str, tipo: str = "ejercicio_cerrado", **values) -> dict:
    entity = item(ident, f"Pregunta {ident}", "Respuesta", tipo=tipo, clase_id=CLASS["id"], asignatura="matematica")
    for field in ("habilidades", "dificultad"):
        entity.pop(field, None)
    return entity | values


BASE = [CLASS, exercise("a"), exercise("b", "vocabulario")]


def label(name: str = "habilidad", **values) -> dict:
    piece = {"id": PREFIX + name, "tipo": "etiqueta", "clase": CLASS["id"], "campo": "habilidades", "valor": [CODE]}
    return piece | {"autor": {"nombre": "autora", "tipo": "ia"}, "fuentes": [SOURCE], "derechos": RIGHTS} | values


def new_item(name: str = "nuevo", **body) -> dict:
    piece = {"entidad": "item", "clase_id": CLASS["id"], "tipo": "ejercicio_cerrado", "publico": ["docente"]}
    piece |= {"publico_solucion": ["docente"], "contenido": {"enunciado": "¿Cuánto es 1 + 1?", "respuesta": "2"}}
    base = label(name) | {"tipo": "entidad", "pieza": piece | body}
    return {k: v for k, v in base.items() if k not in ("clase", "campo", "valor")}


class Layer:
    """Núcleo mínimo publicado en disco y su carpeta de aportes."""

    def __init__(self, root: Path, *pieces: dict) -> None:
        self.nucleo, self.aportes, self.doc = root / "nucleo", root / "aportes", root / "aportes.md"
        self.core = self.nucleo / "demo" / "1-basico"
        self.info = {"pack": "demo", "nivel": "1-basico", "commit_fuente": "abc"}
        self.info["cobertura"] = {"catalogo": 1, "representadas": 1, "excluidas": []}
        write_core(self.core, BASE, self.info)
        self.folder = self.aportes / "demo" / "1-basico"
        self.folder.mkdir(parents=True)
        words = {"habilidades": {"matematica": [CODE]}}
        (self.folder / "vocabulario.json").write_text(json.dumps(words), encoding="utf-8")
        self.write(*pieces)
        self.published = self.bytes(self.core)

    def write(self, *pieces: dict) -> None:
        text = "".join(json.dumps(p) + "\n" for p in pieces)
        (self.folder / "piezas.jsonl").write_text(text, encoding="utf-8")
        report(self.nucleo, self.aportes, self.doc)

    def pieces(self) -> list[dict]:
        return read_jsonl(self.folder / "piezas.jsonl")

    def verify(self, name: str, record: dict = OK) -> None:
        verify(self.nucleo, self.aportes, self.doc, PREFIX + name, dict(record), "2026-01-01")

    def approve(self) -> int:
        return approve(self.nucleo, self.aportes, self.doc, "revisora")

    def composed(self, out: Path) -> dict[str, dict]:
        export(self.nucleo, self.aportes, out)
        assert validate_core(out) == []
        return {e["id"]: e for e in read_core(out / "demo" / "1-basico")}

    @staticmethod
    def bytes(folder: Path) -> dict[str, bytes]:
        return {p.name: p.read_bytes() for p in sorted(folder.glob("*.json*"))}


def test_without_pieces_the_composed_core_is_the_published_one(tmp_path: Path):
    layer = Layer(tmp_path)
    layer.composed(tmp_path / "out")
    assert layer.bytes(tmp_path / "out" / "demo" / "1-basico") == layer.published


def test_a_piece_enters_only_after_verification_and_approval(tmp_path: Path):
    layer = Layer(tmp_path, label(), new_item())
    for step in (lambda: None, lambda: [layer.verify(n) for n in ("habilidad", "nuevo")]):
        step()
        assert layer.composed(tmp_path / "antes") == {e["id"]: e for e in BASE}
    assert layer.approve() == 2
    result = layer.composed(tmp_path / "despues")
    assert result["a"]["habilidades"] == [CODE] and result["a"]["extra"]["aportes"] == [PREFIX + "habilidad"]
    added = result[PREFIX + "nuevo"]
    assert added["asignatura"] == "matematica" and added["marco"] == CLASS["marco"]
    assert added["revision"] == "ia_asistida_sin_revision_humana"
    assert added["procedencia"]["commit"].startswith("huella:")
    assert layer.bytes(layer.core) == layer.published
    layer.composed(tmp_path / "otra")
    assert layer.bytes(tmp_path / "otra" / "demo" / "1-basico") == layer.bytes(tmp_path / "despues/demo/1-basico")
    assert "| aprobada | 1 | 1 |" in layer.doc.read_text(encoding="utf-8")


def test_hidden_answers_of_new_items_stay_hidden(tmp_path: Path):
    layer = Layer(tmp_path, new_item(publico=["estudiante", "docente"]))
    layer.verify("nuevo", OK | {"tipo": "persona"})
    layer.approve()
    result = layer.composed(tmp_path / "out")
    assert result[PREFIX + "nuevo"]["revision"] == "revision_humana_parcial"
    seen = select(result.values(), uso="educativo", publico="estudiante", marcos={CLASS["marco"]})
    [shown] = [e for e in seen if e["id"] == PREFIX + "nuevo"]
    assert shown["contenido"] == {"enunciado": "¿Cuánto es 1 + 1?"}


def test_a_label_can_be_limited_to_some_types(tmp_path: Path):
    layer = Layer(tmp_path, label(campo="dificultad", valor=2, tipos=["ejercicio_cerrado"]))
    layer.verify("habilidad")
    layer.approve()
    result = layer.composed(tmp_path / "out")
    assert result["a"]["dificultad"] == 2 and "dificultad" not in result["b"]


@pytest.mark.parametrize("change", ["piece", "source"])
def test_changing_the_piece_or_its_subject_expires_the_approval(tmp_path: Path, change: str):
    layer = Layer(tmp_path, new_item())
    layer.verify("nuevo")
    layer.approve()
    if change == "piece":
        [piece] = layer.pieces()
        piece["pieza"]["contenido"]["respuesta"] = "3"
        layer.write(piece)
    else:
        write_core(layer.core, [CLASS, exercise("a", contenido={"enunciado": "otra", "respuesta": "x"})], layer.info)
        report(layer.nucleo, layer.aportes, layer.doc)
    assert PREFIX + "nuevo" not in layer.composed(tmp_path / "out")
    assert "| caducada | 1 | 0 |" in layer.doc.read_text(encoding="utf-8")


def test_the_author_cannot_verify_and_unverified_pieces_cannot_be_approved(tmp_path: Path):
    layer = Layer(tmp_path, label())
    with pytest.raises(SystemExit, match="quien escribió"):
        layer.verify("habilidad", OK | {"por": " Autora "})
    with pytest.raises(SystemExit, match="solo se aprueban"):
        approve(layer.nucleo, layer.aportes, layer.doc, "revisora", [PREFIX + "habilidad"])
    layer.verify("habilidad", OK | {"veredicto": "observado"})
    assert layer.approve() == 0
    with pytest.raises(SystemExit, match="quién aprueba|quien aprueba"):
        approve(layer.nucleo, layer.aportes, layer.doc, " ")
    assert "aprobacion" not in layer.pieces()[0]


def test_a_hand_written_approval_without_verification_is_rejected(tmp_path: Path):
    forged = label(aprobacion={"por": "alguien", "huella": "x", "sobre": "y"})
    assert any("verificación favorable" in p for p in checked(tmp_path, forged))


def checked(tmp_path: Path, *pieces: dict, entities: list[dict] = BASE) -> list[str]:
    layer = Layer(tmp_path)
    return check_pieces(entities, list(pieces), layer.folder, PREFIX)


@pytest.mark.parametrize(
    ("piece", "message"),
    [
        (label(id="a"), "identificador debe empezar"),
        (label(autor={"nombre": "x"}), "autor"),
        (label(fuentes=[]), "al menos una fuente"),
        (label(fuentes=[{"ref": "x", "uso": "copiado"}]), "uso"),
        (label(fuentes=[SOURCE | {"licencia": "inventada"}]), "licencia conocida"),
        (label(derechos=RIGHTS | {"licencia": "CC-BY-4.0"}), "esa fuente no"),
        (label(derechos=RIGHTS | {"origen": "desconocido"}), "no permite ningún uso"),
        (label(valor=["inventada"]), "vocabulario"),
        (label(campo="titulo"), "campo"),
        (label(campo="dificultad", valor=9), "1 a 5"),
        (label(clase="otra"), "ningún ítem"),
        (label(item="a"), "solo uno"),
        (new_item(clase_id="otra"), "clase del núcleo"),
        (new_item(marco="sin-marco-oficial"), "no puede fijar"),
        (new_item(revision="revision_humana_completa"), "no puede fijar"),
        (new_item(contenido={}), "enunciado"),
        (new_item(entidad="clase"), "item o recurso"),
    ],
)
def test_defective_pieces_are_rejected(tmp_path: Path, piece: dict, message: str):
    assert any(message in p for p in checked(tmp_path, piece))


def test_consulting_a_source_does_not_limit_the_license(tmp_path: Path):
    open_piece = label(
        fuentes=[{"ref": "https://oficial.example", "uso": "consulta"}],
        derechos=RIGHTS | {"licencia": "CC-BY-4.0"},
    )
    assert checked(tmp_path, open_piece) == []


def test_labels_never_overwrite_the_source_or_each_other(tmp_path: Path):
    filled = [CLASS, exercise("a", habilidades=["de la fuente"])]
    assert any("no lo sobrescribe" in p for p in checked(tmp_path / "x", label(), entities=filled))
    assert any("ya lo llena" in p for p in checked(tmp_path / "y", label(), label("otra")))
    assert any("repetido" in p for p in checked(tmp_path / "z", label(), label()))


def test_a_file_resource_keeps_its_hash_and_stays_inside_the_layer(tmp_path: Path):
    layer = Layer(tmp_path)
    drawing = b"<svg xmlns='http://www.w3.org/2000/svg'/>"
    (layer.folder / "archivos").mkdir()
    (layer.folder / "archivos" / "hoja.svg").write_bytes(drawing)
    body = {"entidad": "recurso", "clase_id": CLASS["id"], "medio": "image/svg+xml", "publico": ["estudiante"]}
    body |= {"uri": "archivos/hoja.svg", "sha256": hashlib.sha256(drawing).hexdigest(), "descripcion": "Una hoja"}
    piece = new_item("hoja") | {"pieza": body}
    assert check_pieces(BASE, [piece], layer.folder, PREFIX) == []
    outside = piece | {"pieza": body | {"uri": "../../aportes.md"}}
    assert any("dentro de la carpeta" in p for p in check_pieces(BASE, [outside], layer.folder, PREFIX))
    wrong = piece | {"pieza": body | {"sha256": "0" * 64}}
    assert any("sha256" in p for p in check_pieces(BASE, [wrong], layer.folder, PREFIX))
    layer.write(piece)
    layer.verify("hoja")
    layer.approve()
    layer.composed(tmp_path / "out")
    assert (tmp_path / "out" / "demo" / "1-basico" / "archivos" / "hoja.svg").read_bytes() == drawing


def test_the_published_core_cannot_be_the_output(tmp_path: Path):
    layer = Layer(tmp_path)
    with pytest.raises(SystemExit, match="núcleo publicado"):
        export(layer.nucleo, layer.aportes, layer.nucleo)
    assert compose(BASE, {}) == sorted(BASE, key=lambda e: e["id"])
