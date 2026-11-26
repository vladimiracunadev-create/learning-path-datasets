"""Línea L03: aportes, es decir, etiquetas y contenido nuevo que se suman al núcleo sin tocar lo que vino de la fuente.

Cada pieza vive en `aportes/<pack>/<nivel>/*.jsonl` con autor, fuentes, derechos y verificación. El núcleo publicado
no se modifica: `compose` combina núcleo y piezas aprobadas en una copia, siempre igual para las mismas entradas.

Una pieza entra solo si otra identidad la verificó y una persona la aprobó, ambas sobre el texto actual de la pieza
y de aquello a lo que se refiere. Si cualquiera de los dos cambia, la pieza queda `caducada` y deja de entrar.

Dos tipos de pieza:

- `entidad`: un ítem o un recurso nuevo, ligado a una clase del núcleo.
- `etiqueta`: llena `habilidades` o `dificultad` en un ítem, o en los ítems de una clase, solo donde la fuente los
  dejó vacíos.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from collections import Counter
from collections.abc import Collection
from datetime import date
from pathlib import Path
from typing import Any

from .build import MANIFEST, dumps, read_jsonl, sha256_file
from .core import CONTRACT, LICENSE_USES, USES, Entity, allows_use, validate_entity
from .core_build import core_folders, read_core, write_core

REPO = "vladimiracunadev-create/learning-path-datasets"
KINDS = ("entidad", "etiqueta")
AUTHORS = ("ia", "persona")
SOURCE_USES = ("derivado", "consulta")  # «derivado» obliga a respetar su licencia; «consulta» solo toma hechos
VERDICTS = ("aprobado", "observado")
LABELS = ("habilidades", "dificultad")
STATES = ("aprobada", "verificada", "observada", "caducada", "borrador")
NEW_FIELDS = {
    "item": ("tipo", "publico", "publico_solucion", "contenido", "habilidades", "dificultad", "idioma", "extra"),
    "recurso": ("medio", "publico", "texto", "uri", "sha256", "descripcion", "idioma", "extra"),
}
RECORDS = ("verificacion", "aprobacion")  # lo que se añade a una pieza y no cambia su contenido

Piece = dict[str, Any]


def _hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fingerprint(piece: Piece) -> str:
    """Huella de lo que la pieza dice; cambia si cambia cualquier cosa salvo su verificación y aprobación."""
    return _hash({k: v for k, v in piece.items() if k not in RECORDS})


def targets(entities: list[Entity], piece: Piece) -> list[Entity]:
    """Entidades de la fuente a las que se refiere una pieza, ordenadas."""
    if piece.get("tipo") == "etiqueta" and "item" in piece:
        found = [e for e in entities if e["entidad"] == "item" and e["id"] == piece["item"]]
    elif piece.get("tipo") == "etiqueta":
        types = piece.get("tipos")
        found = [
            e
            for e in entities
            if e["entidad"] == "item" and e.get("clase_id") == piece.get("clase") and (not types or e["tipo"] in types)
        ]
    else:
        owner = (piece.get("pieza") or {}).get("clase_id")
        found = [e for e in entities if owner and owner in (e["id"], e.get("clase_id"))]
    return sorted(found, key=lambda e: e["id"])


def about(entities: list[Entity], piece: Piece) -> str:
    """Huella del texto de la fuente al que se refiere la pieza: si cambia, hay que volver a verificar."""
    return _hash([[e["id"], e.get("contenido"), e.get("texto"), e.get("titulo")] for e in targets(entities, piece)])


def read_pieces(folder: Path) -> dict[Path, list[Piece]]:
    return {path: read_jsonl(path) for path in sorted(folder.glob("*.jsonl"))} if folder.exists() else {}


def vocabulary(folder: Path) -> dict[str, dict[str, list[str]]]:
    path = folder / "vocabulario.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def check_pieces(entities: list[Entity], pieces: list[Piece], folder: Path, prefix: str) -> list[str]:
    """Problemas de forma, derechos y coherencia; una pieza sin verificar no es un problema, solo no entra."""
    by_id = {e["id"]: e for e in entities}
    words = vocabulary(folder).get("habilidades", {})
    problems = [f"{i}: identificador repetido" for i, n in Counter(p.get("id") for p in pieces).items() if n > 1]
    filled: dict[tuple[str, str], str] = {}
    for piece in pieces:
        found = _check_common(piece, prefix)
        if not found:
            kind = _check_label if piece["tipo"] == "etiqueta" else _check_entity
            found = kind(entities, by_id, piece, folder, words)
        if not found:
            found = _check_records(piece)
        if not found and piece["tipo"] == "etiqueta" and _verdict(piece) != "observado":
            for item in targets(entities, piece):
                slot = (item["id"], piece["campo"])
                if slot in filled:
                    found.append(f"{item['id']}: «{piece['campo']}» ya lo llena {filled[slot]}")
                    break
                filled[slot] = piece["id"]
        problems += [f"{piece.get('id', '?')}: {p}" for p in found]
    return problems


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_common(piece: Piece, prefix: str) -> list[str]:
    problems = []
    if not str(piece.get("id", "")).startswith(prefix):
        problems.append(f"el identificador debe empezar por {prefix}")
    if piece.get("tipo") not in KINDS:
        problems.append(f"«tipo» debe ser {' o '.join(KINDS)}")
    author = piece.get("autor") or {}
    if not _text(author.get("nombre")) or author.get("tipo") not in AUTHORS:
        problems.append(f"«autor» necesita nombre y tipo ({' o '.join(AUTHORS)})")
    rights = piece.get("derechos") or {}
    if not _text(rights.get("licencia")) or not _text(rights.get("titular")) or rights.get("origen") is None:
        problems.append("«derechos» necesita licencia, titular y origen")
    elif not any(allows_use(rights, use) for use in USES):
        problems.append("su licencia u origen no permite ningún uso")
    sources = piece.get("fuentes")
    if not isinstance(sources, list) or not sources:
        return [*problems, "necesita al menos una fuente"]
    for source in sources:
        if not _text(source.get("ref")) or source.get("uso") not in SOURCE_USES:
            problems.append(f"cada fuente necesita «ref» y «uso» ({' o '.join(SOURCE_USES)})")
        elif source["uso"] == "derivado":
            allowed = LICENSE_USES.get(source.get("licencia", ""), ())
            extra = [u for u in USES if not problems and allows_use(rights, u) and u not in allowed]
            if not allowed:
                problems.append(f"{source['ref']}: derivar necesita una licencia conocida")
            elif extra:
                problems.append(f"{source['ref']}: la pieza permite «{', '.join(extra)}» y esa fuente no")
    return problems


def _check_label(
    entities: list[Entity], by_id: dict[str, Entity], piece: Piece, folder: Path, words: dict[str, list[str]]
) -> list[str]:
    if ("item" in piece) == ("clase" in piece):
        return ["una etiqueta se refiere a un «item» o a una «clase», solo uno"]
    field, value = piece.get("campo"), piece.get("valor")
    if field not in LABELS:
        return [f"«campo» debe ser {' o '.join(LABELS)}"]
    found = targets(entities, piece)
    if not found:
        return ["no corresponde a ningún ítem del núcleo"]
    if any(item.get(field) not in (None, []) for item in found):
        return [f"la fuente ya llenó «{field}» en alguno de sus ítems; un aporte no lo sobrescribe"]
    if field == "dificultad":
        valid = isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 5
        return [] if valid else ["la dificultad es un entero de 1 a 5"]
    allowed = {code for item in found for code in words.get(item["asignatura"], [])}
    if not isinstance(value, list) or not value or any(v not in allowed for v in value):
        return ["las habilidades deben salir del vocabulario registrado para la asignatura"]
    if len({item["asignatura"] for item in found}) > 1:
        return ["una etiqueta no mezcla asignaturas"]
    return []


def _check_entity(
    entities: list[Entity], by_id: dict[str, Entity], piece: Piece, folder: Path, words: dict[str, list[str]]
) -> list[str]:
    body = piece.get("pieza") or {}
    kind = body.get("entidad")
    if kind not in NEW_FIELDS:
        return ["«pieza.entidad» debe ser item o recurso"]
    owner = by_id.get(body.get("clase_id", ""))
    if owner is None or owner["entidad"] != "clase":
        return ["«pieza.clase_id» debe ser una clase del núcleo"]
    unknown = set(body) - {"entidad", "clase_id", *NEW_FIELDS[kind]}
    if unknown:
        return [f"campos que la pieza no puede fijar: {', '.join(sorted(unknown))}"]
    if piece["id"] in by_id:
        return ["su identificador ya existe en el núcleo"]
    problems = validate_entity(build_entity(owner, piece, ""))
    if not problems and "uri" in body:
        path = (folder / body["uri"]).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file():
            problems = ["«uri» debe ser un archivo guardado dentro de la carpeta de aportes"]
        elif sha256_file(path) != body["sha256"]:
            problems = ["el archivo no coincide con su sha256"]
    return problems


def _check_records(piece: Piece) -> list[str]:
    problems = []
    check = piece.get("verificacion")
    approval = piece.get("aprobacion")
    if check is not None:
        who = str(check.get("por", "")).strip()
        if not who or check.get("tipo") not in AUTHORS or check.get("veredicto") not in VERDICTS:
            problems.append("la verificación necesita quién, tipo y veredicto")
        elif who.casefold() == piece["autor"]["nombre"].strip().casefold():
            problems.append("quien verifica no puede ser quien escribió")
        elif not _text(check.get("nota")):
            problems.append("la verificación debe decir qué comprobó")
    if approval is not None:
        if check is None or check.get("veredicto") != "aprobado":
            problems.append("solo se aprueba una pieza con verificación favorable")
        elif not _text(approval.get("por")):
            problems.append("la aprobación no dice quién aprueba")
    return problems


def _verdict(piece: Piece) -> str | None:
    return (piece.get("verificacion") or {}).get("veredicto")


def state(entities: list[Entity], piece: Piece) -> str:
    check = piece.get("verificacion")
    if check is None:
        return "borrador"
    current = (fingerprint(piece), about(entities, piece))
    if (check.get("huella"), check.get("sobre")) != current:
        return "caducada"
    if check["veredicto"] == "observado":
        return "observada"
    approval = piece.get("aprobacion")
    if approval is None:
        return "verificada"
    return "aprobada" if (approval.get("huella"), approval.get("sobre")) == current else "caducada"


def build_entity(owner: Entity, piece: Piece, path: str) -> Entity:
    """La entidad nueva tal como entra en el núcleo compuesto."""
    body = copy.deepcopy(piece["pieza"])
    human = (piece.get("verificacion") or {}).get("tipo") == "persona"
    entity = {
        "contrato": CONTRACT,
        "id": piece["id"],
        "nivel": owner["nivel"],
        "marco": owner["marco"],
        "derechos": piece["derechos"],
        "revision": "revision_humana_parcial" if human else "ia_asistida_sin_revision_humana",
        "procedencia": {"repo": REPO, "commit": f"huella:{fingerprint(piece)}", "ruta": path or "aportes"},
    } | body
    if entity["entidad"] == "item":
        entity["asignatura"] = owner["asignatura"]
    return entity


def compose(entities: list[Entity], files: dict[Path, list[Piece]], relative: str = "aportes") -> list[Entity]:
    """Copia del núcleo con las piezas aprobadas; sin ninguna, es igual al original."""
    result = {e["id"]: copy.deepcopy(e) for e in entities}
    approved = [(path, p) for path, rows in files.items() for p in rows if state(entities, p) == "aprobada"]
    for path, piece in sorted(approved, key=lambda x: x[1]["id"]):
        if piece["tipo"] == "entidad":
            owner = result[piece["pieza"]["clase_id"]]
            result[piece["id"]] = build_entity(owner, piece, f"{relative}/{path.name}")
            continue
        for target in targets(entities, piece):
            item = result[target["id"]]
            item[piece["campo"]] = copy.deepcopy(piece["valor"])
            item.setdefault("extra", {}).setdefault("aportes", []).append(piece["id"])
    return sorted(result.values(), key=lambda e: e["id"])


def _locate(nucleo: Path, root: Path) -> tuple[Path, list[Entity], dict[str, Any], Path, str]:
    folders = core_folders(nucleo)
    if len(folders) != 1:
        raise SystemExit(f"se esperaba un solo núcleo en {nucleo} y hay {len(folders)}")
    manifest = json.loads((folders[0] / MANIFEST).read_text(encoding="utf-8"))
    folder = root / manifest["pack"] / manifest["nivel"]
    prefix = f"aporte:{manifest['pack']}:{manifest['nivel']}:"
    return folders[0], read_core(folders[0]), manifest, folder, prefix


def _checked(nucleo: Path, root: Path) -> tuple[list[Entity], dict[str, Any], Path, dict[Path, list[Piece]]]:
    _, entities, manifest, folder, prefix = _locate(nucleo, root)
    files = read_pieces(folder)
    problems = check_pieces(entities, [p for rows in files.values() for p in rows], folder, prefix)
    if problems:
        raise SystemExit("aportes inválidos:\n" + "\n".join(problems[:30]))
    return entities, manifest, folder, files


def export(nucleo: Path, root: Path, out: Path) -> int:
    """Escribe en `out` el núcleo combinado con las piezas aprobadas y devuelve cuántas entraron."""
    entities, manifest, folder, files = _checked(nucleo, root)
    used = [p for rows in files.values() for p in rows if state(entities, p) == "aprobada"]
    info = {k: v for k, v in manifest.items() if k != "aportes"}
    if used:
        info["aportes"] = {"piezas": len(used), "huella": _hash(sorted([p["id"], fingerprint(p)] for p in used))}
    target = out / manifest["pack"] / manifest["nivel"]
    if target.resolve() == core_folders(nucleo)[0].resolve():
        raise SystemExit("la salida no puede ser el núcleo publicado")
    write_core(target, compose(entities, files, f"aportes/{manifest['pack']}/{manifest['nivel']}"), info)
    for piece in used:
        uri = (piece.get("pieza") or {}).get("uri")
        if uri:
            (target / uri).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / uri, target / uri)
    return len(used)


def render(entities: list[Entity], files: dict[Path, list[Piece]]) -> str:
    rows = [(path, p, state(entities, p)) for path, group in files.items() for p in group]
    out = [
        "# Aportes · 1.º básico",
        "",
        "Generado con `lpdatasets contrib-report`; no se edita a mano. Solo las piezas **aprobadas** entran en el "
        "núcleo compuesto; el núcleo publicado no cambia.",
        "",
        f"- Piezas: {len(rows)}.",
        "",
        "| Estado | Entidades nuevas | Etiquetas |",
        "|---|---:|---:|",
        *(
            f"| {name} | {sum(s == name and p['tipo'] == 'entidad' for _, p, s in rows)} | "
            f"{sum(s == name and p['tipo'] == 'etiqueta' for _, p, s in rows)} |"
            for name in STATES
        ),
    ]
    if rows:
        out += ["", "## Piezas", "", "| Pieza | Archivo | Qué es | Autor | Verificó | Aprobó | Estado |"]
        out += ["|---|---|---|---|---|---|---|"]
        for path, piece, name in sorted(rows, key=lambda r: r[1]["id"]):
            what = piece["pieza"]["entidad"] if piece["tipo"] == "entidad" else f"etiqueta de {piece['campo']}"
            check = (piece.get("verificacion") or {}).get("por", "—")
            approval = (piece.get("aprobacion") or {}).get("por", "—")
            cells = [f"`{piece['id']}`", path.name, what, piece["autor"]["nombre"], check, approval, name]
            out.append("| " + " | ".join(" ".join(str(c).split()).replace("|", "/") for c in cells) + " |")
    return "\n".join(out) + "\n"


def report(nucleo: Path, root: Path, doc: Path, check: bool = False) -> list[str]:
    """Valida las piezas y escribe el informe; con `check` no escribe."""
    entities, _, _, files = _checked(nucleo, root)
    text = render(entities, files)
    if check:
        current = doc.read_text(encoding="utf-8") if doc.exists() else None
        return [] if current == text else [f"{doc}: desactualizado (ejecuta lpdatasets contrib-report)"]
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(text, encoding="utf-8", newline="\n")
    return []


def _save(files: dict[Path, list[Piece]], changed: Collection[str]) -> None:
    for path, rows in files.items():
        if any(p["id"] in changed for p in rows):
            path.write_text("".join(dumps(p) + "\n" for p in rows), encoding="utf-8", newline="\n")


def verify(nucleo: Path, root: Path, doc: Path, ident: str, record: dict[str, str], day: str | None = None) -> None:
    """Anota la verificación de una pieza sobre su texto actual y el de la fuente."""
    entities, _, folder, files = _checked(nucleo, root)
    found = [p for rows in files.values() for p in rows if p["id"] == ident]
    if not found:
        raise SystemExit(f"{ident}: no existe esa pieza")
    [piece] = found
    piece.pop("aprobacion", None)
    stamp = {"fecha": day or date.today().isoformat(), "huella": fingerprint(piece), "sobre": about(entities, piece)}
    piece["verificacion"] = record | stamp
    problems = _check_records(piece)
    if problems:
        raise SystemExit("\n".join(f"{ident}: {p}" for p in problems))
    _save(files, {ident})
    report(nucleo, root, doc)


def approve(nucleo: Path, root: Path, doc: Path, approver: str, idents: Collection[str] = ()) -> int:
    """Aprueba las piezas nombradas, o todas las verificadas si no se nombra ninguna; devuelve cuántas."""
    if not approver.strip():
        raise SystemExit("falta el nombre de quien aprueba")
    stale = report(nucleo, root, doc, check=True)
    if stale:
        raise SystemExit("\n".join(stale))
    entities, _, _, files = _checked(nucleo, root)
    states = {p["id"]: state(entities, p) for rows in files.values() for p in rows}
    refused = sorted(i for i in idents if states.get(i) != "verificada")
    if refused:
        raise SystemExit(f"solo se aprueban piezas verificadas y sin cambios: {', '.join(refused)}")
    chosen = set(idents) or {i for i, s in states.items() if s == "verificada"}
    for rows in files.values():
        for piece in rows:
            if piece["id"] in chosen:
                check = piece["verificacion"]
                piece["aprobacion"] = {"por": approver.strip(), "huella": check["huella"], "sobre": check["sobre"]}
    _save(files, chosen)
    report(nucleo, root, doc)
    return len(chosen)
