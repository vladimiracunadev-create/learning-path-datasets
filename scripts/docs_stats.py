"""Mantiene al día las cifras de los documentos a partir de los manifiestos de `datasets/`.

python scripts/docs_stats.py --write   # reescribe los bloques entre marcadores
python scripts/docs_stats.py --check   # falla si algún documento tiene cifras desactualizadas
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", ROOT / "STATUS.md", ROOT / "docs" / "DATASET_CARD_escolar-chile.md"]
BEGIN, END = "<!-- STATS:BEGIN -->", "<!-- STATS:END -->"
BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def render() -> str:
    manifests = sorted((ROOT / "datasets").rglob("manifest.json"))
    lines = [
        BEGIN,
        "",
        "| Dataset | Registros | Entrenamiento | Evaluación | Clases (entr. / eval.) | Verificables por cálculo |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total = 0
    for path in manifests:
        m = json.loads(path.read_text(encoding="utf-8"))
        files = m["archivos"]
        total += m["total"]
        lines.append(
            f"| `{m['pack']}` · {m['nivel']} | {fmt(m['total'])} | {fmt(files['train.jsonl']['registros'])} "
            f"| {fmt(files['eval.jsonl']['registros'])} | {m['clases_train']} / {m['clases_eval']} "
            f"| {fmt(m['verificables'])} |"
        )
    lines += ["", f"**Total publicado:** {fmt(total)} registros en {len(manifests)} dataset(s).", ""]
    for path in manifests:
        m = json.loads(path.read_text(encoding="utf-8"))
        lines.append(
            f"Tipos en `{m['pack']}` · {m['nivel']}: "
            + ", ".join(f"{k} {fmt(v)}" for k, v in m["por_tipo"].items())
            + "."
        )
        lines.append("")
    lines.append(END)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    write = "--write" in argv
    block = render()
    stale = []
    for doc in DOCS:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        if not BLOCK.search(text):
            stale.append(f"{doc.name}: falta el bloque {BEGIN} … {END}")
            continue
        new = BLOCK.sub(lambda _: block, text)
        if new != text:
            if write:
                doc.write_text(new, encoding="utf-8", newline="\n")
            else:
                stale.append(f"{doc.name}: cifras desactualizadas (ejecuta scripts/docs_stats.py --write)")
    if stale and not write:
        print("\n".join(stale))
        return 1
    print("OK: cifras de los documentos al día" if not write else "Documentos actualizados")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
