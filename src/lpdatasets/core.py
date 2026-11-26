"""Contrato del núcleo (nucleo-0.1): clases, ítems y recursos independientes de la modalidad que los use.

Cada entidad declara marco curricular, derechos, revisión y procedencia. `select` es la puerta de salida: filtra
por uso, público y marco, y quita las soluciones a quien no debe verlas. Es independiente del esquema de registros
v1.0 del dataset (`schema.py`).
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Collection, Iterable, Iterator
from pathlib import Path
from typing import Any

from .schema import FUENTE_KEYS, REVISIONES, TIPOS

CONTRACT = "nucleo-0.1"
ENTITIES = ("clase", "item", "recurso")
AUDIENCES = ("estudiante", "docente", "familia")
USES = ("personal", "educativo", "comercial")
ORIGINS = ("propio", "oficial", "tercero", "desconocido")
EDITORIAL = ("desarrollada", "integrada")
NON_COMMERCIAL = ("personal", "educativo")
# Usos que cada licencia permite por sí sola. Una licencia que no figura aquí no permite ninguno.
# Es una política operativa del proyecto, no asesoría legal.
LICENSE_USES: dict[str, tuple[str, ...]] = {
    "CC0-1.0": USES,
    "CC-BY-4.0": USES,
    "CC-BY-SA-4.0": USES,
    "CC-BY-NC-4.0": NON_COMMERCIAL,
    "CC-BY-NC-SA-4.0": NON_COMMERCIAL,
    "MINEDUC-NO-COMERCIAL": NON_COMMERCIAL,
}
COMMON = ("contrato", "entidad", "id", "marco", "nivel", "procedencia", "derechos", "revision")
SPECIFIC = {
    "clase": ("asignatura", "oa", "numero", "estado_editorial", "titulo"),
    "item": ("asignatura", "tipo", "publico", "publico_solucion", "contenido"),
    "recurso": ("medio", "publico"),
}
OPTIONAL = {
    "clase": ("extra",),
    "item": ("clase_id", "habilidades", "dificultad", "extra"),
    "recurso": ("clase_id", "texto", "uri", "sha256", "descripcion", "extra"),
}
SOLUTION_KEYS = ("respuesta", "razon")
MEDIA_TYPE = re.compile(r"^[a-z]+/[a-z0-9][a-z0-9.+-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MARCOS_FILE = Path(__file__).with_name("marcos.json")

Entity = dict[str, Any]


def load_marcos(path: Path = MARCOS_FILE) -> dict[str, dict[str, Any]]:
    """Marcos curriculares registrados, por identificador."""
    return {m["id"]: m for m in json.loads(path.read_text(encoding="utf-8"))["marcos"]}


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_audience(entity: Entity, key: str, allow_empty: bool = False) -> list[str]:
    value = entity[key]
    if not isinstance(value, list) or (not value and not allow_empty) or any(v not in AUDIENCES for v in value):
        return [f"«{key}» debe ser una lista de públicos entre {', '.join(AUDIENCES)}"]
    return []


def _check_rights(rights: Any) -> list[str]:
    if not isinstance(rights, dict):
        return ["«derechos» debe ser un objeto"]
    problems = [
        f"«derechos.{k}» debe ser texto no vacío" for k in ("licencia", "titular") if not _is_text(rights.get(k))
    ]
    if rights.get("origen") not in ORIGINS:
        problems.append(f"«derechos.origen» debe ser uno de {', '.join(ORIGINS)}")
    if str(rights.get("licencia", "")).startswith("CC-BY") and not _is_text(rights.get("atribucion")):
        problems.append("una licencia CC BY necesita «derechos.atribucion»")
    if "atribucion" in rights and not isinstance(rights["atribucion"], str):
        problems.append("«derechos.atribucion» debe ser texto")
    unknown = set(rights) - {"licencia", "titular", "origen", "atribucion", "autorizaciones"}
    if unknown:
        problems.append(f"campos desconocidos en «derechos»: {', '.join(sorted(unknown))}")
    grants = rights.get("autorizaciones", [])
    if not isinstance(grants, list) or any(
        not isinstance(g, dict) or g.get("uso") not in USES or not _is_text(g.get("referencia")) for g in grants
    ):
        problems.append("cada autorización necesita «uso» válido y «referencia»")
    elif grants and rights.get("origen") == "desconocido":
        problems.append("un contenido de origen desconocido no admite autorizaciones")
    return problems


def validate_entity(entity: Any, marcos: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Devuelve la lista de problemas de una entidad; vacía si es válida."""
    if not isinstance(entity, dict):
        return ["la entidad no es un objeto"]
    kind = entity.get("entidad")
    if kind not in ENTITIES:
        return [f"entidad desconocida: {kind!r}"]
    missing = [k for k in COMMON + SPECIFIC[kind] if k not in entity]
    if missing:
        return [f"falta «{k}»" for k in missing]
    problems: list[str] = []
    unknown = set(entity) - set(COMMON + SPECIFIC[kind] + OPTIONAL[kind])
    if unknown:
        problems.append(f"campos desconocidos: {', '.join(sorted(unknown))}")
    if entity["contrato"] != CONTRACT:
        problems.append(f"contrato {entity['contrato']!r} distinto de {CONTRACT}")
    for key in ("id", "nivel"):
        if not _is_text(entity[key]):
            problems.append(f"«{key}» debe ser texto no vacío")
    marcos = load_marcos() if marcos is None else marcos
    marco = marcos.get(entity["marco"]) if isinstance(entity["marco"], str) else None
    if marco is None:
        problems.append(f"marco curricular no registrado: {entity['marco']!r}")
    elif entity["nivel"] not in marco["niveles"]:
        problems.append(f"el marco {entity['marco']} no cubre el nivel {entity['nivel']!r}")
    source = entity["procedencia"]
    if not isinstance(source, dict) or set(source) != set(FUENTE_KEYS) or not all(map(_is_text, source.values())):
        problems.append("«procedencia» necesita exactamente repo, commit y ruta")
    problems += _check_rights(entity["derechos"])
    if entity["revision"] not in REVISIONES:
        problems.append(f"revision desconocida: {entity['revision']!r}")
    if "extra" in entity and not isinstance(entity["extra"], dict):
        problems.append("«extra» debe ser un objeto")
    if entity.get("clase_id") is not None and not _is_text(entity["clase_id"]):
        problems.append("«clase_id» debe ser texto no vacío o nulo")
    problems += {"clase": _check_class, "item": _check_item, "recurso": _check_resource}[kind](entity)
    return problems


def _check_class(entity: Entity) -> list[str]:
    problems = [f"«{k}» debe ser texto no vacío" for k in ("asignatura", "oa", "titulo") if not _is_text(entity[k])]
    number = entity["numero"]
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        problems.append("«numero» debe ser entero positivo")
    if entity["estado_editorial"] not in EDITORIAL:
        problems.append(f"«estado_editorial» debe ser uno de {', '.join(EDITORIAL)}")
    return problems


def _check_item(entity: Entity) -> list[str]:
    problems = [] if _is_text(entity["asignatura"]) else ["«asignatura» debe ser texto no vacío"]
    if entity["tipo"] not in TIPOS:
        problems.append(f"tipo desconocido: {entity['tipo']!r}")
    problems += _check_audience(entity, "publico")
    problems += _check_audience(entity, "publico_solucion", allow_empty=True)
    content = entity["contenido"]
    if not isinstance(content, dict) or not _is_text(content.get("enunciado")):
        problems.append("«contenido» necesita «enunciado»")
    elif set(content) - {"enunciado", *SOLUTION_KEYS} or not all(map(_is_text, content.values())):
        problems.append("«contenido» solo admite enunciado, respuesta y razon como texto no vacío")
    skills = entity.get("habilidades", [])
    if not isinstance(skills, list) or not all(map(_is_text, skills)):
        problems.append("«habilidades» debe ser una lista de texto")
    level = entity.get("dificultad")
    if level is not None and (not isinstance(level, int) or isinstance(level, bool) or not 1 <= level <= 5):
        problems.append("«dificultad» debe ser entero de 1 a 5 o nulo")
    return problems


def _check_resource(entity: Entity) -> list[str]:
    problems = _check_audience(entity, "publico")
    media = entity["medio"]
    if not isinstance(media, str) or not MEDIA_TYPE.match(media):
        return [*problems, "«medio» debe ser un tipo MIME, por ejemplo text/markdown o audio/mpeg"]
    if ("texto" in entity) == ("uri" in entity):
        problems.append("un recurso lleva «texto» o «uri», solo uno")
    for key in ("texto", "uri", "descripcion"):
        if key in entity and not _is_text(entity[key]):
            problems.append(f"«{key}» debe ser texto no vacío")
    if "uri" in entity and not (isinstance(entity.get("sha256"), str) and SHA256.match(entity["sha256"])):
        problems.append("un recurso con «uri» necesita su «sha256»")
    if not media.startswith("text/") and "descripcion" not in entity:
        problems.append("un recurso que no es texto necesita «descripcion» como alternativa accesible")
    return problems


def allows_use(rights: dict[str, Any], use: str) -> bool:
    """Verdadero si la licencia, o una autorización registrada, permite ese uso."""
    if use not in USES:
        raise ValueError(f"uso desconocido: {use!r}")
    if rights.get("origen") == "desconocido":
        return False
    if use in LICENSE_USES.get(rights.get("licencia", ""), ()):
        return True
    return any(g.get("uso") == use for g in rights.get("autorizaciones", []))


def select(entities: Iterable[Entity], *, uso: str, publico: str, marcos: Collection[str]) -> Iterator[Entity]:
    """Entrega copias de las entidades permitidas para un uso, un público y unos marcos elegidos de forma explícita.

    Falla ante una entidad inválida en vez de omitirla. Si el público no puede ver la solución de un ítem, quita
    `respuesta`, `razon` y `extra`, que también podrían revelarla.
    """
    if uso not in USES:
        raise ValueError(f"uso desconocido: {uso!r}")
    if publico not in AUDIENCES:
        raise ValueError(f"público desconocido: {publico!r}")
    known = load_marcos()
    if isinstance(marcos, str) or not marcos or set(marcos) - set(known):
        raise ValueError(f"«marcos» debe ser una colección de marcos registrados: {', '.join(sorted(known))}")
    for entity in entities:
        problems = validate_entity(entity, known)
        if problems:
            raise ValueError(f"entidad inválida {entity.get('id')!r}: {'; '.join(problems)}")
        if entity["marco"] not in marcos or not allows_use(entity["derechos"], uso):
            continue
        if "publico" in entity and publico not in entity["publico"]:
            continue
        result = copy.deepcopy(entity)
        if result["entidad"] == "item" and publico not in result["publico_solucion"]:
            for key in SOLUTION_KEYS:
                result["contenido"].pop(key, None)
            result.pop("extra", None)
        yield result
