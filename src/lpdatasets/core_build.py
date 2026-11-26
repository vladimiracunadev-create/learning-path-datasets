"""Escritura, lectura y validación de un núcleo publicado: JSONL por entidad más un manifiesto verificable."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .build import MANIFEST, dumps, read_jsonl, sha256_file
from .core import CONTRACT, Entity, load_marcos, validate_entity

FILES = {"clase": "clases.jsonl", "item": "items.jsonl", "recurso": "recursos.jsonl"}


def _counts(entities: list[Entity], key: str) -> dict[str, int]:
    return dict(sorted(Counter(e[key] for e in entities if key in e).items()))


def write_core(folder: Path, entities: Iterable[Entity], info: dict[str, Any]) -> dict[str, Any]:
    """Escribe las entidades ordenadas por identificador y devuelve el manifiesto. Falla si algo no es válido."""
    rows = sorted(entities, key=lambda e: str(e.get("id")))
    marcos = load_marcos()
    problems = [f"{e.get('id', '?')}: {p}" for e in rows for p in validate_entity(e, marcos)]
    problems += [f"id repetido: {i}" for i, n in Counter(e.get("id") for e in rows).items() if n > 1]
    if problems:
        raise SystemExit("entidades inválidas:\n" + "\n".join(problems[:30]))
    folder.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for kind, name in FILES.items():
        part = [e for e in rows if e["entidad"] == kind]
        path = folder / name
        path.write_text("".join(dumps(e) + "\n" for e in part), encoding="utf-8", newline="\n")
        files[name] = {"entidades": len(part), "sha256": sha256_file(path)}
    manifest = {
        **info,
        "contrato": CONTRACT,
        "total": len(rows),
        "archivos": files,
        "por_entidad": _counts(rows, "entidad"),
        "por_tipo": _counts(rows, "tipo"),
        "por_asignatura": _counts(rows, "asignatura"),
        "por_marco": _counts(rows, "marco"),
        "revision": sorted({e["revision"] for e in rows}),
        "licencia": sorted({e["derechos"]["licencia"] for e in rows}),
    }
    (folder / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return manifest


def read_core(folder: Path) -> list[Entity]:
    return [e for name in FILES.values() for e in read_jsonl(folder / name)]


def core_folders(root: Path) -> list[Path]:
    return sorted(p.parent for p in root.rglob(MANIFEST))


def validate_core(root: Path) -> list[str]:
    """Comprueba hashes, conteos, contrato, ids, referencias a clases y la conciliación de cobertura."""
    folders = core_folders(root)
    if not folders:
        return [f"no hay manifiestos en {root}"]
    marcos = load_marcos()
    problems: list[str] = []
    seen: set[str] = set()
    for folder in folders:
        manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
        entities: list[Entity] = []
        for kind, name in FILES.items():
            path = folder / name
            info = manifest["archivos"].get(name)
            if info is None or not path.exists():
                problems.append(f"{path}: falta el archivo o no está en el manifiesto")
                continue
            if sha256_file(path) != info["sha256"]:
                problems.append(f"{path}: el sha256 no coincide con el manifiesto")
            rows = read_jsonl(path)
            if len(rows) != info["entidades"]:
                problems.append(f"{path}: {len(rows)} entidades y el manifiesto dice {info['entidades']}")
            problems += [
                f"{path}:{e.get('id', '?')}: entidad en archivo equivocado" for e in rows if e.get("entidad") != kind
            ]
            entities += rows
        classes = {e.get("id") for e in entities if e.get("entidad") == "clase"}
        for entity in entities:
            ident = entity.get("id")
            problems += [f"{folder.name}:{ident}: {p}" for p in validate_entity(entity, marcos)]
            if ident in seen:
                problems.append(f"id repetido: {ident}")
            seen.add(ident)
            if entity.get("clase_id") is not None and entity["clase_id"] not in classes:
                problems.append(f"{folder.name}:{ident}: apunta a una clase inexistente {entity['clase_id']}")
        if len(entities) != manifest["total"]:
            problems.append(f"{folder}: {len(entities)} entidades y el manifiesto dice {manifest['total']}")
        problems += _check_coverage(folder, manifest["cobertura"], len(classes))
    return problems


def _check_coverage(folder: Path, coverage: dict[str, Any], classes: int) -> list[str]:
    problems = []
    excluded = coverage["excluidas"]
    if coverage["representadas"] != classes:
        problems.append(f"{folder}: la cobertura declara {coverage['representadas']} clases y hay {classes}")
    if classes + sum(x["clases"] for x in excluded) != coverage["catalogo"]:
        problems.append(f"{folder}: representadas más excluidas no suman las {coverage['catalogo']} del catálogo")
    if any(not x.get("motivo") for x in excluded):
        problems.append(f"{folder}: hay exclusiones sin motivo")
    return problems
