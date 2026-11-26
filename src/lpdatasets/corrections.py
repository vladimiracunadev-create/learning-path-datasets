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
from typing import Any, NamedTuple

from .build import dumps, read_jsonl
from .cleaning import all_findings, core_findings, dataset_records, normalize
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
        if not notebook:
            continue
        if item["tipo"] == "vocabulario":
            old, new = (f"| {x['enunciado']} | {x['respuesta']} |" for x in (c["antes"], c["despues"]))
        else:
            old, new = c["antes"]["enunciado"], c["despues"]["enunciado"]
        notebook["texto"] = notebook["texto"].replace(old, new)
    return result


def check_corrections(
    entities: list[Entity],
    proposals: list[dict[str, Any]],
    corrections: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[str]:
    """Problemas que impiden presentar las correcciones; vacío si todas pasan las comprobaciones de forma."""
    items = {e["id"]: e for e in entities if e["entidad"] == "item"}
    flagged = {
        ident: p["id"] for p in proposals if p["veredicto"] == "corregir" for ident in p.get("items_a_cambiar", [])
    }
    drafted = {c["item"] for c in corrections}
    still_open = {p["id"] for p in proposals if p["veredicto"] != "aceptar"}
    members = {f["id"]: set(f["entidades"]) for f in findings if f["id"] in still_open}
    problems = [f"{i}: se pide corregir y no tiene redacción" for i in sorted(set(flagged) - drafted)]
    seen: set[str] = set()
    for c in (c for c in corrections if c.get("aplicada")):
        current = items.get(c["item"], {}).get("contenido")
        if current != c["despues"]:
            problems.append(f"{c['item']}: figura como aplicada y el núcleo tiene otro texto")
        if (c.get("aprobacion") or {}).get("huella") != fingerprint(c["despues"]):
            problems.append(f"{c['item']}: figura como aplicada sin una aprobación de ese texto")
    corrections = [c for c in corrections if not c.get("aplicada")]
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
        wanted = set(items[ident]["contenido"])
        if set(new) != wanted or not all(isinstance(v, str) and v.strip() for v in new.values()):
            problems.append(f"{ident}: «despues» necesita {', '.join(k for k in FIELDS if k in wanted)}")
        elif all(normalize(new[k]) == normalize(c["antes"].get(k, "")) for k in new):
            problems.append(f"{ident}: no cambia nada")
        elif items[ident]["tipo"] != "vocabulario" and normalize(new["enunciado"]) == normalize(
            c["antes"].get("enunciado", "")
        ):
            problems.append(f"{ident}: el enunciado no cambia")
        declared = c.get("hallazgo")
        if (declared is None and ident in flagged) or (declared and ident not in members.get(declared, ())):
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
    # Un glosario repite palabras y definiciones entre clases; esas reglas solo bloquean ejercicios.
    exercises = {i for i in seen if items[i]["tipo"] != "vocabulario"}
    for found in core_findings(changed):
        if found["regla"] in BLOCKING:
            problems += [
                f"{i}: la redacción nueva activa {found['regla']}" for i in found["entidades"] if i in exercises
            ]
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
    for c in (c for c in corrections if c["item"] in exercises):
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
    applied = sum(bool(r.get("aplicada")) for r in rows)
    where = f"{applied} de {len(rows)} aplicadas en la fuente" if applied else "ninguna aplicada"
    out = [
        "# Correcciones propuestas · 1.º básico",
        "",
        "Generado con `lpdatasets clean-corrections`; no se edita a mano.",
        "",
        f"- Redacción: {document['redactor']} ({document['fecha']}).",
        f"- Estado: {state}; **{where}**.",
        f"- Textos (preguntas y definiciones): {len(rows)}. Detectados al redactar, fuera de los hallazgos: "
        f"{sum(r['hallazgo'] is None for r in rows)}.",
    ]
    if document.get("segunda_lectura"):
        out += ["", "## Segunda lectura", "", *document["segunda_lectura"]]
    for number, row in enumerate(rows, 1):
        before, after = row["antes"], row["despues"]
        mark = "" if row["hallazgo"] else " · detectada al redactar"
        choice = (
            "razon" in after
            and statement_kind({"contenido": after}) == "otro"
            and normalize(after["respuesta"]) in normalize(after["enunciado"])
        )
        out += [
            "",
            f"## {number}. `{row['item'].split(':', 2)[-1]}`{mark}",
            "",
            f"Qué cambia: {row['cambio']}.",
            "",
            _state(row),
            "",
            "| | Antes | Después |",
            "|---|---|---|",
            *(
                f"| {label} | {_cell(before.get(key, ''))} | {_cell(after[key])} |"
                for key, label in zip(FIELDS, ("Pregunta", "Respuesta", "Razón"), strict=True)
                if key in after
            ),
        ]
        if row.get("duda"):
            out += ["", f"**Para tu criterio:** {row['duda']}."]
        if choice:
            out += ["", "La respuesta nueva figura en el enunciado: confirmar que exige pensarla."]
    return "\n".join(out) + "\n"


def _state(row: dict[str, Any]) -> str:
    if not row.get("aprobacion"):
        return "Estado: sin aprobar."
    applied = f" Aplicada en el commit `{row['aplicada'][:12]}`." if row.get("aplicada") else ""
    return f"Estado: aprobada por {row['aprobacion']['por']}.{applied}"


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
        read_core(folders[0]),
        read_jsonl(folder / "propuestas.jsonl"),
        document["correcciones"],
        read_jsonl(folder / "hallazgos.jsonl"),
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


class Applied(NamedTuple):
    """Lo que cambió al registrar una reexportación."""

    corrections: int
    gone: int  # hallazgos que dejaron de aparecer
    closed: int  # siguen señalados y quedan resueltos con el texto aprobado
    withdrawn: int  # aceptaciones retiradas porque cambió el texto que se aceptó


def mark_applied(nucleo: Path, datasets: Path) -> Applied:
    """Tras volver a exportar, marca como aplicadas las correcciones aprobadas cuyo texto ya está en el núcleo.

    Con cada hallazgo que toca un texto aplicado hace una de tres cosas: si dejó de aparecer, lo archiva con su
    decisión y su juicio de lectura; si sigue, estaba pendiente y todos los textos de su duda están aplicados, lo
    registra como resuelto; si sigue y estaba aceptado, retira la aceptación para que se decida sobre el texto
    nuevo. También retira los juicios sobre textos que ya no existen. Debe ejecutarse antes de `clean-report`,
    que reescribe los hallazgos.
    """
    folder = core_folders(nucleo)[0]
    cleaning = folder / "limpieza"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    commit = manifest["commit_fuente"]
    entities = read_core(folder)
    contents = {e["id"]: e["contenido"] for e in entities if e["entidad"] == "item"}
    document = _load(cleaning / "correcciones.json")
    applied = []
    for row in (r for r in document["correcciones"] if r.get("aprobacion") and not r.get("aplicada")):
        current = contents.get(row["item"])
        if current == row["despues"]:
            applied.append(row)
        elif current != row["antes"]:
            raise SystemExit(f"{row['item']}: el núcleo no tiene ni el texto anterior ni el aprobado")
    if not applied:
        raise SystemExit("ninguna corrección aprobada está en el núcleo")
    ids = {r["item"] for r in applied}
    current_ids = {f["id"] for f in all_findings(entities, dataset_records(datasets, manifest))}
    before = read_jsonl(cleaning / "hallazgos.jsonl")
    gone = [f for f in before if f["id"] not in current_ids]
    unexplained = [f["id"] for f in gone if not ids & set(f["entidades"])]
    if unexplained:
        raise SystemExit("desaparecen hallazgos que ninguna corrección explica: " + ", ".join(unexplained))
    for row in applied:
        row["aplicada"] = commit
    done = {r["item"]: r for r in document["correcciones"] if r.get("aplicada")}
    listed = _load(cleaning / "decisiones.json", {"decisiones": []})["decisiones"]
    decisions = {d["id"]: d for d in listed}
    review = _load(cleaning / "revision.json")
    doubts = {d["hallazgo"]: d for d in _load(cleaning / "dudas.json", {"dudas": []})["dudas"]}

    archived = []
    for f in gone:
        history = {"resuelto_en": commit}
        if f["id"] in decisions:
            history["decision"] = decisions.pop(f["id"])
        if f["id"] in review["hallazgos"]:
            history["juicio"] = review["hallazgos"].pop(f["id"])
        archived.append(f | history)

    withdrawn, closed = [], 0
    for f in (f for f in before if f["id"] in current_ids and ids & set(f["entidades"])):
        ident = f["id"]
        if ident in decisions:
            withdrawn.append(decisions.pop(ident) | {"retirada_en": commit})
            continue
        entry = doubts.get(ident)
        if not entry or entry["recomendacion"] == "mantener":
            continue
        rows = [done.get(i) for i in entry["items"]]
        if not rows or not all(rows):
            continue
        decisions[ident] = {
            "id": ident,
            "estado": "resuelto",
            "motivo": f"textos aprobados y aplicados en el commit {commit[:12]} de la fuente: {entry['motivo']}",
            "aprobado_por": ", ".join(sorted({r["aprobacion"]["por"] for r in rows})),
        }
        review["hallazgos"].pop(ident, None)
        closed += 1

    _append(cleaning / "resueltos.jsonl", archived)
    _append(cleaning / "retiradas.jsonl", withdrawn)
    if listed or decisions:
        ordered = [decisions[k] for k in sorted(decisions)]
        _save(cleaning / "decisiones.json", {"decisiones": ordered}, indent=1)
    _save(cleaning / "correcciones.json", document, indent=1)
    review["items"] = {
        rule: {i: j for i, j in table.items() if i not in ids} for rule, table in review["items"].items()
    }
    _save(cleaning / "revision.json", review, indent=1, sort_keys=True)
    return Applied(len(applied), len(archived), closed, len(withdrawn))


def _load(path: Path, default: Any = None) -> Any:
    if default is not None and not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _append(path: Path, rows: list[dict[str, Any]]) -> None:
    """Añade filas a un archivo histórico, sin reescribir las anteriores."""
    if not rows:
        return
    previous = read_jsonl(path) if path.exists() else []
    path.write_text("".join(dumps(r) + "\n" for r in previous + rows), encoding="utf-8", newline="\n")


def _save(path: Path, document: dict[str, Any], **options: Any) -> None:
    text = json.dumps(document, ensure_ascii=False, **options) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
