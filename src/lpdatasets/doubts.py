"""Línea L02: hoja de decisión de las dudas abiertas, con una recomendación por hallazgo, y registro de lo decidido.

Las recomendaciones están en `limpieza/dudas.json` y los textos propuestos en `limpieza/correcciones.json`.
`resolve_doubts` es el único paso que decide, y solo con el nombre de quien aprueba. No cambia el contenido.
"""

from __future__ import annotations

import json
import os
from collections.abc import Collection
from pathlib import Path
from typing import Any, NamedTuple

from .build import read_jsonl
from .cleaning import report
from .core_build import core_folders, read_core
from .corrections import corrections_report, fingerprint
from .proposals import proposals_report

KINDS = ("mantener", "reescribir", "aprobar redacción")
HEADINGS = {
    "mantener": "Mantener como está",
    "reescribir": "Reescribir",
    "aprobar redacción": "Aprobar la redacción ya escrita",
}
NEEDS_JUDGEMENT = ("decidir", "corregir")
LATER = ("etiquetas", "cruces-dataset")  # dependen de líneas posteriores, no de una decisión


class Docs(NamedTuple):
    """Informes que una resolución comprueba antes y regenera después."""

    clean: Path
    proposals: Path
    corrections: Path
    doubts: Path


def check_doubts(
    proposals: list[dict[str, Any]],
    doubts: list[dict[str, Any]],
    corrections: list[dict[str, Any]],
    resolved: Collection[str] = (),
) -> list[str]:
    """Cada duda abierta necesita exactamente una recomendación y, si pide cambiar, su texto.

    Las que ya se decidieron o resolvieron se conservan en la hoja como historial.
    """
    expected = {
        p["id"]
        for p in proposals
        if p["estado"] == "pendiente" and p["veredicto"] in NEEDS_JUDGEMENT and p["lote"] not in LATER
    }
    decided = {p["id"] for p in proposals if p["estado"] != "pendiente"} | set(resolved)
    given = [d.get("hallazgo") for d in doubts]
    problems = [f"{i}: sin recomendación" for i in sorted(expected - set(given))]
    problems += [f"{i}: recomienda algo que ya no está abierto" for i in sorted(set(given) - expected - decided)]
    problems += [f"{i}: recomendado dos veces" for i in sorted({i for i in given if given.count(i) > 1})]
    drafted = {c["item"] for c in corrections if not c.get("aplicada")}
    for d in doubts:
        if d.get("recomendacion") not in KINDS or not str(d.get("motivo", "")).strip():
            problems.append(f"{d.get('hallazgo')}: necesita recomendación ({', '.join(KINDS)}) y motivo")
        elif d["recomendacion"] != "mantener" and d["hallazgo"] in expected and not drafted & set(d.get("items", [])):
            problems.append(f"{d['hallazgo']}: falta el texto propuesto")
    return problems


def _decision(entry: dict[str, Any], rows: dict[str, dict[str, Any]], decisions: dict[str, str]) -> str | None:
    """Qué se decidió sobre una duda, si algo se decidió."""
    if entry["hallazgo"] in decisions:
        return f"mantener como está, aprobado por {decisions[entry['hallazgo']]}"
    if entry["recomendacion"] == "mantener":
        return None
    chosen = [rows[i] for i in entry.get("items", []) if i in rows]
    if not chosen or not all(c.get("aprobacion") for c in chosen):
        return None
    people = ", ".join(sorted({c["aprobacion"]["por"] for c in chosen}))
    state = "aplicados en la fuente" if all(c.get("aplicada") for c in chosen) else "sin aplicar"
    return f"textos aprobados por {people}; {state}"


def render(
    doubts: dict[str, Any],
    items: dict[str, dict[str, str]],
    findings: dict[str, list[str]],
    corrections: list[dict[str, Any]],
    decisions: dict[str, str] | None = None,
) -> str:
    rows = doubts["dudas"]
    by_item = {c["item"]: c for c in corrections}
    made = {r["hallazgo"]: _decision(r, by_item, decisions or {}) for r in rows}
    count = sum(bool(v) for v in made.values())
    state = f"{count} de {len(rows)} decididas" if count else "**Son recomendaciones: nada está decidido.**"
    out = [
        "# Dudas · 1.º básico",
        "",
        f"Generado con `lpdatasets clean-doubts`; no se edita a mano. {state}",
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
            if made[r["hallazgo"]]:
                out += [f"**Decisión:** {made[r['hallazgo']]}.", ""]
            if kind != "reescribir":
                out += [f"Motivo: {r['motivo']}.", ""]
            changes = [by_item[i] for i in r.get("items", []) if i in by_item]
            if changes:
                out += ["| Ítem | Antes | Propuesto |", "|---|---|---|"]
                out += [
                    f"| `{c['item'].split(':', 2)[-1]}` | {_text(c['antes'])} | {_text(c['despues'])} |"
                    for c in changes
                ]
                notes = [f"`{c['item'].split(':', 2)[-1]}`: {c['duda']}" for c in changes if c.get("duda")]
                if notes:
                    out += ["", "**Observación de la lectura:** " + "; ".join(notes) + "."]
            else:
                out += ["| Ítem | Texto |", "|---|---|"]
                out += [f"| `{i.split(':', 2)[-1]}` | {_text(items[i])} |" for i in findings.get(r["hallazgo"], [])]
    return "\n".join(out) + "\n"


def _text(content: dict[str, str]) -> str:
    return " ".join(f"{content['enunciado']} → {content.get('respuesta', '')}".split()).replace("|", "/")


def _load(path: Path, default: Any = None) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def doubts_report(nucleo: Path, doc: Path, check: bool = False) -> list[str]:
    """Valida las recomendaciones y escribe la hoja de decisión; con `check` no escribe."""
    folder = core_folders(nucleo)[0]
    cleaning = folder / "limpieza"
    doubts = _load(cleaning / "dudas.json")
    corrections = _load(cleaning / "correcciones.json")["correcciones"]
    archive = cleaning / "resueltos.jsonl"
    resolved = {f["id"] for f in read_jsonl(archive)} if archive.exists() else set()
    problems = check_doubts(read_jsonl(cleaning / "propuestas.jsonl"), doubts["dudas"], corrections, resolved)
    if problems:
        return problems
    items = {e["id"]: e["contenido"] for e in read_core(folder) if e["entidad"] == "item"}
    findings = {f["id"]: f["entidades"] for f in read_jsonl(cleaning / "hallazgos.jsonl")}
    asked = {d["hallazgo"] for d in doubts["dudas"] if d["recomendacion"] == "mantener"}
    decisions = {
        d["id"]: d["aprobado_por"]
        for d in _load(cleaning / "decisiones.json", {"decisiones": []})["decisiones"]
        if d["id"] in asked
    }
    text = render(doubts, items, findings, corrections, decisions)
    if check:
        current = doc.read_text(encoding="utf-8") if doc.exists() else None
        return [] if current == text else [f"{doc}: desactualizado (ejecuta lpdatasets clean-doubts)"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(text, encoding="utf-8", newline="\n")
    return []


def resolve_doubts(
    nucleo: Path, datasets: Path, approver: str, docs: Docs, exclude: Collection[str] = ()
) -> tuple[int, int]:
    """Registra la aprobación de las recomendaciones, salvo los hallazgos de `exclude`.

    «Mantener» queda como decisión sobre el hallazgo; los textos nuevos o ya redactados quedan aprobados, sin
    aplicar. Devuelve (hallazgos mantenidos, textos aprobados) que son nuevos.
    """
    if not approver.strip():
        raise SystemExit("falta el nombre de quien aprueba")
    stale = report(nucleo, datasets, docs.clean, check=True)
    stale += proposals_report(nucleo, docs.proposals, check=True)
    stale += corrections_report(nucleo, docs.corrections, check=True)
    stale += doubts_report(nucleo, docs.doubts, check=True)
    if stale:
        raise SystemExit(os.linesep.join(stale))
    cleaning = core_folders(nucleo)[0] / "limpieza"
    entries = _load(cleaning / "dudas.json")["dudas"]
    unknown = set(exclude) - {e["hallazgo"] for e in entries}
    if unknown:
        raise SystemExit(f"no son dudas registradas: {', '.join(sorted(unknown))}")
    open_ids = {p["id"] for p in read_jsonl(cleaning / "propuestas.jsonl") if p["estado"] == "pendiente"}
    chosen = [e for e in entries if e["hallazgo"] in open_ids and e["hallazgo"] not in exclude]

    decisions = _load(cleaning / "decisiones.json", {"decisiones": []})["decisiones"]
    kept = [
        {
            "id": e["hallazgo"],
            "estado": "aceptado",
            "motivo": f"duda resuelta, mantener: {e['motivo']}",
            "aprobado_por": approver.strip(),
        }
        for e in chosen
        if e["recomendacion"] == "mantener"
    ]
    document = _load(cleaning / "correcciones.json")
    wanted = {i for e in chosen if e["recomendacion"] != "mantener" for i in e["items"]}
    texts = [r for r in document["correcciones"] if r["item"] in wanted and not r.get("aprobacion")]
    for row in texts:
        row["aprobacion"] = {"por": approver.strip(), "huella": fingerprint(row["despues"])}
    if kept:
        _save(cleaning / "decisiones.json", {"decisiones": sorted(decisions + kept, key=lambda d: d["id"])})
    if texts:
        _save(cleaning / "correcciones.json", document)
    report(nucleo, datasets, docs.clean)
    proposals_report(nucleo, docs.proposals)
    corrections_report(nucleo, docs.corrections)
    doubts_report(nucleo, docs.doubts)
    return len(kept), len(texts)
