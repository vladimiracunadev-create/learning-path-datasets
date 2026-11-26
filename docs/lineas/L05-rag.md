# L05 · Recuperación (RAG)

- **Estado:** `PLANIFICADO`
- **Depende de:** L01 y L02

## Propósito

Encontrar la parte correcta del contenido y entregarla con su cita, para responder apoyándose en él.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| «Cómo enseño a contar de 2 en 2» | docente | educativo | docente |
| Apoyo en casa sin revelar la solución | familia | personal | familia |
| Ejercicios parecidos a uno dado | docente | educativo | docente |
| Consulta sin internet | docente | educativo | docente |

## Entradas y salidas

Entrada: selección del núcleo por uso, público y marco. Salida: fragmentos por sección de clase, índice y resultados con identificador, OA, licencia y atribución.

## Contrato de datos

Cada fragmento conserva el identificador de su entidad, marco, público y derechos. Los ítems se entregan con su clase: la misma pregunta o palabra puede tener respuestas distintas y válidas según la clase ([propuestas de limpieza](../informes/propuestas-limpieza-1-basico.md)).

## Derechos

Los resultados muestran atribución y licencia. El índice se construye desde la selección, así lo no permitido nunca entra.

## Cómo se ejecuta

La modalidad no está implementada. Hoy existe la búsqueda léxica sobre el dataset v1.0:

```bash
lpdatasets index --out .vector
lpdatasets search "contar de uno en uno" -k 3
```

## Pruebas

Existentes para el índice v1.0: `tests/test_pipeline.py`. Exigidas: conjunto de consultas de referencia y comprobación de que la vista de estudiante no devuelve soluciones.

## Métricas

Acierto en los primeros k resultados y posición media del primer acierto sobre 100 a 200 consultas de referencia, comparando léxico, semántico e híbrido.

## Listo cuando

El acierto está medido y publicado, y la variante elegida supera a la búsqueda léxica.

## Límites

Recuperar bien no garantiza responder bien. Los modelos de embeddings candidatos no se han probado en este repositorio.

## Decisiones

- 2026-11-26: candidatos `intfloat/multilingual-e5-small` y `BAAI/bge-m3`; la elección se hace midiendo.
- 2026-11-26: al evaluar un modelo, el índice excluye el contenido reservado para evaluación.
