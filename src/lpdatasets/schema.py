"""Esquema común de registros (v1.0) y su validación sin dependencias externas."""

from __future__ import annotations

import hashlib
from typing import Any

SCHEMA_VERSION = "1.0"

TIPOS = (
    "explicacion",
    "ejemplo_resuelto",
    "ejercicio_cerrado",
    "autoevaluacion",
    "error_comun",
    "actividad_abierta",
    "vocabulario",
    "diccionario_es",
    "diccionario_en",
    "concepto",
    "hecho",
    "definicion",
    "relacion",
    "procedimiento",
    "concepcion_erronea",
)
REVISIONES = (
    "ia_asistida_sin_revision_humana",
    "revision_humana_parcial",
    "revision_humana_completa",
    "no_aplica",
)
PARTICIONES = ("train", "eval")
REQUIRED = (
    "schema",
    "id",
    "pack",
    "dominio",
    "nivel",
    "asignatura",
    "unidad",
    "tipo",
    "entrada",
    "salida",
    "idioma",
    "verificable",
    "fuente",
    "licencia",
    "revision",
    "particion",
)
FUENTE_KEYS = ("repo", "commit", "ruta")
EVAL_PERCENT = 10


def partition_for(pack: str, key: str) -> str:
    """Partición determinista por clase o unidad, para que nunca se mezclen entre train y eval."""
    digest = hashlib.sha256(f"{pack}|{key}".encode()).digest()
    return "eval" if digest[0] % 100 < EVAL_PERCENT else "train"


def validate_record(rec: Any) -> list[str]:
    """Devuelve la lista de problemas de un registro; vacía si es válido."""
    if not isinstance(rec, dict):
        return ["el registro no es un objeto"]
    problems: list[str] = []
    for key in REQUIRED:
        if key not in rec:
            problems.append(f"falta «{key}»")
    if problems:
        return problems
    if rec["schema"] != SCHEMA_VERSION:
        problems.append(f"schema {rec['schema']!r} distinto de {SCHEMA_VERSION}")
    for key in ("id", "pack", "dominio", "nivel", "asignatura", "unidad", "idioma", "licencia"):
        if not isinstance(rec[key], str) or not rec[key].strip():
            problems.append(f"«{key}» debe ser texto no vacío")
    for key in ("entrada", "salida"):
        if not isinstance(rec[key], str) or not rec[key].strip():
            problems.append(f"«{key}» debe ser texto no vacío")
    if rec["tipo"] not in TIPOS:
        problems.append(f"tipo desconocido: {rec['tipo']!r}")
    if rec["revision"] not in REVISIONES:
        problems.append(f"revision desconocida: {rec['revision']!r}")
    if rec["particion"] not in PARTICIONES:
        problems.append(f"particion desconocida: {rec['particion']!r}")
    if not isinstance(rec["verificable"], bool):
        problems.append("«verificable» debe ser booleano")
    fuente = rec["fuente"]
    if not isinstance(fuente, dict) or any(
        not isinstance(fuente.get(k), str) or not fuente.get(k) for k in FUENTE_KEYS
    ):
        problems.append("«fuente» necesita repo, commit y ruta")
    clase = rec.get("clase")
    if clase is not None and (not isinstance(clase, int) or isinstance(clase, bool) or clase < 1):
        problems.append("«clase» debe ser entero positivo o nulo")
    dificultad = rec.get("dificultad")
    if dificultad is not None and (
        not isinstance(dificultad, int) or isinstance(dificultad, bool) or not 1 <= dificultad <= 5
    ):
        problems.append("«dificultad» debe ser entero de 1 a 5 o nulo")
    razon = rec.get("razon")
    if razon is not None and (not isinstance(razon, str) or not razon.strip()):
        problems.append("«razon» debe ser texto no vacío o nulo")
    if "extra" in rec and not isinstance(rec["extra"], dict):
        problems.append("«extra» debe ser un objeto")
    return problems


def text_for_embedding(rec: dict[str, Any]) -> str:
    """Texto que representa un registro en el índice vectorial."""
    parts = [rec["entrada"], rec["salida"]]
    if rec.get("razon"):
        parts.append(rec["razon"])
    return " \n".join(parts)
