# Informe de limpieza · escolar-chile · 1-basico

Generado con `lpdatasets clean-report`; no se edita a mano. Propone cambios y **no modifica los datos**.

- Núcleo: 18926 entidades, 16386 ítems, commit de la fuente `b3647111142b`.
- Dataset v1.0 revisado como línea base: 16386 registros.
- Hallazgos: 1141; pendientes: 49.

| Regla | Severidad | Hallazgos | Afectados | Pendientes |
|---|---|---:|---:|---:|
| `clase_incompleta` | error | 0 | 0 | 0 |
| `cruce_identico` | error | 9 | 27 | 9 |
| `cruce_por_entrada` | revisar | 10 | 203 | 10 |
| `duplicado_exacto` | revisar | 152 | 350 | 0 |
| `respuestas_en_conflicto` | revisar | 327 | 854 | 0 |
| `recurso_ausente` | revisar | 0 | 0 | 0 |
| `solucion_en_enunciado` | revisar | 445 | 1555 | 0 |
| `solucion_en_cuaderno` | revisar | 156 | 190 | 0 |
| `texto_oficial` | revisar | 12 | 12 | 0 |
| `sin_habilidades` | info | 22 | 16386 | 22 |
| `sin_dificultad` | info | 8 | 8518 | 8 |

«Afectados» cuenta entidades o registros dentro de cada regla; una misma entidad puede aparecer en varias.
Las reglas son comprobaciones de forma: un hallazgo «revisar» puede ser legítimo.

Resueltos con textos aprobados que la regla sigue señalando: 19.

## Resueltos

Hallazgos que dejaron de aparecer al aplicar correcciones en la fuente o aportes. Se conservan en `limpieza/resueltos.jsonl`.

| Resuelto en | Regla | Hallazgos | Afectados |
|---|---|---:|---:|
| `3fd976d50bb2` | `solucion_en_cuaderno` | 6 | 9 |
| `3fd976d50bb2` | `solucion_en_enunciado` | 10 | 51 |
| `b3647111142b` | `respuestas_en_conflicto` | 1 | 2 |
| `b3647111142b` | `solucion_en_cuaderno` | 5 | 6 |
| `b3647111142b` | `solucion_en_enunciado` | 4 | 19 |

## `clase_incompleta`

Detecta: clase sin guía, o clase desarrollada sin cuaderno o sin ítems. Propuesta: revisar la exportación y la fuente.

Sin hallazgos.

## `cruce_identico`

Detecta: registros de evaluación del dataset v1.0 idénticos a uno de entrenamiento. Propuesta: sacarlos de evaluación al construir la siguiente versión del dataset.

- `cruce_identico:e9d749368a99` (8): lenguaje-comunicacion: 8 registros de evaluación
- `cruce_identico:244803a8a228` (6): ingles-propuesta: 6 registros de evaluación
- `cruce_identico:3b74d502a448` (3): artes-visuales: 3 registros de evaluación

## `cruce_por_entrada`

Detecta: registros de evaluación del dataset v1.0 cuya entrada está en entrenamiento. Propuesta: partir por OA en la siguiente versión y revisar los que persistan.

- `cruce_por_entrada:c8ff6728e8c7` (82): lenguaje-comunicacion: 82 registros de evaluación
- `cruce_por_entrada:42441d672d3f` (27): matematica: 27 registros de evaluación
- `cruce_por_entrada:6bd905813f54` (19): historia-geografia-ciencias-sociales: 19 registros de evaluación

## `duplicado_exacto`

Detecta: ítems de una asignatura con el mismo enunciado y la misma respuesta. Propuesta: conservar uno en las modalidades donde repetir no aporte.

- `duplicado_exacto:06dbf55a0c5c` (6): ingles-propuesta: «happy» → «contento»
- `duplicado_exacto:108afe0388b8` (5): ingles-propuesta: «where?» → «¿dónde?»
- `duplicado_exacto:35be76d2d04b` (5): ingles-propuesta: «thank you» → «gracias»

## `respuestas_en_conflicto`

Detecta: mismo enunciado, asignatura y tipo con respuestas distintas. Propuesta: decidir si falta contexto en el enunciado o si ambas respuestas son válidas.

- `respuestas_en_conflicto:25ca145d512f` (9): matematica: «comprobar» → «contar para ver qué tan cerca estuve» / «revisar calculando los dos lados» / «revisar con otra operación» / «revisar con una suma» / «revisar que el orden sea correcto» / «revisar que encaja» / «revisar que la respuesta cumple todas las pistas» / «revisar que todo coincida
- `respuestas_en_conflicto:053a4c1eda9c` (7): matematica: «diferencia» → «cuánto aumenta» / «cuánto más duró uno que otro» / «cuántos más tiene una que otra» / «lo que falta para igualar» / «lo que separa dos números» / «lo que separa dos números; se calcula restando el menor al mayor» / «lo que sobra al emparejar»
- `respuestas_en_conflicto:66c46ff39d40` (7): lenguaje-comunicacion: «detalle» → «dato pequeño» / «dato pequeño que da imagen» / «dato pequeño que da información» / «dato que agrega información» / «parte pequeña del dibujo» / «una parte pequeña del texto» / «una parte pequeña pero importante»

## `recurso_ausente`

Detecta: consigna que pide ver o escuchar algo que no está como recurso. Propuesta: crear el recurso (línea L03) o reescribir la consigna.

Sin hallazgos.

## `solucion_en_enunciado`

Detecta: ejercicio con solución oculta cuyo enunciado contiene la respuesta. Propuesta: confirmar si es una pregunta de elección legítima o reescribirla.

- `solucion_en_enunciado:ceca0bc63543` (11): escolar-chile:1-basico:le01-oa-04:c05: «Lee: «La rana salta». ¿Quién salta?»
- `solucion_en_enunciado:ef8dd4c99b81` (11): escolar-chile:1-basico:le01-oa-10:c03: «¿Un artículo informativo cuenta datos verdaderos o inventados?»
- `solucion_en_enunciado:96a3b613cafd` (10): escolar-chile:1-basico:le01-oa-01:c03: «Una etiqueta dice: «Este yogur tiene leche». ¿Informa o invita?»

## `solucion_en_cuaderno`

Detecta: respuesta larga de un ejercicio que aparece literal en el cuaderno de su clase. Propuesta: confirmar si es parte de la explicación o si regala la respuesta.

- `solucion_en_cuaderno:0fcce8bb5c71` (3): escolar-chile:1-basico:te01-oa-01:c03: «12 cm de largo y 6 cm de ancho»
- `solucion_en_cuaderno:2b42041ef191` (3): escolar-chile:1-basico:or01-oa-02:c03: ««Me enojé porque se rompió mi dibujo»»
- `solucion_en_cuaderno:4546f51cd8aa` (3): escolar-chile:1-basico:le01-oa-10:c03: «Muchas plantas no tendrían frutos»

## `texto_oficial`

Detecta: tramo de ocho o más palabras que coincide con la redacción oficial de un OA. Propuesta: confirmar si es vocabulario común o reescribirlo citando el código.

- `texto_oficial:02550a9a1f50` (1): coincide con la redacción de HI01 OA 05
- `texto_oficial:565a00d8e06e` (1): coincide con la redacción de HI01 OA 15
- `texto_oficial:56e36b7234bd` (1): coincide con la redacción de MA01 OA 01

## `sin_habilidades`

Detecta: ítems sin habilidades etiquetadas. Propuesta: etiquetar desde OA e indicadores (L03).

- `sin_habilidades:b393baf10ef0` (2620): lenguaje-comunicacion: 2620 ítems de tarea
- `sin_habilidades:b16385ddf462` (1660): matematica: 1660 ítems de tarea
- `sin_habilidades:789012cd68cc` (1380): ingles-propuesta: 1380 ítems de tarea

## `sin_dificultad`

Detecta: ítems sin dificultad. Propuesta: etiquetar con un criterio declarado.

- `sin_dificultad:28547402e89c` (2884): vocabulario: 2884 ítems
- `sin_dificultad:c809686e40da` (1686): autoevaluacion: 1686 ítems
- `sin_dificultad:4b55f1574bdd` (1131): ejemplo_resuelto: 1131 ítems
