"""Packs: un adaptador por programa de aprendizaje, todos hacia el mismo esquema."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

Record = dict[str, Any]
PackFn = Callable[..., Iterator[Record]]

REGISTRY: dict[str, PackFn] = {}


def register(pack_id: str) -> Callable[[PackFn], PackFn]:
    def deco(fn: PackFn) -> PackFn:
        REGISTRY[pack_id] = fn
        return fn

    return deco


def load_builtin() -> None:
    """Importa los packs incluidos para que se registren."""
    from . import escolar_chile, markdown_course  # noqa: F401
