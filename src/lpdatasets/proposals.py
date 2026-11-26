"""Línea L02: agrupa los hallazgos de limpieza en lotes con una propuesta, para que una persona decida por lote.

Una propuesta no cambia datos ni decide nada. Combina dos orígenes que quedan declarados: reglas generales sobre
el texto («regla») y juicios de quien leyó los casos, guardados en `limpieza/revision.json` («individual»). Lo que
necesita lectura y no la tiene cae en el lote `sin-revisar`.

`approve` es el único paso que registra decisiones, solo para lotes que proponen aceptar y con el nombre de quien
aprueba.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .build import dumps, read_jsonl
from .cleaning import normalize, report
from .core import Entity
from .core_build import core_folders, read_core

ACCEPT, FIX, ASK = "aceptar", "corregir", "decidir"
# lote: (veredicto, dónde se aplica, por qué, qué se haría)
LOTS: dict[str, tuple[str, str, str, str]] = {
    "duplicado-glosario": (
        ACCEPT,
        "ninguno",
        "la misma palabra con la misma definición en el glosario de varias clases",
        "conservar en el núcleo; el dataset siguiente usa una sola copia",
    ),
    "duplicado-repaso": (
        ACCEPT,
        "ninguno",
        "la misma pregunta se repite en otra clase como repaso",
        "conservar en el núcleo; el dataset siguiente usa una sola copia",
    ),
    "vocabulario-variantes": (
        ACCEPT,
        "ninguno",
        "la misma idea redactada de otra forma según la clase",
        "conservar; toda modalidad entrega la definición con su clase",
    ),
    "vocabulario-acepciones": (
        ACCEPT,
        "ninguno",
        "la palabra tiene sentidos distintos según la clase",
        "conservar; toda modalidad entrega la definición con su clase",
    ),
    "vocabulario-redaccion": (
        ASK,
        "fuente",
        "alguna definición puede ser imprecisa para 6 años",
        "que una persona con criterio pedagógico confirme o reescriba",
    ),
    "conflicto-contexto": (
        ACCEPT,
        "ninguno",
        "respuestas distintas y válidas para la misma pregunta en clases distintas",
        "conservar; toda modalidad entrega la pregunta con su clase",
    ),
    "enunciado-opciones": (
        ACCEPT,
        "ninguno",
        "pregunta de elección, lista o lectura donde la respuesta debe estar en el enunciado",
        "conservar",
    ),
    "enunciado-comprension": (
        ACCEPT,
        "ninguno",
        "copia, comprensión o inferencia sobre un texto dado",
        "conservar",
    ),
    "enunciado-decidir": (
        ASK,
        "fuente",
        "puede ser un apoyo intencional o regalar la respuesta",
        "decidir caso a caso",
    ),
    "enunciado-corregir": (FIX, "fuente", "la pregunta entrega su propia respuesta", "reescribir en la fuente"),
    "cuaderno-propio-enunciado": (
        ACCEPT,
        "ninguno",
        "la respuesta aparece en el cuaderno solo porque está en su propio enunciado",
        "conservar; se juzga en la regla del enunciado",
    ),
    "cuaderno-ensenanza": (
        ACCEPT,
        "ninguno",
        "la respuesta es el contenido que la clase enseña antes de preguntar",
        "conservar",
    ),
    "cuaderno-corregir": (FIX, "fuente", "otro ejercicio o ejemplo entrega la respuesta", "cambiar uno de los dos"),
    "cuaderno-decidir": (ASK, "fuente", "el cuaderno puede adelantar la respuesta", "decidir caso a caso"),
    "texto-oficial-fragmento": (
        ACCEPT,
        "ninguno",
        "fragmento breve de vocabulario o enumeración común, no el objetivo completo",
        "conservar; es una decisión de derechos del titular",
    ),
    "cruces-dataset": (
        FIX,
        "modalidad L08",
        "contenido de evaluación presente en entrenamiento en el dataset v1.0",
        "partir por OA y sacar de evaluación toda entrada presente en entrenamiento",
    ),
    "etiquetas": (FIX, "línea L03", "faltan habilidades o dificultad", "etiquetar con criterio y verificador"),
    "sin-revisar": (ASK, "por definir", "necesita lectura y nadie la ha hecho", "leer antes de proponer"),
}
WORDS = re.compile(r"\w+")
FILLER = r"(?:(?:un|una|el|la|los|las|en|de|con|a|al|por|para|que|se|lo|su|sus) ){0,3}"
WORKED = "**Ejemplos resueltos"
QUOTED = re.compile(r"«([^»]*)»|“([^”]*)”|\"([^\"]*)\"")


def _words(text: str) -> str:
    return f" {' '.join(WORDS.findall(text.lower()))} "


def statement_kind(item: Entity) -> str:
    """Por qué un enunciado contiene su respuesta, según la forma del texto; `otro` exige leerlo."""
    question = item["contenido"]["enunciado"]
    answer = _words(item["contenido"]["respuesta"]).strip()
    flat, target = _words(question), re.escape(answer)
    if re.search(r"(^|\s)A[:)]\s", question) and re.search(r"\sB[:)]\s", question):
        return "alternativas"
    if re.search(rf" {target} (?:\w+ ){{0,3}}[ou] ", flat) or re.search(rf" [ou] {FILLER}(?:\w+ )?{target} ", flat):
        # Si lo afirmado antes de la pregunta ya dice la respuesta, la elección puede estar regalada.
        premise = question[: max(question.rfind("¿"), 0)]
        return "otro" if f" {answer} " in _words(premise) else "eleccion"
    if any(f" {answer} " in _words(part) for groups in QUOTED.findall(question) for part in groups if part):
        return "texto_citado"
    lower = " ".join(question.lower().split())
    if re.search(rf"[:,(]\s*{FILLER}{target}\s*(?:,|\)| y )", lower) or re.search(
        rf",\s*{FILLER}{target}\s*[.?)»]", lower
    ):
        return "lista"
    return "otro"


def _judged(finding: dict[str, Any], review: dict[str, Any]) -> tuple[str, list[str]] | None:
    """Lote que imponen los juicios individuales sobre los ítems, si alguno pide cambiar o decidir."""
    judgements = review["items"].get(finding["regla"], {})
    for verdict in (FIX, ASK):
        ids = [i for i in finding["entidades"] if judgements.get(i, {}).get("veredicto") == verdict]
        if ids:
            return verdict, ids
    return None


def _statement_lot(finding, items, review) -> tuple[str, str, list[str]]:
    judged = _judged(finding, review)
    if judged:
        return ("enunciado-corregir" if judged[0] == FIX else "enunciado-decidir"), "individual", judged[1]
    unread = [i for i in finding["entidades"] if statement_kind(items[i]) == "otro"]
    pending = [i for i in unread if i not in review["items"].get(finding["regla"], {})]
    if pending:
        return "sin-revisar", "regla", pending
    return ("enunciado-comprension", "individual", []) if unread else ("enunciado-opciones", "regla", [])


def _notebook_lot(finding, items, notebooks, review) -> tuple[str, str, list[str]]:
    judged = _judged(finding, review)
    if judged:
        return ("cuaderno-corregir" if judged[0] == FIX else "cuaderno-decidir"), "individual", judged[1]
    taught, unread = False, []
    for ident in finding["entidades"]:
        item = items[ident]
        answer = normalize(item["contenido"]["respuesta"])
        lesson = notebooks.get(item["clase_id"], "").partition("**Ejercicios**")[0]
        explanation, _, examples = lesson.partition(WORKED)
        if answer in normalize(examples):
            unread.append(ident)  # un ejemplo resuelto o un error comentado puede responder esta misma pregunta
        elif answer in normalize(explanation):
            taught = True
        elif answer not in normalize(item["contenido"]["enunciado"]):
            unread.append(ident)
    pending = [i for i in unread if i not in review["items"].get(finding["regla"], {})]
    if pending:
        return "sin-revisar", "regla", pending
    if unread:
        return "cuaderno-ensenanza", "individual", []
    return ("cuaderno-ensenanza" if taught else "cuaderno-propio-enunciado"), "regla", []


def propose(findings: list[dict[str, Any]], entities: list[Entity], review: dict[str, Any]) -> list[dict[str, Any]]:
    """Una propuesta por hallazgo, en el mismo orden."""
    items = {e["id"]: e for e in entities if e["entidad"] == "item"}
    notebooks = {
        e["clase_id"]: e["texto"]
        for e in entities
        if e["entidad"] == "recurso" and e.get("extra", {}).get("rol") == "cuaderno_estudiante"
    }
    known = {f["id"] for f in findings}
    judged_items = {ident for table in review["items"].values() for ident in table}
    stale = sorted(set(review["hallazgos"]) - known) + sorted(judged_items - set(items))
    if stale:
        raise SystemExit("la revisión cita hallazgos o ítems que ya no existen:\n" + "\n".join(stale[:30]))
    result = []
    for f in findings:
        rule, reading, targets, note = f["regla"], "regla", [], None
        judged = review["hallazgos"].get(f["id"])
        if judged:
            lot, reading, note = judged["lote"], "individual", judged.get("motivo")
        elif rule == "solucion_en_enunciado":
            lot, reading, targets = _statement_lot(f, items, review)
        elif rule == "solucion_en_cuaderno":
            lot, reading, targets = _notebook_lot(f, items, notebooks, review)
        elif rule == "duplicado_exacto" and all(items[i]["tipo"] == "vocabulario" for i in f["entidades"]):
            lot = "duplicado-glosario"
        elif rule in ("cruce_identico", "cruce_por_entrada"):
            lot = "cruces-dataset"
        elif rule in ("sin_habilidades", "sin_dificultad"):
            lot = "etiquetas"
        else:
            lot = "sin-revisar"
        if lot not in LOTS:
            raise SystemExit(f"{f['id']}: lote desconocido {lot!r}")
        judgements = review["items"].get(rule, {})
        notes = [judgements[i]["motivo"] for i in targets if judgements.get(i, {}).get("motivo")]
        result.append(
            {
                "id": f["id"],
                "regla": rule,
                "lote": lot,
                "veredicto": LOTS[lot][0],
                "lectura": reading,
                "motivo": note or "; ".join(sorted(set(notes))) or LOTS[lot][2],
                "items_a_cambiar": targets,
                "total": f["total"],
                "estado": f["estado"],
            }
        )
    return result


def render(proposals: list[dict[str, Any]], entities: list[Entity], review: dict[str, Any]) -> str:
    items = {e["id"]: e for e in entities if e["entidad"] == "item"}
    lots = {lot: [p for p in proposals if p["lote"] == lot] for lot in LOTS}
    lots = {lot: group for lot, group in lots.items() if group}
    out = [
        "# Propuestas de limpieza · 1.º básico",
        "",
        "Generado con `lpdatasets clean-proposals`; no se edita a mano. **Nada está decidido hasta que una persona "
        "lo apruebe.**",
        "",
        f"Primera lectura: {review['revisor']} ({review['fecha']}).",
        "",
        "| Veredicto propuesto | Lotes | Hallazgos | Pendientes |",
        "|---|---:|---:|---:|",
    ]
    for verdict in (ACCEPT, FIX, ASK):
        group = [p for p in proposals if p["veredicto"] == verdict]
        pending = sum(p["estado"] == "pendiente" for p in group)
        out.append(f"| {verdict} | {len({p['lote'] for p in group})} | {len(group)} | {pending} |")
    out += [
        "",
        "## Lotes",
        "",
        "| Lote | Veredicto | Hallazgos | Afectados | Cómo se clasificó | Pendientes |",
        "|---|---|---:|---:|---|---:|",
    ]
    for lot, group in lots.items():
        how = " y ".join(sorted({"leído" if p["lectura"] == "individual" else "por regla" for p in group}))
        pending = sum(p["estado"] == "pendiente" for p in group)
        out.append(
            f"| `{lot}` | {LOTS[lot][0]} | {len(group)} | {sum(p['total'] for p in group)} | {how} | {pending} |"
        )
    second = review.get("segunda_lectura")
    if second:
        out += ["", "## Segunda lectura", "", *second["resumen"]]
    out += [
        "",
        "## Cómo aprobar",
        "",
        "Solo se aprueban lotes con veredicto `aceptar`; queda registrado quién aprobó:",
        "",
        "```bash",
        'lpdatasets clean-approve --lote duplicado-glosario --aprobado-por "nombre"',
        "```",
        "",
        "Los lotes `corregir` y `decidir` siguen pendientes hasta que el cambio esté aplicado y comprobado.",
    ]
    for lot, group in lots.items():
        verdict, where, why, change = LOTS[lot]
        out += ["", f"## `{lot}`", "", f"**{verdict}** · {why}. Propuesta: {change}. Se aplica en: {where}."]
        targets = [(p, i) for p in group for i in p["items_a_cambiar"]]
        if targets:
            out += ["", "| Ítem | Enunciado | Respuesta | Motivo |", "|---|---|---|---|"]
            for p, ident in targets:
                content = items[ident]["contenido"]
                reason = review["items"].get(p["regla"], {}).get(ident, {}).get("motivo", p["motivo"])
                cells = [content["enunciado"], content.get("respuesta", ""), reason]
                out.append(f"| `{ident.split(':', 2)[-1]}` | " + " | ".join(_cell(c) for c in cells) + " |")
        elif verdict != ACCEPT and lot not in ("cruces-dataset", "etiquetas"):
            out += [""] + [f"- `{p['id']}`: {_cell(p['motivo'])}" for p in group]
        else:
            out += ["", "Ejemplos: " + ", ".join(f"`{p['id']}`" for p in group[:3]) + "."]
    return "\n".join(out) + "\n"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "/").replace("[", "(").replace("]", ")")


def _folder(nucleo: Path) -> Path:
    folders = core_folders(nucleo)
    if len(folders) != 1:
        raise SystemExit(f"se esperaba un solo núcleo en {nucleo} y hay {len(folders)}")
    return folders[0]


def proposals_report(nucleo: Path, doc: Path, check: bool = False) -> list[str]:
    """Escribe las propuestas y su informe; con `check` no escribe y devuelve lo que esté desactualizado."""
    folder = _folder(nucleo)
    review = json.loads((folder / "limpieza" / "revision.json").read_text(encoding="utf-8"))
    entities = read_core(folder)
    proposals = propose(read_jsonl(folder / "limpieza" / "hallazgos.jsonl"), entities, review)
    outputs = {
        folder / "limpieza" / "propuestas.jsonl": "".join(dumps(p) + "\n" for p in proposals),
        doc: render(proposals, entities, review),
    }
    stale = []
    for path, text in outputs.items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(f"{path}: desactualizado (ejecuta lpdatasets clean-proposals)")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    return stale


def approve(nucleo: Path, datasets: Path, lots: list[str], approver: str, clean_doc: Path, doc: Path) -> int:
    """Registra como aceptados los hallazgos de los lotes indicados y regenera ambos informes."""
    if not approver.strip():
        raise SystemExit("falta el nombre de quien aprueba")
    refused = [lot for lot in lots if lot not in LOTS or LOTS[lot][0] != ACCEPT]
    if refused or not lots:
        raise SystemExit(f"solo se aprueban lotes que proponen aceptar; no válidos: {', '.join(refused) or 'ninguno'}")
    stale = proposals_report(nucleo, doc, check=True)
    if stale:
        raise SystemExit("\n".join(stale))
    folder = _folder(nucleo)
    chosen = [p for p in read_jsonl(folder / "limpieza" / "propuestas.jsonl") if p["lote"] in lots]
    path = folder / "limpieza" / "decisiones.json"
    previous = json.loads(path.read_text(encoding="utf-8"))["decisiones"] if path.exists() else []
    decided = {d["id"]: d for d in previous}
    new = [p for p in chosen if p["id"] not in decided]
    for p in new:
        motive = f"lote {p['lote']}: {p['motivo']}"
        decided[p["id"]] = {"id": p["id"], "estado": "aceptado", "motivo": motive, "aprobado_por": approver.strip()}
    path.write_text(
        json.dumps({"decisiones": [decided[k] for k in sorted(decided)]}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report(nucleo, datasets, clean_doc)
    proposals_report(nucleo, doc)
    return len(new)
