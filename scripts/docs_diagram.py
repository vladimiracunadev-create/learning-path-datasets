"""Dibuja el esquema SVG de lo que se construye, con la fase y el estado de cada línea.

Lee `docs/lineas/lineas.json`, así el dibujo no se desactualiza.

python scripts/docs_diagram.py --write   # reescribe docs/img/plan-1-basico.svg
python scripts/docs_diagram.py --check   # falla si el dibujo no coincide con lineas.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("docs") / "img" / "plan-1-basico.svg"
WIDTH = 1200
# Posición y textos breves de las líneas conocidas. Una línea nueva se apila sola bajo «Modalidad nueva».
BOXES: dict[str, tuple[int, int, int, int, str, str]] = {
    "L01": (420, 220, 360, 180, "Núcleo de contenido", "clases · ítems · recursos"),
    "L02": (880, 260, 280, 100, "Limpieza", "duplicados y conflictos"),
    "L03": (40, 300, 280, 100, "Vacíos y creación", "audio, imágenes, ítems"),
    "L04": (40, 150, 280, 100, "Vigía curricular", "cambios educativos en Chile"),
    "L05": (60, 570, 320, 100, "Recuperación (RAG)", "buscar y citar"),
    "L06": (60, 710, 320, 100, "Servidor MCP", "consulta desde asistentes"),
    "L07": (60, 850, 320, 100, "Skills y agentes de uso", "tutor, guías, evaluaciones"),
    "L08": (440, 570, 320, 100, "Dataset", "entrenar y evaluar"),
    "L09": (440, 710, 320, 100, "Ajuste de modelos", "estilo y nivel de 6 años"),
    "L10": (820, 570, 320, 100, "Modalidad nueva", "fichas, audio, apps…"),
}
EXTRA_X, EXTRA_Y, EXTRA_STEP = 820, 710, 140
ARROWS = (
    "M600 160 V214",  # fuente -> núcleo
    "M180 250 V294",  # vigía -> creación
    "M320 350 H414",  # creación -> núcleo
    "M780 292 H874",  # núcleo -> limpieza
    "M880 328 H786",  # limpieza -> núcleo
    "M600 400 V444",  # núcleo -> selección
    "M220 510 V564",
    "M600 510 V564",
    "M980 510 V564",
    "M220 670 V704",
    "M220 810 V844",
    "M600 670 V704",
)
LABELS = (
    (612, 192, "start", "adaptadores"),
    (192, 278, "start", "aprobación humana"),
    (367, 340, "middle", "crea"),
    (830, 282, "middle", "revisa"),
    (830, 348, "middle", "corrige"),
)
STATE_STYLE = {
    "OPERATIVO": ("#dcfce7", "#15803d", "", "operativo"),
    "EXPERIMENTAL": ("#fef3c7", "#b45309", "", "experimental"),
    "PLANIFICADO": ("#f8fafc", "#64748b", ' stroke-dasharray="7 5"', "planificado"),
}
PHASE_STYLE = {"hecha": "OPERATIVO", "en curso": "EXPERIMENTAL", "pendiente": "PLANIFICADO"}


def text(
    x: int, y: int, value: str, size: int = 14, anchor: str = "middle", weight: int = 400, fill: str = "#0f172a"
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'fill="{fill}">{escape(value)}</text>'
    )


def rect(x: int, y: int, w: int, h: int, state: str) -> str:
    fill, stroke, dash, _ = STATE_STYLE[state]
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="2"{dash}/>'
    )


def line_box(line: dict[str, Any], geometry: tuple[int, int, int, int, str, str]) -> list[str]:
    x, y, w, h, label, detail = geometry
    mid, top = x + w // 2, y + (h - 100) // 2
    parts = [
        rect(x, y, w, h, line["estado"]),
        text(mid, top + 32, f"{line['id']} · {label}", 17, weight=700),
        text(mid, top + 57, detail, fill="#334155"),
        text(mid, top + 82, f"Fase {line['fase']} · {STATE_STYLE[line['estado']][3]}", 13, fill="#475569"),
    ]
    if line["id"] == "L01":
        parts.append(text(mid, top + 112, "marco · derechos · revisión · procedencia", 13, fill="#334155"))
    return parts


def render(root: Path = ROOT) -> str:
    registry = json.loads((root / "docs" / "lineas" / "lineas.json").read_text(encoding="utf-8"))
    lines, phases = registry["lineas"], registry["fases"]
    extra = [line for line in lines if line["id"] not in BOXES]
    strip = max(1010, EXTRA_Y + EXTRA_STEP * len(extra) + 20)
    height = strip + 200
    description = "; ".join(f"{p['titulo']} (fase {p['fase']}): {p['estado']}" for p in phases)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" '
        'role="img" aria-labelledby="titulo descripcion" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
        '<title id="titulo">Qué se construye para 1.º básico</title>',
        f'<desc id="descripcion">La fuente alimenta un núcleo de contenido; cada modalidad lee de él a través de '
        f"una selección por uso, público y marco. {escape(description)}.</desc>",
        '<defs><marker id="punta" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#334155"/></marker></defs>',
        f'<rect width="{WIDTH}" height="{height}" fill="#ffffff"/>',
        text(600, 42, "Qué se construye · 1.º básico", 28, weight=700),
        text(600, 68, "Un solo núcleo de contenido y muchas formas de usarlo", 15, fill="#475569"),
        '<rect x="420" y="90" width="360" height="70" rx="10" fill="#e0f2fe" stroke="#0369a1" stroke-width="2"/>',
        text(600, 119, "Fuente: chilean-school-learning-path", 16, weight=700),
        text(600, 143, "commit fijo", fill="#334155"),
    ]
    arrows = list(ARROWS)
    if extra:
        arrows.append(f"M1140 485 H1170 V{EXTRA_Y + EXTRA_STEP * (len(extra) - 1) + 50} H1146")
    svg += [f'<path d="{d}" fill="none" stroke="#334155" stroke-width="2" marker-end="url(#punta)"/>' for d in arrows]
    svg += [text(x, y, value, 13, anchor, fill="#334155") for x, y, anchor, value in LABELS]
    svg += [
        '<rect x="60" y="450" width="1080" height="60" rx="10" fill="#1e293b"/>',
        text(600, 476, "Selección: select()", 17, weight=700, fill="#ffffff"),
        text(600, 498, "filtra por uso, público y marco curricular, y oculta las soluciones", fill="#e2e8f0"),
    ]
    for line in lines:
        if line["id"] in BOXES:
            svg += line_box(line, BOXES[line["id"]])
    for position, line in enumerate(extra):
        geometry = (EXTRA_X, EXTRA_Y + EXTRA_STEP * position, 320, 100, line["titulo"], "modalidad agregada")
        svg += line_box(line, geometry)
    svg.append(text(60, strip + 16, "Fases", 17, "start", 700))
    width = (1080 - 14 * (len(phases) - 1)) // len(phases)
    for position, phase in enumerate(phases):
        x = 60 + position * (width + 14)
        svg += [
            rect(x, strip + 30, width, 74, PHASE_STYLE[phase["estado"]]),
            text(x + width // 2, strip + 56, f"Fase {phase['fase']} · {phase['estado']}", 14, weight=700),
            text(x + width // 2, strip + 82, phase["titulo"], 13, fill="#334155"),
        ]
    for position, (state, label) in enumerate(
        (("OPERATIVO", "operativo o hecho"), ("EXPERIMENTAL", "experimental o en curso"), ("PLANIFICADO", "pendiente"))
    ):
        x = 60 + position * 260
        svg += [rect(x, strip + 126, 28, 18, state), text(x + 40, strip + 140, label, 13, "start", fill="#334155")]
    note = "Hoy siguen operativos, fuera de este flujo: el dataset v1.0 y su búsqueda léxica."
    svg += [text(60, strip + 178, note, 13, "start", fill="#334155"), "</svg>"]
    return "\n".join(svg) + "\n"


def main(argv: list[str], root: Path = ROOT) -> int:
    target = root / OUTPUT
    drawing = render(root)
    if "--write" in argv:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(drawing, encoding="utf-8", newline="\n")
        print(f"Esquema escrito en {OUTPUT.as_posix()}")
        return 0
    if not target.exists() or target.read_text(encoding="utf-8") != drawing:
        print("El esquema está desactualizado: ejecuta python scripts/docs_diagram.py --write")
        return 1
    print("OK: esquema al día")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
