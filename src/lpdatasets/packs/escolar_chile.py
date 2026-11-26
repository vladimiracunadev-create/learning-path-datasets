"""Pack «escolar-chile»: lee el repositorio chilean-school-learning-path y emite registros del esquema común.

Lee el registro de cuadernos del estudiante (explicación, ejemplos resueltos, ejercicios con razón,
errores comunes, autoevaluación y actividad abierta) y los diccionarios de español e inglés del nivel.

No copia los textos oficiales de los OA: solo cita su código. Excluye por ahora las asignaturas de
lengua y cultura de pueblos originarios, que necesitan un educador tradicional.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..schema import SCHEMA_VERSION, partition_for
from . import Record, register

PACK_ID = "escolar-chile"
DOMINIO = "educacion-escolar"
LICENCIA = "CC-BY-NC-SA-4.0"
REVISION = "ia_asistida_sin_revision_humana"
SOURCE_REPO = "vladimiracunadev-create/chilean-school-learning-path"
EXCLUDED_SUBJECTS = {"lengua-cultura-pueblos-originarios-ancestrales"}
LEVEL_CODE = {
    "1-basico": "01",
    "2-basico": "02",
    "3-basico": "03",
    "4-basico": "04",
    "5-basico": "05",
    "6-basico": "06",
    "7-basico": "07",
    "8-basico": "08",
    "1-medio": "09",
    "2-medio": "10",
    "3-medio": "11",
    "4-medio": "12",
}
TIER_DIFFICULTY = {"recovery": 1, "understand": 2, "apply": 3, "reason": 4, "challenge": 5}
GRADE_OF_PREFIX_LEVEL = {
    "01": "1-basico",
    "02": "2-basico",
    "03": "3-basico",
    "04": "4-basico",
    "05": "5-basico",
    "06": "6-basico",
    "07": "7-basico",
    "08": "8-basico",
}


def _git_commit(source: Path) -> str:
    out = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return out.stdout.strip() or "desconocido"


def _txt(value: Any) -> str:
    return " ".join(str(value).split())


def _rec(base: dict[str, Any], suffix: str, tipo: str, entrada: str, salida: str, **extra: Any) -> Record:
    rec: Record = {
        "schema": SCHEMA_VERSION,
        "id": f"{base['_prefix']}:{suffix}",
        "pack": PACK_ID,
        "dominio": DOMINIO,
        "nivel": base["nivel"],
        "asignatura": base["asignatura"],
        "unidad": base["unidad"],
        "clase": base["clase"],
        "tipo": tipo,
        "dificultad": extra.pop("dificultad", None),
        "entrada": _txt(entrada),
        "salida": _txt(salida),
        "razon": extra.pop("razon", None),
        "idioma": "es",
        "habilidades": [],
        "verificable": bool(extra.pop("verificable", False)),
        "fuente": {"repo": SOURCE_REPO, "commit": base["_commit"], "ruta": base["_ruta"]},
        "licencia": LICENCIA,
        "revision": REVISION,
        "particion": base["particion"],
    }
    if rec["razon"]:
        rec["razon"] = _txt(rec["razon"])
    if extra:
        rec["extra"] = extra
    return rec


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")


def _class_records(base: dict[str, Any], content: dict[str, Any]) -> Iterator[Record]:
    if content.get("use") and content.get("explain"):
        yield _rec(
            base, "explicacion", "explicacion", f"Objetivo de la clase: {content['use']}", " ".join(content["explain"])
        )
    for i, (term, meaning) in enumerate(content.get("vocab", []), 1):
        yield _rec(base, f"vocab-{i:02d}", "vocabulario", term, meaning)
    for i, ex in enumerate(content.get("worked", []), 1):
        steps = " ".join(f"{n}. {s}" for n, s in enumerate(ex.get("steps", []), 1))
        yield _rec(
            base,
            f"ejemplo-{i:02d}",
            "ejemplo_resuelto",
            f"{ex['title']}: {ex['problem']}",
            ex["answer"],
            razon=steps or None,
        )
    for i, err in enumerate(content.get("mistakes", []), 1):
        yield _rec(
            base, f"error-{i:02d}", "error_comun", f"Error frecuente: {err['wrong']}", err["fix"], razon=err.get("why")
        )
    for tier, items in content.get("tiers", {}).items():
        for i, ex in enumerate(items, 1):
            yield _rec(
                base,
                f"ej-{tier}-{i:02d}",
                "ejercicio_cerrado",
                ex["q"],
                ex["a"],
                razon=ex.get("why"),
                dificultad=TIER_DIFFICULTY.get(tier),
                verificable=ex.get("calc") is not None,
            )
    for i, ex in enumerate(content.get("context", []), 1):
        yield _rec(
            base,
            f"ej-contexto-{i:02d}",
            "ejercicio_cerrado",
            ex["q"],
            ex["a"],
            razon=ex.get("why"),
            dificultad=3,
            verificable=ex.get("calc") is not None,
        )
    for i, ex in enumerate(content.get("selfcheck", []), 1):
        yield _rec(
            base,
            f"auto-{i:02d}",
            "autoevaluacion",
            ex["q"],
            ex["a"],
            razon=ex.get("why"),
            verificable=ex.get("calc") is not None,
        )
    task = content.get("open_task")
    if task:
        criteria = "; ".join(task.get("criteria", []))
        yield _rec(
            base,
            "actividad-abierta",
            "actividad_abierta",
            task["statement"],
            task["example"],
            razon=f"Criterios: {criteria}" if criteria else None,
            evidencia=task.get("evidence", []),
            errores_posibles=task.get("errors", []),
        )


def _dictionary_records(source: Path, commit: str, nivel: str) -> Iterator[Record]:
    code = LEVEL_CODE[nivel]
    base_common = {"unidad": f"diccionario-{nivel}", "clase": None, "particion": "train", "_commit": commit}
    for lang, tipo in (("es", "diccionario_es"), ("en", "diccionario_en")):
        mod_name = f"dict_data_{lang}_{code}"
        if not (source / "scripts" / f"{mod_name}.py").exists():
            continue
        mod = importlib.import_module(mod_name)
        base = {
            **base_common,
            "nivel": nivel,
            "asignatura": f"lengua-{lang}",
            "_prefix": f"{PACK_ID}:{nivel}:{mod_name}",
            "_ruta": f"scripts/{mod_name}.py",
        }
        for line in mod.PALABRAS.strip().splitlines():
            f = [p.strip() for p in line.split("|")]
            if lang == "es":
                word, silabas, clase_g, sig, sin, ant, ejemplo, tema = f
                rec = _rec(
                    base,
                    f"pal-{_slug(word)}-{_slug(clase_g)}",
                    tipo,
                    word,
                    sig,
                    silabas=silabas,
                    clase_gramatical=clase_g,
                    sinonimos=sin,
                    antonimos=ant,
                    ejemplo=ejemplo,
                    tema=tema,
                )
            else:
                word, clase_g, ipa, figurada, es, sig, ex_en, ex_es, tema = f
                rec = _rec(
                    base,
                    f"word-{_slug(word)}-{_slug(clase_g)}",
                    tipo,
                    word,
                    es,
                    ipa=ipa,
                    como_suena=figurada,
                    clase_gramatical=clase_g,
                    significado=sig,
                    ejemplo_en=ex_en,
                    ejemplo_es=ex_es,
                    tema=tema,
                )
                rec["idioma"] = "en"
            yield rec
        for line in mod.VERBOS.strip().splitlines():
            f = [p.strip() for p in line.split("|")]
            if lang == "es":
                inf, silabas, sig, yo, el, ayer, man, sin, ant, ejemplo = f
                yield _rec(
                    base,
                    f"verbo-{_slug(inf)}",
                    tipo,
                    inf,
                    sig,
                    silabas=silabas,
                    clase_gramatical="verbo",
                    yo_presente=yo,
                    el_presente=el,
                    el_ayer=ayer,
                    el_manana=man,
                    sinonimos=sin,
                    antonimos=ant,
                    ejemplo=ejemplo,
                )
            else:
                b, ipa, past, past_es, es, el_es, sig, ex_en, ex_es = f
                rec = _rec(
                    base,
                    f"verb-{_slug(b)}",
                    tipo,
                    b,
                    es,
                    ipa=ipa,
                    pasado=past,
                    pasado_es=past_es,
                    presente_el_es=el_es,
                    clase_gramatical="verbo",
                    significado=sig,
                    ejemplo_en=ex_en,
                    ejemplo_es=ex_es,
                )
                rec["idioma"] = "en"
                yield rec


@register(PACK_ID)
def records(source: str | Path, nivel: str = "1-basico", **_: Any) -> Iterator[Record]:
    """Emite los registros de un nivel a partir de un checkout de chilean-school-learning-path."""
    source = Path(source).resolve()
    if nivel not in LEVEL_CODE:
        raise SystemExit(f"nivel desconocido: {nivel}")
    if not (source / "scripts" / "student_lessons.py").exists():
        raise SystemExit(f"{source} no parece ser chilean-school-learning-path")
    sys.path.insert(0, str(source / "scripts"))
    try:
        student_lessons = importlib.import_module("student_lessons")
        validator = importlib.import_module("validate_student_lessons")
        student_lessons.load_all()
        commit = _git_commit(source)
        code = LEVEL_CODE[nivel]
        files: dict[str, Path | None] = {}
        for (oa_code, number), content in sorted(student_lessons.REGISTRY.items()):
            if oa_code not in files:
                files[oa_code] = validator.curriculum_file(oa_code)
            path = files[oa_code]
            if path is None or path.parent.parent.name != nivel:
                continue
            asignatura = path.parent.name
            if asignatura in EXCLUDED_SUBJECTS:
                continue
            ruta = path.relative_to(source).as_posix()
            key = f"{nivel}|{oa_code}|{number}"
            base = {
                "nivel": nivel,
                "asignatura": asignatura,
                "unidad": oa_code,
                "clase": number,
                "particion": partition_for(PACK_ID, key),
                "_commit": commit,
                "_ruta": ruta,
                "_prefix": f"{PACK_ID}:{nivel}:{_slug(oa_code)}:c{number:02d}",
            }
            yield from _class_records(base, content)
        if code:
            yield from _dictionary_records(source, commit, nivel)
    finally:
        sys.path.remove(str(source / "scripts"))
