# Contribuir

Abre un issue con una fuente mínima (o un fragmento sintético), el resultado esperado y el real, tu sistema operativo y tu versión de Python. Para cambios de código crea una rama, limita el alcance y acompaña cada comportamiento nuevo con una prueba.

```bash
python -m venv .venv && . .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -e ".[dev,qdrant]"
ruff check src tests scripts
ruff format --check src tests scripts
pytest
python scripts/smoke.py
python scripts/docs_stats.py --check
lpdatasets validate
```

## Reglas para los datos

- **No incluyas** textos de terceros, datos personales, credenciales ni contenido sin licencia que permita redistribuirlo.
- **No copies** textos oficiales de objetivos de aprendizaje: cita su código.
- Cada registro necesita `fuente` (repositorio, commit y ruta) y `licencia`. El estado de `revision` debe ser verdadero: no marques revisión humana si no la hubo.
- Si cambias un dataset publicado, regenéralo con `lpdatasets export` y actualiza las cifras con `python scripts/docs_stats.py --write`. No edites los JSONL a mano: el SHA-256 del manifiesto lo detectará.
- Un pack nuevo debe asignar la partición por clase o unidad, nunca por ejemplo suelto, y traer pruebas con una fuente sintética.

Al participar aceptas el [Código de conducta](CODE_OF_CONDUCT.md).
