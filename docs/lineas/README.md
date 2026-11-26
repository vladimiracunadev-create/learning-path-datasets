# Líneas de implementación

Cada línea del [plan de 1.º básico](../PLAN_1_BASICO.md) se documenta aquí. El registro es [`lineas.json`](lineas.json) y la forma la fija la [plantilla](_PLANTILLA.md).

| Línea | Documento |
|---|---|
| L01 | [Núcleo de contenido](L01-nucleo.md) |
| L02 | [Limpieza de datos](L02-limpieza.md) |
| L03 | [Vacíos y creación de contenido](L03-vacios-creacion.md) |
| L04 | [Vigía curricular](L04-vigia-curricular.md) |
| L05 | [Recuperación (RAG)](L05-rag.md) |
| L06 | [Servidor MCP](L06-mcp.md) |
| L07 | [Skills y agentes de uso](L07-agentes-uso.md) |
| L08 | [Dataset](L08-dataset.md) |
| L09 | [Ajuste de modelos](L09-fine-tuning.md) |
| L10 | [Modalidad nueva](L10-modalidad-nueva.md) |

Al avanzar, actualiza en `lineas.json` el estado de la línea y de su fase (`hecha`, `en curso` o `pendiente`) y regenera el [esquema](../img/plan-1-basico.svg):

```bash
python scripts/docs_diagram.py --write
```

Comprobación:

```bash
python scripts/verify_docs.py
```

Falla si una línea registrada no tiene documento, si falta una sección, si el estado no coincide con el registro, si hay un enlace local roto o si el código registra una modalidad sin línea.

Estados: `PLANIFICADO` (no hay implementación nueva), `EXPERIMENTAL` (hay una parte probada), `OPERATIVO` (cumple su criterio de término).
