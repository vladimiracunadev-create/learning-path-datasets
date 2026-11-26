"""Línea L02: encuentra problemas en el núcleo y en el dataset v1.0 y propone qué hacer. Nunca modifica los datos.

Cada hallazgo tiene un identificador estable, así una decisión humana (`decisiones.json`) queda asociada a él; si
las entidades afectadas cambian, el identificador cambia y la decisión antigua se rechaza.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .build import dumps, manifests, read_jsonl
from .contributions import combined
from .core import Entity
from .core_build import core_folders

HIDDEN_TYPES = ("ejercicio_cerrado", "autoevaluacion", "actividad_abierta")
TASK_TYPES = (*HIDDEN_TYPES, "ejemplo_resuelto")
# A qué piezas corresponde cada etiqueta. En las demás, su falta se informa aparte para que una persona la acepte.
# Habilidades: lo que un estudiante hace. Dificultad: lo que la fuente gradúa de 1 a 5.
APPLIES = {"habilidades": TASK_TYPES, "dificultad": ("ejercicio_cerrado",)}
DECIDED = ("aceptado", "resuelto")
SAMPLE = 20  # identificadores que guarda un hallazgo agregado
NEEDS_MEDIA = re.compile(
    r"\b(observa|mira|escucha|revisa)\b[^.?!]{0,40}\b(imagen|foto|fotografía|lámina|ilustración|video|audio|grabación)",
    re.I,
)
WORDS = re.compile(r"\w+")
# regla: (severidad, qué detecta, qué se propone, agregado)
RULES: dict[str, tuple[str, str, str, bool]] = {
    "clase_incompleta": (
        "error",
        "clase sin guía, o clase desarrollada sin cuaderno o sin ítems",
        "revisar la exportación y la fuente",
        False,
    ),
    "cruce_identico": (
        "error",
        "registros de evaluación del dataset v1.0 idénticos a uno de entrenamiento",
        "sacarlos de evaluación al construir la siguiente versión del dataset",
        False,
    ),
    "cruce_por_entrada": (
        "revisar",
        "registros de evaluación del dataset v1.0 cuya entrada está en entrenamiento",
        "partir por OA en la siguiente versión y revisar los que persistan",
        False,
    ),
    "duplicado_exacto": (
        "revisar",
        "ítems de una asignatura con el mismo enunciado y la misma respuesta",
        "conservar uno en las modalidades donde repetir no aporte",
        False,
    ),
    "respuestas_en_conflicto": (
        "revisar",
        "mismo enunciado, asignatura y tipo con respuestas distintas",
        "decidir si falta contexto en el enunciado o si ambas respuestas son válidas",
        False,
    ),
    "recurso_ausente": (
        "revisar",
        "consigna que pide ver o escuchar algo que no está como recurso",
        "crear el recurso (línea L03) o reescribir la consigna",
        False,
    ),
    "solucion_en_enunciado": (
        "revisar",
        "ejercicio con solución oculta cuyo enunciado contiene la respuesta",
        "confirmar si es una pregunta de elección legítima o reescribirla",
        False,
    ),
    "solucion_en_cuaderno": (
        "revisar",
        "respuesta larga de un ejercicio que aparece literal en el cuaderno de su clase",
        "confirmar si es parte de la explicación o si regala la respuesta",
        False,
    ),
    "texto_oficial": (
        "revisar",
        "tramo de ocho o más palabras que coincide con la redacción oficial de un OA",
        "confirmar si es vocabulario común o reescribirlo citando el código",
        False,
    ),
    "sin_habilidades": ("info", "ítems sin habilidades etiquetadas", "etiquetar desde OA e indicadores (L03)", True),
    "sin_dificultad": ("info", "ítems sin dificultad", "etiquetar con un criterio declarado", True),
}


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _words(text: str) -> str:
    return f" {' '.join(WORDS.findall(text.lower()))} "


def finding(rule: str, scope: str, ids: Iterable[str], evidence: str) -> dict[str, Any]:
    severity, _, action, aggregated = RULES[rule]
    ordered = sorted(set(ids))
    digest = hashlib.sha256("|".join(ordered).encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"{rule}:{digest}",
        "regla": rule,
        "severidad": severity,
        "ambito": scope,
        "total": len(ordered),
        "entidades": ordered[:SAMPLE] if aggregated else ordered,
        "evidencia": " ".join(evidence.split())[:300],
        "accion_propuesta": action,
        "estado": "pendiente",
        "aprobado_por": None,
        "motivo": None,
    }


def core_findings(entities: list[Entity]) -> list[dict[str, Any]]:
    items = [e for e in entities if e["entidad"] == "item"]
    resources = [e for e in entities if e["entidad"] == "recurso"]
    found: list[dict[str, Any]] = []

    roles: dict[str, dict[str, str]] = defaultdict(dict)
    for r in resources:
        if r.get("clase_id"):
            roles[r["clase_id"]][r.get("extra", {}).get("rol", "")] = r.get("texto", "")
    with_items = {i["clase_id"] for i in items if i.get("clase_id")}
    for c in (e for e in entities if e["entidad"] == "clase"):
        missing = [] if "guia_docente" in roles[c["id"]] else ["guía docente"]
        if c["estado_editorial"] == "desarrollada":
            missing += [] if "cuaderno_estudiante" in roles[c["id"]] else ["cuaderno"]
            missing += [] if c["id"] in with_items else ["ítems"]
        if missing:
            found.append(finding("clase_incompleta", "nucleo", [c["id"]], f"falta: {', '.join(missing)}"))

    same: dict[tuple[str, ...], list[str]] = defaultdict(list)
    questions: dict[tuple[str, ...], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    media: dict[str, list[Entity]] = defaultdict(list)
    given: dict[str, list[Entity]] = defaultdict(list)
    revealed: dict[str, list[Entity]] = defaultdict(list)
    no_skills: dict[tuple[str, bool], list[str]] = defaultdict(list)
    no_level: dict[str, list[str]] = defaultdict(list)
    for i in items:
        question, answer = i["contenido"]["enunciado"], i["contenido"].get("respuesta", "")
        same[(i["asignatura"], normalize(question), normalize(answer))].append(i["id"])
        questions[(i["asignatura"], i["tipo"], normalize(question))][normalize(answer)].append(i["id"])
        group = i.get("clase_id") or i["asignatura"]
        if i["tipo"] in TASK_TYPES and NEEDS_MEDIA.search(question):
            media[group].append(i)
        if "estudiante" not in i["publico_solucion"]:
            if len(answer) >= 4 and _words(answer) in _words(question):
                given[group].append(i)
            notebook = roles.get(i.get("clase_id") or "", {}).get("cuaderno_estudiante", "")
            if len(answer) >= 30 and normalize(answer) in normalize(notebook):
                revealed[group].append(i)
        if not i.get("habilidades"):
            no_skills[(i["asignatura"], i["tipo"] in APPLIES["habilidades"])].append(i["id"])
        if i.get("dificultad") is None:
            no_level[i["tipo"]].append(i["id"])

    for (subject, question, answer), ids in same.items():
        if len(ids) > 1:
            found.append(finding("duplicado_exacto", "nucleo", ids, f"{subject}: «{question}» → «{answer}»"))
    for (subject, _, question), answers in questions.items():
        if len(answers) > 1:
            ids = [x for group_ids in answers.values() for x in group_ids]
            evidence = f"{subject}: «{question}» → " + " / ".join(f"«{a}»" for a in sorted(answers))
            found.append(finding("respuestas_en_conflicto", "nucleo", ids, evidence))
    for rule, groups, field in (
        ("recurso_ausente", media, "enunciado"),
        ("solucion_en_enunciado", given, "enunciado"),
        ("solucion_en_cuaderno", revealed, "respuesta"),
    ):
        for group, members in groups.items():
            evidence = f"{group}: «{members[0]['contenido'][field]}»"
            found.append(finding(rule, "nucleo", [m["id"] for m in members], evidence))
    for e in entities:
        code = e.get("extra", {}).get("coincide_texto_oficial")
        if code:
            found.append(finding("texto_oficial", "nucleo", [e["id"]], f"coincide con la redacción de {code}"))
    for (subject, is_task), ids in no_skills.items():
        what = "ítems de tarea" if is_task else "ítems que no son tareas"
        found.append(finding("sin_habilidades", "nucleo", ids, f"{subject}: {len(ids)} {what}"))
    for name, ids in no_level.items():
        found.append(finding("sin_dificultad", "nucleo", ids, f"{name}: {len(ids)} ítems"))
    return found


def dataset_findings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cruces entre entrenamiento y evaluación del dataset de pares, agrupados por asignatura."""
    train = [r for r in records if r["particion"] == "train"]
    pairs = {(normalize(r["entrada"]), normalize(r["salida"])) for r in train}
    inputs = {normalize(r["entrada"]) for r in train}
    exact: dict[str, list[str]] = defaultdict(list)
    shared: dict[str, list[str]] = defaultdict(list)
    for r in (r for r in records if r["particion"] == "eval"):
        if (normalize(r["entrada"]), normalize(r["salida"])) in pairs:
            exact[r["asignatura"]].append(r["id"])
        if normalize(r["entrada"]) in inputs:
            shared[r["asignatura"]].append(r["id"])
    return [
        finding(rule, "dataset-v1", ids, f"{subject}: {len(ids)} registros de evaluación")
        for rule, groups in (("cruce_identico", exact), ("cruce_por_entrada", shared))
        for subject, ids in groups.items()
    ]


def apply_decisions(findings: list[dict[str, Any]], path: Path) -> list[dict[str, Any]]:
    """Anota las decisiones humanas registradas; falla si una está incompleta o ya no corresponde a un hallazgo."""
    if not path.exists():
        return findings
    by_id = {f["id"]: f for f in findings}
    problems = []
    for d in json.loads(path.read_text(encoding="utf-8"))["decisiones"]:
        target = by_id.get(d.get("id"))
        if target is None:
            problems.append(f"{d.get('id')}: no corresponde a ningún hallazgo actual")
        elif d.get("estado") not in DECIDED or not d.get("motivo") or not d.get("aprobado_por"):
            problems.append(f"{d['id']}: necesita estado ({' o '.join(DECIDED)}), motivo y aprobado_por")
        else:
            target.update(estado=d["estado"], motivo=d["motivo"], aprobado_por=d["aprobado_por"])
    if problems:
        raise SystemExit("decisiones de limpieza inválidas:\n" + "\n".join(problems))
    return findings


def dataset_records(datasets: Path, core_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Registros del dataset de pares que corresponde al mismo programa y nivel del núcleo."""
    return [
        r
        for m in manifests(datasets)
        if m.parent.parent.name == core_manifest["pack"] and m.parent.name == core_manifest["nivel"]
        for name in json.loads(m.read_text(encoding="utf-8"))["archivos"]
        for r in read_jsonl(m.parent / name)
    ]


def all_findings(entities: list[Entity], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(core_findings(entities) + dataset_findings(records), key=lambda f: f["id"])


def render(
    findings: list[dict[str, Any]],
    core_manifest: dict[str, Any],
    items: int,
    records: int,
    resolved: list[dict[str, Any]] | None = None,
) -> str:
    out = [
        f"# Informe de limpieza · {core_manifest['pack']} · {core_manifest['nivel']}",
        "",
        "Generado con `lpdatasets clean-report`; no se edita a mano. Propone cambios y **no modifica los datos**.",
        "",
        f"- Núcleo: {core_manifest['total']} entidades, {items} ítems, commit de la fuente "
        f"`{core_manifest['commit_fuente'][:12]}`.",
        f"- Dataset v1.0 revisado como línea base: {records} registros.",
        f"- Hallazgos: {len(findings)}; pendientes: {sum(f['estado'] == 'pendiente' for f in findings)}.",
        "",
        "| Regla | Severidad | Hallazgos | Afectados | Pendientes |",
        "|---|---|---:|---:|---:|",
    ]
    grouped = {rule: [f for f in findings if f["regla"] == rule] for rule in RULES}
    for rule, group in grouped.items():
        affected = sum(f["total"] for f in group)
        pending = sum(f["estado"] == "pendiente" for f in group)
        out.append(f"| `{rule}` | {RULES[rule][0]} | {len(group)} | {affected} | {pending} |")
    out += [
        "",
        "«Afectados» cuenta entidades o registros dentro de cada regla; una misma entidad puede aparecer en varias.",
        "Las reglas son comprobaciones de forma: un hallazgo «revisar» puede ser legítimo.",
    ]
    closed = sum(f["estado"] == "resuelto" for f in findings)
    if closed:
        out += ["", f"Resueltos con textos aprobados que la regla sigue señalando: {closed}."]
    if resolved:
        out += [
            "",
            "## Resueltos",
            "",
            "Hallazgos que dejaron de aparecer al aplicar correcciones en la fuente o aportes. Se conservan en "
            "`limpieza/resueltos.jsonl`.",
            "",
            "| Resuelto en | Regla | Hallazgos | Afectados |",
            "|---|---|---:|---:|",
        ]
        for commit, rule in sorted({(f["resuelto_en"], f["regla"]) for f in resolved}):
            group = [f for f in resolved if (f["resuelto_en"], f["regla"]) == (commit, rule)]
            origin = commit if commit == "aportes" else commit[:12]
            affected = sum(f["total"] for f in group)
            out.append(f"| `{origin}` | `{rule}` | {len(group)} | {affected} |")
    for rule, group in grouped.items():
        _, what, action, _ = RULES[rule]
        out += ["", f"## `{rule}`", "", f"Detecta: {what}. Propuesta: {action}.", ""]
        if not group:
            out.append("Sin hallazgos.")
        for f in sorted(group, key=lambda f: (-f["total"], f["id"]))[:3]:
            out.append(f"- `{f['id']}` ({f['total']}): {f['evidencia'].replace('[', '(').replace(']', ')')}")
    return "\n".join(out) + "\n"


def report(nucleo: Path, datasets: Path, doc: Path, check: bool = False) -> list[str]:
    """Escribe los hallazgos y el informe; con `check` no escribe y devuelve lo que esté desactualizado."""
    folders = core_folders(nucleo)
    if len(folders) != 1:
        raise SystemExit(f"se esperaba un solo núcleo en {nucleo} y hay {len(folders)}")
    folder = folders[0]
    entities = combined(nucleo)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    records = dataset_records(datasets, manifest)
    findings = all_findings(entities, records)
    apply_decisions(findings, folder / "limpieza" / "decisiones.json")
    items = sum(e["entidad"] == "item" for e in entities)
    archive = folder / "limpieza" / "resueltos.jsonl"
    resolved = read_jsonl(archive) if archive.exists() else []
    outputs = {
        folder / "limpieza" / "hallazgos.jsonl": "".join(dumps(f) + "\n" for f in findings),
        doc: render(findings, manifest, items, len(records), resolved),
    }
    stale = []
    for path, text in outputs.items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(f"{path}: desactualizado (ejecuta lpdatasets clean-report)")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    return stale
