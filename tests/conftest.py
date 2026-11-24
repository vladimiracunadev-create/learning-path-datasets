from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def mini_course(tmp_path: Path) -> Path:
    """Programa de aprendizaje mínimo en Markdown, con dos dominios sintéticos."""
    folder = tmp_path / "curso"
    folder.mkdir()
    (folder / "redes.md").write_text(
        "# Redes\n\n## Direcciones IP\n\n"
        + "Una dirección IP identifica a un equipo dentro de una red y permite que los paquetes lleguen a su destino. "
        * 2
        + "\n\n## Puertos\n\n"
        + "Un puerto es un número que indica qué servicio de un equipo debe recibir una conexión, por ejemplo el puerto 443 para HTTPS. "
        * 2
        + "\n",
        encoding="utf-8",
    )
    (folder / "finanzas.md").write_text(
        "# Finanzas\n\n## Interés compuesto\n\n"
        + "El interés compuesto calcula los intereses sobre el capital inicial y también sobre los intereses ya acumulados en periodos anteriores. "
        * 2
        + "\n",
        encoding="utf-8",
    )
    return folder
