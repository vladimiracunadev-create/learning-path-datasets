"""Exportación al núcleo con una fuente sintética que imita la forma de chilean-school-learning-path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from lpdatasets.core import select
from lpdatasets.core_build import read_core, validate_core
from lpdatasets.core_escolar import OfficialIndex, export, redact, split_class

CONTENT_OA = "Contar objetos pequeños usando palabras numéricas en orden estable y sin saltos."
ATTITUDE_OA = "Abordar de manera flexible y creativa la búsqueda de soluciones a problemas."
EXCLUDED = "lengua-cultura-pueblos-originarios-ancestrales"

DEVELOPED = """# Ficha de ejemplo

**Explicación pedagógica.** Orientación propia de ejemplo.

## Planificación clase a clase

### Clase 1 de 1: Contar fichas {#cl-00001}

**Propósito docente:** Practicar el conteo.

### Cuaderno del estudiante

**Ejercicios**

- **R1.** ¿Cuántas fichas hay?

**Solucionario razonado**

- **R1.** Hay tres fichas porque se cuentan una por una hasta llegar a la última.

## Fuente

Nada más.
"""

INTEGRATED = f"""# Actitud de ejemplo

## Planificación clase a clase

### Clase 1 de 1: Explorar: abordar de manera flexible y creativa la… {{#cl-00002}}

**Propósito docente:** Centrado en «{ATTITUDE_OA}»

**Meta:** Hoy aprenderé a abordar de manera flexible y creativa la búsqueda de soluciones a problemas.
"""

LESSONS = """
REGISTRY = {}
def load_all():
    REGISTRY[("MA01 OA 01", 1)] = {
        "use": "contar", "explain": ["Se dice un número por ficha."],
        "tiers": {"recovery": [{"q": "¿Cuántas fichas hay?", "a": "3",
                  "why": "Hay tres fichas porque se cuentan una por una hasta llegar a la última."}]},
    }
"""


def catalog_row(code: str, subject: str, path: str, anchor: int, state: str, oa: str) -> dict:
    return {
        "course_slug": "1-basico",
        "subject_slug": subject,
        "oa_code": code,
        "oa_text": oa,
        "lesson": 1,
        "editorial_status": state,
        "path": f"{path}#cl-{anchor:05d}",
        "class_code": f"CL-{anchor:05d}",
        "axis": "Eje",
        "phase": "Conectar",
    }


def git(folder: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(folder), "-c", "user.name=prueba", "-c", "user.email=prueba@example.invalid", *args],
        check=True,
        capture_output=True,
    )


@pytest.fixture()
def source(tmp_path: Path):
    folder = tmp_path / "fuente"
    math = "curriculum/1-basico/matematica/ma01-oa-01.md"
    attitude = "curriculum/1-basico/matematica/de-actitud-ma01-oaa-a.md"
    other = f"curriculum/1-basico/{EXCLUDED}/lc01-oa-01.md"
    files = {
        math: DEVELOPED,
        attitude: INTEGRATED,
        other: DEVELOPED,
        "curriculum/catalog.json": json.dumps(
            {
                "classes": [
                    catalog_row("MA01 OA 01", "matematica", math, 1, "desarrollada", CONTENT_OA),
                    catalog_row("MA01 OAA A", "matematica", attitude, 2, "integrada", ATTITUDE_OA),
                    catalog_row("LC01 OA 01", EXCLUDED, other, 3, "desarrollada", "Otro objetivo."),
                ]
            },
            ensure_ascii=False,
        ),
        "scripts/student_lessons.py": LESSONS,
        "scripts/validate_student_lessons.py": "from pathlib import Path\n"
        "def curriculum_file(code):\n"
        f"    return Path(__file__).resolve().parents[1] / {math!r}\n",
        ".gitignore": "__pycache__/\n",
    }
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    git(folder, "init", "-q")
    git(folder, "add", "-A")
    git(folder, "commit", "-q", "-m", "fuente")
    yield folder
    for module in ("student_lessons", "validate_student_lessons"):
        sys.modules.pop(module, None)


def test_export_represents_or_declares_every_class(source: Path, tmp_path: Path):
    folder = export(source, tmp_path / "nucleo")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    coverage = manifest["cobertura"]
    assert (coverage["catalogo"], coverage["representadas"]) == (3, 2)
    assert coverage["excluidas"][0]["asignatura"] == EXCLUDED
    assert coverage["excluidas"][0]["motivo"]
    assert validate_core(tmp_path / "nucleo") == []
    assert not any(EXCLUDED in json.dumps(e) for e in read_core(folder))


def test_official_text_of_integrated_classes_is_replaced_by_its_code(source: Path, tmp_path: Path):
    entities = read_core(export(source, tmp_path / "nucleo"))
    text = " ".join(e.get("texto", "") + e.get("titulo", "") for e in entities).lower()
    assert "flexible y creativa" not in text
    assert "texto oficial no incluido: ma01 oaa a" in text


def test_student_never_receives_the_answer_key(source: Path, tmp_path: Path):
    entities = read_core(export(source, tmp_path / "nucleo"))
    seen = select(entities, uso="educativo", publico="estudiante", marcos={"cl-bases-1-6"})
    dumped = json.dumps(list(seen), ensure_ascii=False)
    assert "¿Cuántas fichas hay?" in dumped
    assert "hasta llegar a la última" not in dumped
    teacher = select(entities, uso="educativo", publico="docente", marcos={"cl-bases-1-6"})
    assert "hasta llegar a la última" in json.dumps(list(teacher), ensure_ascii=False)


def test_export_is_deterministic_and_validation_detects_changes(source: Path, tmp_path: Path):
    first = export(source, tmp_path / "a")
    second = export(source, tmp_path / "b")
    for name in ("clases.jsonl", "items.jsonl", "recursos.jsonl", "manifest.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    with (first / "items.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    assert any("sha256" in p for p in validate_core(tmp_path / "a"))


def test_uncommitted_source_changes_are_rejected(source: Path, tmp_path: Path):
    (source / "scripts" / "student_lessons.py").write_text("REGISTRY = {}\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="sin confirmar"):
        export(source, tmp_path / "nucleo")


def test_other_levels_are_not_supported(source: Path, tmp_path: Path):
    with pytest.raises(SystemExit, match="1-basico"):
        export(source, tmp_path / "nucleo", "2-basico")


@pytest.mark.parametrize(
    "body",
    [
        "Plan\n### Cuaderno del estudiante\nPreguntas",
        "Plan\n**Solucionario razonado**\nR\n### Cuaderno del estudiante\nPreguntas",
        "Plan solamente",
    ],
)
def test_class_without_a_separable_answer_key_stops_the_export(body: str):
    with pytest.raises(SystemExit, match="solucionario"):
        split_class(body, "demo")


def test_redaction_keeps_own_text_and_ignores_short_coincidences():
    text, count = redact("Hoy vamos a contar objetos con calma.", CONTENT_OA, "MA01 OA 01")
    assert (text, count) == ("Hoy vamos a contar objetos con calma.", 0)
    assert OfficialIndex({"MA01 OA 01": CONTENT_OA}).match(f"Dice: {CONTENT_OA}") == "MA01 OA 01"
    assert OfficialIndex({"MA01 OA 01": CONTENT_OA}).match("contar objetos pequeños") is None
