"""Modalidades: cada forma de usar el contenido es un módulo que recibe del núcleo datos ya filtrados.

Agregar una no exige tocar el núcleo: se registra aquí desde su propio módulo y se documenta como línea en
`docs/lineas/`. Ver `docs/lineas/L10-modalidad-nueva.md`.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Iterable
from pathlib import Path
from typing import Protocol

from .core import Entity, select

LINE_ID = re.compile(r"^L\d{2}$")


class Modality(Protocol):
    linea: str

    def build(self, entities: list[Entity], out: Path) -> int: ...


REGISTRY: dict[str, type[Modality]] = {}


def register(name: str) -> Callable[[type[Modality]], type[Modality]]:
    def deco(cls: type[Modality]) -> type[Modality]:
        if name in REGISTRY:
            raise ValueError(f"modalidad ya registrada: {name}")
        if not LINE_ID.match(getattr(cls, "linea", "")):
            raise ValueError(f"la modalidad {name} debe declarar su línea documentada, por ejemplo linea = 'L11'")
        REGISTRY[name] = cls
        return cls

    return deco


def run(name: str, entities: Iterable[Entity], out: Path, *, uso: str, publico: str, marcos: Collection[str]) -> int:
    """Ejecuta una modalidad sobre la selección permitida; devuelve lo que la modalidad informe."""
    if name not in REGISTRY:
        raise ValueError(f"modalidad desconocida: {name}")
    selected = list(select(entities, uso=uso, publico=publico, marcos=marcos))
    return REGISTRY[name]().build(selected, out)
