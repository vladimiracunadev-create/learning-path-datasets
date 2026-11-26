# L01 · Núcleo de contenido

- **Estado:** `EXPERIMENTAL`
- **Depende de:** nada; las demás líneas dependen de esta

## Propósito

Representar el contenido de 1.º básico una sola vez, como clases, ítems y recursos con marco curricular, derechos, revisión y procedencia, para que cada modalidad lo lea sin volver a interpretar la fuente.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Ver una clase completa con su OA | docente | educativo | docente |
| Entregar un ejercicio sin la solución | estudiante acompañado | educativo | estudiante |
| Saber si un contenido puede usarse en un producto pagado | titular | comercial | docente |
| Separar bases vigentes de una propuesta | mantenimiento | educativo | docente |
| Agregar una imagen o un audio a una clase | autor | personal | estudiante |

## Entradas y salidas

Entrada: un commit fijo de `chilean-school-learning-path` (fichas, cuadernos del estudiante, catálogo y diccionarios). Salida prevista: archivos JSONL de entidades del núcleo, con manifiesto y SHA-256, fuera de `datasets/`.

## Contrato de datos

[Contrato `nucleo-0.1`](../CORE_CONTRACT.md): `schema/core.schema.json` y `src/lpdatasets/core.py`.

## Derechos

El contenido pedagógico original de la fuente es CC BY-NC-SA 4.0. El texto de los OA es redacción oficial: se cita el código y, si algún día se incluye el texto, va como entidad aparte con origen `oficial` y licencia `MINEDUC-NO-COMERCIAL`. Lengua y Cultura de Pueblos Originarios queda excluida.

## Cómo se ejecuta

Hoy existen el contrato, su validador y la selección por uso, público y marco:

```python
from lpdatasets.core import select, validate_entity
```

La exportación de 1.º básico al núcleo **no está implementada**.

## Pruebas

Existentes: `tests/test_core.py` (validación, coincidencia con el JSON Schema, permisos y ocultamiento de soluciones). Exigidas para terminar: exportación reproducible y conciliación con el catálogo de la fuente.

## Métricas

Entradas de catálogo representadas sobre 1.034; entidades inválidas (objetivo: 0); entidades sin derechos o sin marco (objetivo: 0).

## Listo cuando

Las 691 clases desarrolladas y las 343 experiencias integradas están representadas o excluidas con motivo declarado, y dos exportaciones del mismo commit producen los mismos bytes.

## Límites

El contrato puede cambiar mientras sea `0.1`. Validar la forma no comprueba que el contenido sea correcto.

## Decisiones

- 2026-11-26: el núcleo es independiente del esquema de registros v1.0, que no cambia; el dataset publicado sigue siendo válido.
- 2026-11-26: las particiones de entrenamiento no son parte del núcleo; las decide cada modalidad.
