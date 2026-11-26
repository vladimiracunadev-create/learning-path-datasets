"""Línea L02: hoja de decisión de las dudas abiertas, con una recomendación por hallazgo. No decide nada.

Las recomendaciones están en `limpieza/dudas.json` y los textos propuestos en `limpieza/correcciones.json`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .build import read_jsonl
from .core_build import core_folders, read_core

KINDS = ("mantener", "reescribir", "aprobar redacción")
HEADINGS = {
    "mantener": "Mantener como está",
    "reescribir": "Reescribir",
    "aprobar redacción": "Aprobar la redacción ya escrita",
}
NEEDS_JUDGEMENT = ("decidir", "corregir")
LATER = ("etiquetas", "cruces-dataset")  # dependen de líneas posteriores, no de una decisión


def check_doubts(
    proposals: list[dict[str, Any]], doubts: list[dict[str, Any]], corrections: list[dict[str, Any]]
) -> list[str]:
    """Cada duda abierta necesita exactamente una recomendación y, si pide cambiar, su texto."""
    expected = {
        p["id"]
        for p in proposals
        if p["estado"] == "pendiente" and p["veredicto"] in NEEDS_JUDGEMENT and p["lote"] not in LATER
    }
    given = [d.get("hallazgo") for d in doubts]
    problems = [f"{i}: sin recomendación" for i in sorted(expected - set(given))]
    problems += [f"{i}: recomienda algo que ya no está abierto" for i in sorted(set(given) - expected)]
    problems += [f"{i}: recomendado dos veces" for i in sorted({i for i in given if given.count(i) > 1})]
    drafted = {c["item"] for c in corrections if not c.get("aplicada")}
    for d in doubts:
        if d.get("recomendacion") not in KINDS or not str(d.get("motivo", "")).strip():
            problems.append(f"{d.get('hallazgo')}: necesita recomendación ({', '.join(KINDS)}) y motivo")
        elif d["recomendacion"] != "mantener" and not drafted & set(d.get("items", [])):
            problems.append(f"{d['hallazgo']}: falta el texto propuesto")
    return problems


def render(
    doubts: dict[str, Any],
    items: dict[str, dict[str, str]],
    findings: dict[str, list[str]],
    corrections: list[dict[str, Any]],
) -> str:
    rows = doubts["dudas"]
    drafted = {c["item"]: c for c in corrections if not c.get("aplicada") and not c.get("aprobacion")}
    out = [
        "# Dudas abiertas · 1.º básico",
        "",
        "Generado con `lpdatasets clean-doubts`; no se edita a mano. **Son recomendaciones: nada está decidido.**",
        "",
        f"- Recomendaciones: {doubts['redactor']} ({doubts['fecha']}).",
        f"- Dudas: {len(rows)}.",
        "",
        "| Recomendación | Hallazgos |",
        "|---|---:|",
        *(f"| {HEADINGS[k]} | {sum(r['recomendacion'] == k for r in rows)} |" for k in KINDS),
    ]
    if doubts.get("segunda_lectura"):
        out += ["", "## Segunda lectura", "", *doubts["segunda_lectura"]]
    for kind in KINDS:
        group = [r for r in rows if r["recomendacion"] == kind]
        if not group:
            continue
        out += ["", f"## {HEADINGS[kind]}"]
        for r in group:
            out += ["", f"### `{r['hallazgo']}`", ""]
            if kind != "reescribir":
                out += [f"Motivo: {r['motivo']}.", ""]
            changes = [drafted[i] for i in r.get("items", []) if i in drafted]
            if changes:
                out += ["| Ítem | Ahora | Propuesto |", "|---|---|---|"]
                out += [
                    f"| `{c['item'].split(':', 2)[-1]}` | {_text(c['antes'])} | {_text(c['despues'])} |"
                    for c in changes
                ]
                notes = [f"`{c['item'].split(':', 2)[-1]}`: {c['duda']}" for c in changes if c.get("duda")]
                if notes:
                    out += ["", "**Para tu criterio:** " + "; ".join(notes) + "."]
            else:
                out += ["| Ítem | Texto actual |", "|---|---|"]
                out += [f"| `{i.split(':', 2)[-1]}` | {_text(items[i])} |" for i in findings[r["hallazgo"]]]
    return "\n".join(out) + "\n"


def _text(content: dict[str, str]) -> str:
    return " ".join(f"{content['enunciado']} → {content.get('respuesta', '')}".split()).replace("|", "/")


def doubts_report(nucleo: Path, doc: Path, check: bool = False) -> list[str]:
    """Valida las recomendaciones y escribe la hoja de decisión; con `check` no escribe."""
    folder = core_folders(nucleo)[0]
    cleaning = folder / "limpieza"
    doubts = json.loads((cleaning / "dudas.json").read_text(encoding="utf-8"))
    corrections = json.loads((cleaning / "correcciones.json").read_text(encoding="utf-8"))["correcciones"]
    problems = check_doubts(read_jsonl(cleaning / "propuestas.jsonl"), doubts["dudas"], corrections)
    if problems:
        return problems
    items = {e["id"]: e["contenido"] for e in read_core(folder) if e["entidad"] == "item"}
    findings = {f["id"]: f["entidades"] for f in read_jsonl(cleaning / "hallazgos.jsonl")}
    text = render(doubts, items, findings, corrections)
    if check:
        current = doc.read_text(encoding="utf-8") if doc.exists() else None
        return [] if current == text else [f"{doc}: desactualizado (ejecuta lpdatasets clean-doubts)"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(text, encoding="utf-8", newline="\n")
    return []
