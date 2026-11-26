# L08 · Dataset

- **Estado:** `PLANIFICADO`
- **Depende de:** L01 y L02

## Propósito

Producir desde el núcleo datos para entrenar y evaluar, en varios formatos. Hoy existe el dataset v1.0 de pares, exportado directamente desde la fuente y operativo; esta línea cubre su sucesor.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Datos en formato conversacional | quien entrena | educativo | docente |
| Pares instrucción y respuesta | quien entrena | educativo | docente |
| Conjunto de evaluación aislado | quien evalúa | educativo | docente |
| Conocimiento atómico | quien entrena o recupera | educativo | docente |

## Entradas y salidas

Entrada: selección del núcleo y 19 hallazgos que [L02](L02-limpieza.md) le asignó sobre el dataset v1.0 (9 de registros de evaluación idénticos a uno de entrenamiento y 10 con la misma entrada). Salida: JSONL por formato, manifiesto con SHA-256 y tarjeta del dataset.

## Contrato de datos

El [esquema de registros v1.0](../DATASET_SCHEMA.md) sigue vigente. La partición pasa a decidirse por OA y se agrega el formato `messages`. Además, se saca de evaluación toda entrada presente en entrenamiento, se conserva una sola copia de los duplicados exactos y los pares repetidos entre clases llevan el contexto de su clase ([propuestas de limpieza](../informes/propuestas-limpieza-1-basico.md)).

## Derechos

Un conjunto declara la licencia más restrictiva de sus componentes y nunca incluye entidades sin el uso permitido.

## Cómo se ejecuta

La versión nueva no está implementada. La actual:

```bash
lpdatasets export --pack escolar-chile --nivel 1-basico --source ../chilean-school-learning-path --out datasets
lpdatasets validate
```

## Pruebas

Existentes: `tests/test_published_datasets.py`. Exigidas: ausencia de cruces entre particiones, exactos y por entrada.

## Métricas

Cruces entre particiones (objetivo: 0); cobertura de OA; registros por tipo.

## Listo cuando

No queda ningún registro de evaluación idéntico a uno de entrenamiento ni con su misma entrada, y cada formato tiene manifiesto, tarjeta y validación en CI.

## Límites

El volumen de 1.º básico (unos 0,6 millones de tokens estimados a 4 caracteres por token) sirve para ajuste y evaluación, no para preentrenar un modelo.

## Decisiones

- 2026-11-26: al cerrar la fase 1, la eliminación de los cruces es criterio de término de esta línea.
- 2026-11-26: reemplazar v1.0 solo cuando la nueva versión esté validada. Hasta entonces v1.0 conserva sus cruces y no sirve para medir un modelo.
