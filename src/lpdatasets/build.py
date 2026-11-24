"""Construcción, validación y estadísticas de datasets JSONL con manifiesto verificable."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .packs import REGISTRY, load_builtin
from .schema import SCHEMA_VERSION, validate_record

MANIFEST = "manifest.json"


def dumps(rec: dict[str, Any]) -> str:
    return json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build(pack: str, out_root: Path, /, **kwargs: Any) -> Path:
    """Genera train.jsonl, eval.jsonl y manifest.json de un pack; devuelve la carpeta."""
    load_builtin()
    if pack not in REGISTRY:
        raise SystemExit(f"pack desconocido: {pack}. Disponibles: {', '.join(sorted(REGISTRY))}")
    records = sorted(REGISTRY[pack](**kwargs), key=lambda r: r["id"])
    if not records:
        raise SystemExit("el pack no produjo registros")
    problems = [f"{r.get('id', '?')}: {p}" for r in records for p in validate_record(r)]
    ids = Counter(r["id"] for r in records)
    problems += [f"id repetido: {i}" for i, n in ids.items() if n > 1]
    if problems:
        raise SystemExit("registros inválidos:\n" + "\n".join(problems[:30]))
    nivel = kwargs.get("nivel", records[0]["nivel"])
    folder = out_root / records[0]["pack"] / nivel
    folder.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for split in ("train", "eval"):
        part = [r for r in records if r["particion"] == split]
        path = folder / f"{split}.jsonl"
        path.write_text("".join(dumps(r) + "\n" for r in part), encoding="utf-8", newline="\n")
        files[f"{split}.jsonl"] = {"registros": len(part), "sha256": sha256_file(path)}
    manifest = {
        "schema": SCHEMA_VERSION,
        "pack": records[0]["pack"],
        "nivel": nivel,
        "fuente": records[0]["fuente"]["repo"],
        "commit_fuente": records[0]["fuente"]["commit"],
        "licencia": sorted({r["licencia"] for r in records}),
        "revision": sorted({r["revision"] for r in records}),
        "total": len(records),
        "archivos": files,
        "por_tipo": dict(sorted(Counter(r["tipo"] for r in records).items())),
        "por_asignatura": dict(sorted(Counter(r["asignatura"] for r in records).items())),
        "por_idioma": dict(sorted(Counter(r["idioma"] for r in records).items())),
        "verificables": sum(1 for r in records if r["verificable"]),
        "clases_train": len({(r["unidad"], r["clase"]) for r in records if r["clase"] and r["particion"] == "train"}),
        "clases_eval": len({(r["unidad"], r["clase"]) for r in records if r["clase"] and r["particion"] == "eval"}),
    }
    (folder / MANIFEST).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return folder


def manifests(root: Path) -> list[Path]:
    return sorted(root.rglob(MANIFEST))


def validate_datasets(root: Path) -> list[str]:
    """Comprueba esquema, ids únicos, hashes, conteos y que train y eval no compartan clases."""
    problems: list[str] = []
    found = manifests(root)
    if not found:
        return [f"no hay manifiestos en {root}"]
    seen_ids: set[str] = set()
    for mpath in found:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        folder = mpath.parent
        classes: dict[str, set[tuple[str, int]]] = {"train": set(), "eval": set()}
        total = 0
        for name, info in manifest["archivos"].items():
            path = folder / name
            if not path.exists():
                problems.append(f"{path}: falta el archivo")
                continue
            if sha256_file(path) != info["sha256"]:
                problems.append(f"{path}: el sha256 no coincide con el manifiesto")
            rows = read_jsonl(path)
            if len(rows) != info["registros"]:
                problems.append(f"{path}: {len(rows)} registros y el manifiesto dice {info['registros']}")
            split = name.removesuffix(".jsonl")
            for rec in rows:
                total += 1
                problems += [f"{path}:{rec.get('id', '?')}: {p}" for p in validate_record(rec)]
                if rec.get("particion") != split:
                    problems.append(f"{path}:{rec.get('id', '?')}: partición {rec.get('particion')!r} en {name}")
                if rec.get("id") in seen_ids:
                    problems.append(f"id repetido: {rec.get('id')}")
                seen_ids.add(rec.get("id"))
                if rec.get("clase"):
                    classes.setdefault(split, set()).add((rec["unidad"], rec["clase"]))
        if total != manifest["total"]:
            problems.append(f"{folder}: {total} registros y el manifiesto dice {manifest['total']}")
        shared = classes["train"] & classes["eval"]
        if shared:
            problems.append(f"{folder}: {len(shared)} clases aparecen en train y en eval")
    return problems


def stats(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"datasets": [], "registros": 0}
    for mpath in manifests(root):
        m = json.loads(mpath.read_text(encoding="utf-8"))
        out["datasets"].append({"pack": m["pack"], "nivel": m["nivel"], "total": m["total"]})
        out["registros"] += m["total"]
    return out
