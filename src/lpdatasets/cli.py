"""Línea de comandos: export, validate, stats, index, search y las órdenes del núcleo y de limpieza."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .build import build, stats, validate_datasets
from .cleaning import report
from .core_build import validate_core
from .core_escolar import export as export_core
from .vector import build_index, search


def _filters(args: argparse.Namespace) -> dict[str, str]:
    keys = ("pack", "dominio", "nivel", "asignatura", "tipo", "particion", "idioma")
    return {k: getattr(args, k) for k in keys if getattr(args, k, None)}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="lpdatasets", description=__doc__)
    parser.add_argument("--version", action="version", version=f"lpdatasets {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("export", help="genera un dataset JSONL desde un pack")
    p.add_argument("--pack", required=True)
    p.add_argument("--source", required=True, help="carpeta del programa de aprendizaje")
    p.add_argument("--nivel")
    p.add_argument("--out", default="datasets")
    p.add_argument("--pack-id", dest="pack_id")
    p.add_argument("--dominio")
    p.add_argument("--licencia")
    p.add_argument("--idioma")
    p.add_argument("--repo")

    p = sub.add_parser("core-export", help="exporta chilean-school-learning-path al núcleo")
    p.add_argument("--source", required=True, help="carpeta del programa de aprendizaje")
    p.add_argument("--nivel", default="1-basico")
    p.add_argument("--out", default="nucleo")

    p = sub.add_parser("core-validate", help="valida el núcleo publicado")
    p.add_argument("--nucleo", default="nucleo")

    p = sub.add_parser("clean-report", help="informe de limpieza; no modifica los datos")
    p.add_argument("--nucleo", default="nucleo")
    p.add_argument("--datasets", default="datasets")
    p.add_argument("--informe", default="docs/informes/limpieza-1-basico.md")
    p.add_argument("--check", action="store_true", help="falla si el informe está desactualizado")

    p = sub.add_parser("validate", help="valida esquema, hashes y particiones")
    p.add_argument("--datasets", default="datasets")

    p = sub.add_parser("stats", help="cuenta registros por dataset")
    p.add_argument("--datasets", default="datasets")

    p = sub.add_parser("index", help="construye la base vectorial")
    p.add_argument("--datasets", default="datasets")
    p.add_argument("--out", default=".vector")
    p.add_argument("--backend", choices=("numpy", "qdrant"), default="numpy")
    p.add_argument("--splits", default="train,eval", help="particiones a indexar, separadas por coma")

    p = sub.add_parser("search", help="busca en la base vectorial")
    p.add_argument("query")
    p.add_argument("--index", default=".vector")
    p.add_argument("-k", type=int, default=5)
    for f in ("pack", "dominio", "nivel", "asignatura", "tipo", "particion", "idioma"):
        p.add_argument(f"--{f}")
    p.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "export":
        extra = {
            k: getattr(args, k)
            for k in ("nivel", "pack_id", "dominio", "licencia", "idioma", "repo")
            if getattr(args, k)
        }
        folder = build(args.pack, Path(args.out), source=args.source, **extra)
        print(f"Dataset escrito en {folder}")
        return 0
    if args.cmd == "core-export":
        folder = export_core(Path(args.source), Path(args.out), args.nivel)
        print(f"Núcleo escrito en {folder}")
        return 0
    if args.cmd == "core-validate":
        problems = validate_core(Path(args.nucleo))
        print("\n".join(problems[:50]) if problems else "OK: núcleo válido")
        return 1 if problems else 0
    if args.cmd == "clean-report":
        stale = report(Path(args.nucleo), Path(args.datasets), Path(args.informe), args.check)
        print("\n".join(stale) if stale else "OK: informe de limpieza al día")
        return 1 if stale else 0
    if args.cmd == "validate":
        problems = validate_datasets(Path(args.datasets))
        print("\n".join(problems[:50]) if problems else "OK: datasets válidos")
        return 1 if problems else 0
    if args.cmd == "stats":
        print(json.dumps(stats(Path(args.datasets)), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "index":
        n = build_index(Path(args.datasets), Path(args.out), args.backend, splits=tuple(args.splits.split(",")))
        print(f"Indexados {n} registros en {args.out} ({args.backend})")
        return 0
    results = search(Path(args.index), args.query, args.k, _filters(args) or None)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"{r['score']:.3f}  [{r['tipo']}] {r['nivel']} · {r['asignatura']} · {r['unidad']}")
            print(f"       {r['entrada'][:110]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
