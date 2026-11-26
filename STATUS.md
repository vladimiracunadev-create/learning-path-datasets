# Estado verificable

Versión canónica: **0.2.0** · Python mínimo: **3.11**

## Cifras de los datasets

<!-- STATS:BEGIN -->

| Dataset | Registros | Entrenamiento | Evaluación | Clases (entr. / eval.) | Verificables por cálculo |
|---|---:|---:|---:|---:|---:|
| `escolar-chile` · 1-basico | 16.386 | 14.589 | 1.797 | 498 / 64 | 427 |

**Total publicado:** 16.386 registros en 1 dataset(s).

Tipos en `escolar-chile` · 1-basico: actividad_abierta 562, autoevaluacion 1.686, diccionario_en 214, diccionario_es 355, ejemplo_resuelto 1.131, ejercicio_cerrado 7.868, error_comun 1.124, explicacion 562, vocabulario 2.884.

<!-- STATS:END -->

## Matriz de madurez

| Componente | Estado | Fuente de verdad |
|---|---|---|
| Esquema v1.0 y validación | `OPERATIVO` | `src/lpdatasets/schema.py`, `schema/record.schema.json` |
| Pack `escolar-chile` · 1.º básico | `OPERATIVO` | `datasets/escolar-chile/1-basico/` y su `manifest.json` |
| Pack `escolar-chile` · 2.º básico a 4.º medio | `PLANIFICADO` | el programa de origen ya tiene los cuadernos; falta exportarlos |
| Pack `markdown-course` | `EXPERIMENTAL` | `tests/test_pipeline.py` (programa sintético) |
| Validación de SHA-256, ids y particiones | `OPERATIVO` | `lpdatasets validate` |
| Índice NumPy exacto | `OPERATIVO` | `lpdatasets index` y `search` |
| Índice Qdrant local | `OPERATIVO-CON-EXTRA` | extra `qdrant`; prueba de equivalencia |
| Embeddings semánticos | `PLANIFICADO` | no implementado; el embedder por defecto es léxico |
| Skills y agentes (`.claude/`) | `OPERATIVO` | `scripts/verify_assets.py`; estructura verificada, calidad de salida no medida |
| Etiquetado de habilidades | `PLANIFICADO` | el campo `habilidades` está vacío |
| Contrato del núcleo `nucleo-0.1` | `EXPERIMENTAL` | `src/lpdatasets/core.py`, `schema/core.schema.json`, `tests/test_core.py` |
| Núcleo de 1.º básico | `OPERATIVO` | `nucleo/escolar-chile/1-basico/manifest.json`, `lpdatasets core-validate` |
| Informe y propuestas de limpieza | `EXPERIMENTAL` | `lpdatasets clean-report --check` y `clean-proposals --check`; 1.073 hallazgos aceptados, 19 resueltos, 39 pendientes y 26 archivados |
| Vigía curricular | `OPERATIVO` | `lpdatasets watch-report --check`, `tests/test_watch.py`, `tests/test_watch_pages.py`; a pedido, 4 fuentes manuales sin revisar |
| Capa de aportes | `EXPERIMENTAL` | `lpdatasets contrib-report --check`, `tests/test_contributions.py`; ninguna pieza todavía |
| Registro de modalidades | `EXPERIMENTAL` | `src/lpdatasets/modalities.py`, `tests/test_modalities.py`; ninguna modalidad real |
| Líneas de implementación | ver cada una | [`docs/lineas/`](docs/lineas/README.md), `scripts/verify_docs.py` |
| Revisión humana profesional | `NO REALIZADA` | todos los registros declaran `ia_asistida_sin_revision_humana` |

## Cómo comprobarlo

```bash
ruff check src tests scripts
pytest
python scripts/smoke.py
python scripts/docs_stats.py --check
python scripts/verify_docs.py
python scripts/docs_diagram.py --check
lpdatasets core-validate
lpdatasets clean-report --check
lpdatasets clean-proposals --check
lpdatasets clean-corrections --check
lpdatasets clean-doubts --check
lpdatasets watch-report --check
lpdatasets contrib-report --check
lpdatasets validate
```
