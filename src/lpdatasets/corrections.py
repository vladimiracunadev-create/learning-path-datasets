"""Línea L02: redacciones nuevas para las preguntas que hay que corregir, antes de llevarlas a la fuente.

No cambia el núcleo. Comprueba cada propuesta simulando el cambio en una copia: la pregunta nueva no puede
duplicar otra, entrar en conflicto con otra ni quedar respondida por el cuaderno de su clase. Que la redacción sea
buena para un niño lo decide una persona, y su aprobación queda en cada fila, ligada al texto aprobado.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from collections.abc import Collection
from pathlib import Path
from typing import Any

from .build import read_jsonl
from .cleaning import core_findings, normalize
from .core import Entity
from .core_build import core_folders, read_core
from .proposals import WORKED, statement_kind

FIELDS = ("enunciado", "respuesta", "razon")
BLOCKING = ("duplicado_exacto", "respuestas_en_conflicto", "recurso_ausente")
SHORT = 12  # una respuesta más corta puede aparecer en un ejemplo por casualidad
LONG = 30  # a partir de aquí, aparecer en cualquier otra parte del cuaderno ya la entrega


def fingerprint(content: dict[str, str]) -> str:
    """Huella del texto aprobado: si la redacción cambia, la aprobación deja de valer."""
    return hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def simulate(entities: list[Entity], corrections: list[dict[str, Any]]) -> list[Entity]:
    """Copia del núcleo con las preguntas nuevas, también en el cuaderno donde figuraba la anterior."""
    result = copy.deepcopy(entities)
    by_id = {e["id"]: e for e in result}
    notebooks = {
        e["clase_id"]: e
        for e in result
        if e["entidad"] == "recurso" and e.get("extra", {}).get("rol") == "cuaderno_estudiante"
    }
    for c in corrections:
        item = by_id[c["item"]]
        item["contenido"] = dict(c["despues"])
        notebook = notebooks.get(item.get("clase_id"))
        if notebook:
            notebook["texto"] = notebook["texto"].replace(c["antes"]["enunciado"], c["despues"]["enunciado"])
    return result


def check_corrections(
    entities: list[Entity], proposals: list[dict[str, Any]], corrections: list[dict[str, Any]]
) -> list[str]:
    """Problemas que impiden presentar las correcciones; vacío si todas pasan las comprobaciones de forma."""
    items = {e["id"]: e for e in entities if e["entidad"] == "item"}
    flagged = {
        ident: p["id"] for p in proposals if p["veredicto"] == "corregir" for ident in p.get("items_a_cambiar", [])
    }
    problems = [
        f"{i}: se pide corregir y no tiene redacción"
        for i in sorted(set(flagged))
        if i not in {c["item"] for c in corrections}
    ]
    seen: set[str] = set()
    for c in corrections:
        ident = c["item"]
        if ident not in items:
            problems.append(f"{ident}: no existe en el núcleo")
            continue
        if ident in seen:
            problems.append(f"{ident}: repetido")
        seen.add(ident)
        if c["antes"] != items[ident]["contenido"]:
            problems.append(f"{ident}: «antes» ya no coincide con el núcleo")
        new = c["despues"]
        if set(new) != set(FIELDS) or not all(isinstance(v, str) and v.strip() for v in new.values()):
            problems.append(f"{ident}: «despues» necesita {', '.join(FIELDS)}")
        elif normalize(new["enunciado"]) == normalize(c["antes"].get("enunciado", "")):
            problems.append(f"{ident}: el enunciado no cambia")
        if c.get("hallazgo") != flagged.get(ident):
            problems.append(f"{ident}: el hallazgo declarado no corresponde")
        if not str(c.get("cambio", "")).strip():
            problems.append(f"{ident}: falta explicar qué cambia")
        approval = c.get("aprobacion")
        if approval is not None:
            if not str(approval.get("por", "")).strip():
                problems.append(f"{ident}: la aprobación no dice quién aprueba")
            if approval.get("huella") != fingerprint(c["despues"]):
                problems.append(f"{ident}: el texto cambió después de aprobarse")
    if problems:
        return problems
    changed = simulate(entities, corrections)
    for found in core_findings(changed):
        if found["regla"] in BLOCKING:
            problems += [f"{i}: la redacción nueva activa {found['regla']}" for i in found["entidades"] if i in seen]
    statements: dict[str, list[str]] = {}
    for e in changed:
        if e["entidad"] == "item" and "estudiante" not in e["publico_solucion"]:
            statements.setdefault(normalize(e["contenido"]["enunciado"]), []).append(e["id"])
    problems += [
        f"{i}: repite el enunciado de otro ejercicio"
        for ids in statements.values()
        if len(ids) > 1
        for i in ids
        if i in seen
    ]
    notebooks = {
        e["clase_id"]: e.get("texto", "")
        for e in changed
        if e["entidad"] == "recurso" and e.get("extra", {}).get("rol") == "cuaderno_estudiante"
    }
    for c in corrections:
        answer = normalize(c["despues"]["respuesta"])
        notebook = normalize(notebooks.get(items[c["item"]].get("clase_id"), ""))
        # La respuesta puede estar en el propio enunciado (una elección); no en el resto del cuaderno.
        rest = notebook.replace(normalize(c["despues"]["enunciado"]), " ")
        worked = normalize(rest.partition(normalize(WORKED))[2].partition("**ejercicios**")[0])
        if len(answer) >= LONG and answer in rest:
            problems.append(f"{c['item']}: otra parte del cuaderno contiene la respuesta nueva")
        elif len(answer) >= SHORT and answer in worked:
            problems.append(f"{c['item']}: un ejemplo del cuaderno contiene la respuesta nueva")
    return sorted(set(problems))


def render(document: dict[str, Any]) -> str:
    rows = document["correcciones"]
    approved = [r for r in rows if r.get("aprobacion")]
    people = ", ".join(sorted({r["aprobacion"]["por"] for r in approved}))
    state = f"{len(approved)} de {len(rows)} aprobadas por {people}" if approved else "**sin aprobar**"
    out = [
        "# Correcciones propuestas · 1.º básico",
        "",
        "Generado con `lpdatasets clean-corrections`; no se edita a mano.",
        "",
        f"- Redacción: {document['redactor']} ({document['fecha']}).",
        f"- Estado: {state}. **No están aplicadas**: el núcleo y la fuente siguen igual.",
        f"- {len(rows)} preguntas. Detectadas al redactar, fuera de los hallazgos: "
        f"{sum(r['hallazgo'] is None for r in rows)}.",
    ]
    if document.get("segunda_lectura"):
        out += ["", "## Segunda lectura", "", *document["segunda_lectura"]]
    for number, row in enumerate(rows, 1):
        before, after = row["antes"], row["despues"]
        mark = "" if row["hallazgo"] else " · detectada al redactar"
        choice = statement_kind({"contenido": after}) == "otro" and normalize(after["respuesta"]) in normalize(
            after["enunciado"]
        )
        out += [
            "",
            f"## {number}. `{row['item'].split(':', 2)[-1]}`{mark}",
            "",
            f"Qué cambia: {row['cambio']}.",
            "",
            f"Estado: aprobada por {row['aprobacion']['por']}." if row.get("aprobacion") else "Estado: sin aprobar.",
            "",
            "| | Antes | Después |",
            "|---|---|---|",
            *(
                f"| {label} | {_cell(before.get(key, ''))} | {_cell(after[key])} |"
                for key, label in zip(FIELDS, ("Pregunta", "Respuesta", "Razón"), strict=True)
            ),
        ]
        if row.get("duda"):
            out += ["", f"**Para tu criterio:** {row['duda']}."]
        if choice:
            out += ["", "La respuesta nueva figura en el enunciado: confirmar que exige pensarla."]
    return "\n".join(out) + "\n"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "/")


def corrections_report(nucleo: Path, doc: Path, check: bool = False) -> list[str]:
    """Valida las correcciones y escribe su informe; con `check` no escribe."""
    folders = core_folders(nucleo)
    if len(folders) != 1:
        raise SystemExit(f"se esperaba un solo núcleo en {nucleo} y hay {len(folders)}")
    folder = folders[0] / "limpieza"
    document = json.loads((folder / "correcciones.json").read_text(encoding="utf-8"))
    problems = check_corrections(
        read_core(folders[0]), read_jsonl(folder / "propuestas.jsonl"), document["correcciones"]
    )
    if problems:
        return problems
    text = render(document)
    if check:
        current = doc.read_text(encoding="utf-8") if doc.exists() else None
        return [] if current == text else [f"{doc}: desactualizado (ejecuta lpdatasets clean-corrections)"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(text, encoding="utf-8", newline="\n")
    return []


def approve_corrections(nucleo: Path, doc: Path, approver: str, include: Collection[str] = ()) -> int:
    """Aprueba las correcciones sin duda abierta y las que se nombren en `include`; devuelve cuántas son nuevas.

    Aprobar no aplica el cambio: el núcleo y los hallazgos siguen como estaban.
    """
    if not approver.strip():
        raise SystemExit("falta el nombre de quien aprueba")
    problems = corrections_report(nucleo, doc, check=True)
    if problems:
        raise SystemExit(os.linesep.join(problems))
    path = core_folders(nucleo)[0] / "limpieza" / "correcciones.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document["correcciones"]
    named: set[str] = set()
    for name in include:
        found = [r["item"] for r in rows if r["item"] == name or r["item"].endswith(f":{name}")]
        if len(found) != 1:
            raise SystemExit(f"no se reconoce la corrección nombrada: {name}")
        named.add(found[0])
    new = [r for r in rows if not r.get("aprobacion") and (not r.get("duda") or r["item"] in named)]
    for row in new:
        row["aprobacion"] = {"por": approver.strip(), "huella": fingerprint(row["despues"])}
    text = json.dumps(document, ensure_ascii=False, indent=1) + chr(10)
    path.write_text(text, encoding="utf-8", newline=chr(10))
    corrections_report(nucleo, doc)
    return len(new)
