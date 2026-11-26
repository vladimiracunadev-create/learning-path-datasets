"""Línea L04: registro de lo que una persona revisa en las fuentes que no admiten lectura automatizada.

Un registro es evidencia: nunca cambia `marcos.json`. Puede proponer el estado de un marco, y solo una fuente oficial
puede proponer que esté vigente.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any
from urllib.parse import urlsplit

RESULTS = ("sin_novedad", "novedad")
FRAMEWORK_STATES = ("vigente", "propuesta_sin_confirmar", "propuesta_no_obligatoria", "no_aplica")


def check_manual(entry: dict[str, Any], sources: Mapping[str, dict[str, Any]], marcos: Mapping[str, Any]) -> list[str]:
    """Problemas de un registro manual; vacío si se puede aceptar."""
    source = sources.get(entry.get("fuente", ""))
    if source is None:
        return [f"{entry.get('fuente')!r}: no es una fuente registrada"]
    problems = []
    try:
        date.fromisoformat(str(entry.get("fecha")))
    except ValueError:
        problems.append("falta una fecha válida (AAAA-MM-DD)")
    for key, what in (("revisado_por", "quién revisó"), ("nota", "qué se leyó, con palabras propias")):
        if not str(entry.get(key, "")).strip():
            problems.append(f"falta {what}")
    if entry.get("resultado") not in RESULTS:
        problems.append(f"el resultado debe ser {' o '.join(RESULTS)}")
    url = urlsplit(str(entry.get("url", "")))
    if url.scheme != "https" or url.netloc != urlsplit(source["url"]).netloc:
        problems.append("la dirección debe ser https y del mismo sitio que la fuente")
    framework, state = entry.get("marco"), entry.get("estado_marco")
    if framework or state:
        if framework not in marcos or state not in FRAMEWORK_STATES:
            problems.append("para proponer sobre un marco se necesitan un marco registrado y un estado válido")
        elif state == "vigente" and source["tipo"] != "oficial":
            problems.append(f"una fuente de tipo {source['tipo']} no puede marcar un marco como vigente")
    return [f"{source['id']}: {p}" for p in problems]


def check_marcos(marcos: Mapping[str, Mapping[str, Any]], sources: Mapping[str, dict[str, Any]]) -> list[str]:
    """Un marco vigente necesita una página oficial leída, en un sitio registrado como oficial."""
    official = {urlsplit(s["url"]).netloc for s in sources.values() if s["tipo"] == "oficial"}
    problems = []
    for name, marco in marcos.items():
        if marco["estado"] != "vigente":
            continue
        if marco["verificacion"] != "pagina_oficial_leida":
            problems.append(f"marco {name}: figura vigente sin una página oficial leída")
        if urlsplit(marco.get("url") or "").netloc not in official:
            problems.append(f"marco {name}: figura vigente con una dirección que no es de un sitio oficial registrado")
    return problems
