from __future__ import annotations

import copy
import json

import pytest

from lpdatasets.core import CONTRACT, allows_use, load_marcos, select, validate_entity
from lpdatasets.schema import TIPOS
from tests.conftest import ROOT

COMMON = {
    "contrato": CONTRACT,
    "marco": "cl-bases-1-6",
    "nivel": "1-basico",
    "procedencia": {"repo": "demo/repo", "commit": "abc123", "ruta": "a/b.md"},
    "derechos": {
        "licencia": "CC-BY-NC-SA-4.0",
        "titular": "Autoría de ejemplo",
        "origen": "propio",
        "atribucion": "Ejemplo sintético",
    },
    "revision": "ia_asistida_sin_revision_humana",
}
CLASS = {
    **COMMON,
    "entidad": "clase",
    "id": "demo:clase:1",
    "asignatura": "matematica",
    "oa": "MA01 OA 01",
    "numero": 1,
    "estado_editorial": "desarrollada",
    "titulo": "Contar de uno en uno",
}
ITEM = {
    **COMMON,
    "entidad": "item",
    "id": "demo:item:1",
    "asignatura": "matematica",
    "tipo": "ejercicio_cerrado",
    "publico": ["estudiante", "docente"],
    "publico_solucion": ["docente"],
    "contenido": {"enunciado": "¿Cuánto es 1 + 1?", "respuesta": "2", "razon": "Uno más uno es dos."},
    "clase_id": "demo:clase:1",
    "habilidades": [],
    "dificultad": 1,
    "extra": {"pista": "La respuesta es 2"},
}
RESOURCE = {
    **COMMON,
    "entidad": "recurso",
    "id": "demo:recurso:1",
    "medio": "audio/mpeg",
    "publico": ["estudiante"],
    "uri": "recursos/contar.mp3",
    "sha256": "a" * 64,
    "descripcion": "Una voz cuenta del uno al cinco.",
}
EXAMPLES = [CLASS, ITEM, RESOURCE]


def changed(base: dict, **values) -> dict:
    entity = copy.deepcopy(base)
    entity.update(values)
    return entity


def without(base: dict, key: str) -> dict:
    entity = copy.deepcopy(base)
    del entity[key]
    return entity


def rights(**values) -> dict:
    return {**COMMON["derechos"], **values}


INVALID = [
    changed(CLASS, entidad="video"),
    changed(CLASS, numero=0),
    changed(CLASS, idioma=""),
    changed(CLASS, estado_editorial="borrador"),
    changed(CLASS, inventado=True),
    without(CLASS, "derechos"),
    changed(CLASS, revision="aprobado"),
    changed(CLASS, procedencia={"repo": "x"}),
    changed(CLASS, derechos=rights(atribucion="")),
    changed(CLASS, derechos=rights(licencia="CC0-1.0", atribucion=7)),
    changed(CLASS, derechos=rights(origen="desconocido", autorizaciones=[{"uso": "comercial", "referencia": "x"}])),
    changed(CLASS, derechos=rights(autorizaciones=[{"uso": "comercial"}])),
    changed(ITEM, tipo="inventado"),
    changed(ITEM, publico=[]),
    changed(ITEM, publico_solucion=["todos"]),
    changed(ITEM, contenido={"respuesta": "2"}),
    changed(ITEM, dificultad=9),
    changed(RESOURCE, medio="audio"),
    changed(RESOURCE, texto="duplicado"),
    without(RESOURCE, "sha256"),
    without(RESOURCE, "descripcion"),
]


@pytest.mark.parametrize("entity", EXAMPLES, ids=lambda e: e["entidad"])
def test_valid_entities_pass(entity):
    assert validate_entity(entity) == []


@pytest.mark.parametrize("entity", INVALID)
def test_invalid_entities_are_rejected(entity):
    assert validate_entity(entity)


def test_json_schema_file_agrees_with_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "schema" / "core.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    for entity in EXAMPLES:
        assert validator.is_valid(entity), entity["id"]
    for entity in INVALID:
        assert not validator.is_valid(entity), entity
    assert schema["$defs"]["item"]["properties"]["tipo"]["enum"] == list(TIPOS)


def test_new_media_type_needs_no_contract_change():
    assert validate_entity(changed(RESOURCE, medio="model/gltf-binary")) == []


def test_framework_must_be_registered_and_cover_the_level():
    assert validate_entity(changed(CLASS, marco="otro"))
    assert validate_entity(changed(CLASS, marco="cl-propuesta-ingles-1b", nivel="2-basico"))


def test_unconfirmed_framework_is_never_marked_as_current():
    for marco in load_marcos().values():
        if marco["estado"] == "vigente":
            assert marco["verificacion"] == "pagina_oficial_leida"


@pytest.mark.parametrize(
    ("derechos", "uso", "expected"),
    [
        (rights(), "educativo", True),
        (rights(), "comercial", False),
        (rights(licencia="CC-BY-4.0"), "comercial", True),
        (rights(licencia="MINEDUC-NO-COMERCIAL", origen="oficial"), "comercial", False),
        (rights(licencia="licencia-rara"), "personal", False),
        (rights(licencia="CC0-1.0", origen="desconocido"), "personal", False),
        (rights(autorizaciones=[{"uso": "comercial", "referencia": "permiso firmado"}]), "comercial", True),
    ],
)
def test_allowed_uses(derechos, uso, expected):
    assert allows_use(derechos, uso) is expected


def test_student_view_hides_solution_without_touching_the_original():
    original = copy.deepcopy(ITEM)
    [seen] = select([original], uso="educativo", publico="estudiante", marcos={"cl-bases-1-6"})
    assert seen["contenido"] == {"enunciado": "¿Cuánto es 1 + 1?"}
    assert "extra" not in seen
    assert original == ITEM


def test_teacher_view_keeps_solution():
    [seen] = select([ITEM], uso="educativo", publico="docente", marcos={"cl-bases-1-6"})
    assert seen["contenido"]["respuesta"] == "2"


def test_selection_filters_by_use_audience_and_framework():
    ids = lambda **kw: [e["id"] for e in select(EXAMPLES, **kw)]  # noqa: E731
    assert ids(uso="comercial", publico="docente", marcos={"cl-bases-1-6"}) == []
    assert ids(uso="educativo", publico="familia", marcos={"cl-bases-1-6"}) == ["demo:clase:1"]
    assert ids(uso="educativo", publico="docente", marcos={"cl-bases-1-6-propuesta-2026"}) == []


@pytest.mark.parametrize(
    "kwargs",
    [
        {"uso": "otro", "publico": "docente", "marcos": {"cl-bases-1-6"}},
        {"uso": "educativo", "publico": "otro", "marcos": {"cl-bases-1-6"}},
        {"uso": "educativo", "publico": "docente", "marcos": set()},
        {"uso": "educativo", "publico": "docente", "marcos": "cl-bases-1-6"},
        {"uso": "educativo", "publico": "docente", "marcos": {"inventado"}},
    ],
)
def test_selection_rejects_unknown_criteria(kwargs):
    with pytest.raises(ValueError):
        list(select(EXAMPLES, **kwargs))


def test_selection_fails_loudly_on_invalid_entity():
    with pytest.raises(ValueError, match="demo:item:1"):
        list(select([changed(ITEM, tipo="x")], uso="educativo", publico="docente", marcos={"cl-bases-1-6"}))
