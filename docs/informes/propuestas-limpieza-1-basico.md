# Propuestas de limpieza · 1.º básico

Generado con `lpdatasets clean-proposals`; no se edita a mano. **Nada está decidido hasta que una persona lo apruebe.**

Primera lectura: asistente de IA; sin revisión humana (2026-11-26).

| Veredicto propuesto | Lotes | Hallazgos | Pendientes |
|---|---:|---:|---:|
| aceptar | 11 | 1081 | 7 |
| corregir | 2 | 39 | 39 |
| decidir | 3 | 11 | 0 |

## Lotes

| Lote | Veredicto | Hallazgos | Afectados | Cómo se clasificó | Pendientes |
|---|---|---:|---:|---|---:|
| `duplicado-glosario` | aceptar | 139 | 324 | por regla | 2 |
| `duplicado-repaso` | aceptar | 13 | 26 | leído | 0 |
| `vocabulario-variantes` | aceptar | 266 | 688 | leído | 0 |
| `vocabulario-acepciones` | aceptar | 30 | 73 | leído | 0 |
| `vocabulario-redaccion` | decidir | 3 | 14 | leído | 0 |
| `conflicto-contexto` | aceptar | 13 | 26 | leído | 0 |
| `enunciado-opciones` | aceptar | 318 | 1006 | por regla | 1 |
| `enunciado-comprension` | aceptar | 117 | 504 | leído | 3 |
| `enunciado-decidir` | decidir | 6 | 32 | leído | 0 |
| `cuaderno-propio-enunciado` | aceptar | 26 | 29 | por regla | 1 |
| `cuaderno-ensenanza` | aceptar | 128 | 158 | leído y por regla | 0 |
| `cuaderno-decidir` | decidir | 2 | 3 | leído | 0 |
| `texto-oficial-fragmento` | aceptar | 12 | 12 | leído | 0 |
| `cruces-dataset` | corregir | 19 | 230 | por regla | 19 |
| `etiquetas` | corregir | 20 | 24904 | por regla | 20 |
| `texto-aplicado` | aceptar | 19 | 66 | por regla | 0 |

## Segunda lectura

Otro agente de IA leyó a ciegas una muestra de 136 casos: elegidos al azar, más todos los que la primera lectura quería corregir o dejar a decisión en ese momento, como control.

- Las 9 correcciones propuestas entonces: confirmadas las 9.
- De 116 casos que la primera lectura aceptaba: 101 sin observaciones, 3 defectos y 12 dudas.
- Esos 15 casos pasaron a `corregir` o `decidir`. Dos reglas se endurecieron y se leyeron los 61 casos que quedaron marcados.
- Los lotes resultantes **no tienen una tercera lectura**: los clasificados por regla pueden contener defectos no detectados.

## Cómo aprobar

Solo se aprueban lotes con veredicto `aceptar`; queda registrado quién aprobó:

```bash
lpdatasets clean-approve --lote duplicado-glosario --aprobado-por "nombre"
```

Los lotes `corregir` y `decidir` siguen pendientes hasta que el cambio esté aplicado y comprobado.

## `duplicado-glosario`

**aceptar** · la misma palabra con la misma definición en el glosario de varias clases. Propuesta: conservar en el núcleo; el dataset siguiente usa una sola copia. Se aplica en: ninguno.

Ejemplos: `duplicado_exacto:0037967b4c4e`, `duplicado_exacto:010336af34e6`, `duplicado_exacto:029752f209e5`.

## `duplicado-repaso`

**aceptar** · la misma pregunta se repite en otra clase como repaso. Propuesta: conservar en el núcleo; el dataset siguiente usa una sola copia. Se aplica en: ninguno.

Ejemplos: `duplicado_exacto:338a9e749bfc`, `duplicado_exacto:69093fde205b`, `duplicado_exacto:69c6bd1e4516`.

## `vocabulario-variantes`

**aceptar** · la misma idea redactada de otra forma según la clase. Propuesta: conservar; toda modalidad entrega la definición con su clase. Se aplica en: ninguno.

Ejemplos: `respuestas_en_conflicto:0192056e3926`, `respuestas_en_conflicto:01e918dea215`, `respuestas_en_conflicto:024de9617903`.

## `vocabulario-acepciones`

**aceptar** · la palabra tiene sentidos distintos según la clase. Propuesta: conservar; toda modalidad entrega la definición con su clase. Se aplica en: ninguno.

Ejemplos: `respuestas_en_conflicto:07a27b42764c`, `respuestas_en_conflicto:0d452de1d95f`, `respuestas_en_conflicto:2a5952e9bf5f`.

## `vocabulario-redaccion`

**decidir** · alguna definición puede ser imprecisa para 6 años. Propuesta: que una persona con criterio pedagógico confirme o reescriba. Se aplica en: fuente.

- `respuestas_en_conflicto:50631ae00456`: «regla»: mezcla el instrumento con descripciones muy particulares de un patrón
- `respuestas_en_conflicto:939bfa6fcbfe`: «generalizar»: ambas definiciones lo presentan solo como algo negativo
- `respuestas_en_conflicto:e0983b929fd0`: «total»: «cuántas marcas hay en una fila» es muy particular

## `conflicto-contexto`

**aceptar** · respuestas distintas y válidas para la misma pregunta en clases distintas. Propuesta: conservar; toda modalidad entrega la pregunta con su clase. Se aplica en: ninguno.

Ejemplos: `respuestas_en_conflicto:2d3bc9b39148`, `respuestas_en_conflicto:41d15493a41f`, `respuestas_en_conflicto:55015b928ca0`.

## `enunciado-opciones`

**aceptar** · pregunta de elección, lista o lectura donde la respuesta debe estar en el enunciado. Propuesta: conservar. Se aplica en: ninguno.

Ejemplos: `solucion_en_enunciado:03233cc2280c`, `solucion_en_enunciado:0374fa85b4e4`, `solucion_en_enunciado:0410e555306a`.

## `enunciado-comprension`

**aceptar** · copia, comprensión o inferencia sobre un texto dado. Propuesta: conservar. Se aplica en: ninguno.

Ejemplos: `solucion_en_enunciado:01bd1353b0ca`, `solucion_en_enunciado:02e7aeda9928`, `solucion_en_enunciado:03390d3cb25b`.

## `enunciado-decidir`

**decidir** · puede ser un apoyo intencional o regalar la respuesta. Propuesta: decidir caso a caso. Se aplica en: fuente.

| Ítem | Enunciado | Respuesta | Motivo |
|---|---|---|---|
| `ar01-oa-02:c05:ej-understand-03` | En una composición con líneas rectas negras y rectángulos de colores, ¿la textura es protagonista o el color y la línea? | El color y la línea | se puede acertar repitiendo palabras de la descripción |
| `le01-oa-13:c01:ej-challenge-02` | Escribe una frase que diga qué hay en tu mesa (por ejemplo, «Hay un vaso»). | Por ejemplo: Hay un vaso | el ejemplo del enunciado es una respuesta válida; puede ser un apoyo |
| `te01-oa-01:c03:ej-apply-01` | Dibujas una caja para 8 fichas. Mide 12 cm de largo y 6 cm de ancho. ¿Qué dos medidas escribes en el dibujo? | 12 cm de largo y 6 cm de ancho | las medidas ya están dadas y solo se copian |
| `te01-oa-01:c03:ej-challenge-01` | Tu marcador mide 15 cm de largo y 3 cm de ancho. Escribe cómo pondrías las medidas, con unidades, junto al dibujo. | 15 cm de largo y 3 cm de ancho | las medidas ya están dadas y solo se copian |
| `hi01-oa-06:c04:ej-recovery-02` | Pedro dice que baila el 16 de julio. ¿Qué mes dice? | julio | basta repetir un dato dicho en la misma frase |
| `hi01-oa-03:c02:ej-recovery-01` | Mateo nació en Arica. ¿Cuál es su lugar de nacimiento? | Arica | basta repetir un dato dicho en la misma frase |
| `ma01-oa-16:c01:ej-apply-01` | Luis tardó 12 aplausos en armar una torre. ¿Cuánto duró? | 12 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-apply-02` | Sofía tardó 9 aplausos en lavarse las manos. ¿Cuánto duró? | 9 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-apply-03` | Camila se ató los cordones en 6 pulsos. ¿Cuánto duró? | 6 pulsos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-contexto-01` | Mientras la profesora escribe la fecha en la pizarra, cuento 11 aplausos. ¿Cuánto duró? | 11 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-01` | Una niña camina hasta la puerta y cuento 5 aplausos. ¿Cuánto duró? | 5 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-02` | Un niño dibuja un círculo en 7 aplausos. ¿Cuánto duró? | 7 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-03` | Una niña tarda 3 aplausos en cerrar su mochila. ¿Cuánto duró? | 3 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |

## `cuaderno-propio-enunciado`

**aceptar** · la respuesta aparece en el cuaderno solo porque está en su propio enunciado. Propuesta: conservar; se juzga en la regla del enunciado. Se aplica en: ninguno.

Ejemplos: `solucion_en_cuaderno:08b98cdf8f86`, `solucion_en_cuaderno:0fcce8bb5c71`, `solucion_en_cuaderno:0fd3875893bb`.

## `cuaderno-ensenanza`

**aceptar** · la respuesta es el contenido que la clase enseña antes de preguntar. Propuesta: conservar. Se aplica en: ninguno.

Ejemplos: `solucion_en_cuaderno:01fea5ddc6d9`, `solucion_en_cuaderno:03ad553d1174`, `solucion_en_cuaderno:03b7bcf761bc`.

## `cuaderno-decidir`

**decidir** · el cuaderno puede adelantar la respuesta. Propuesta: decidir caso a caso. Se aplica en: fuente.

| Ítem | Enunciado | Respuesta | Motivo |
|---|---|---|---|
| `hi01-oa-07:c05:ej-apply-01` | Gabriela Mistral se llamaba Lucila Godoy Alcayaga. Nació el 7 de abril de 1889 en Vicuña, en el valle de Elqui. Fue maestra. Publicó el libro «Ternura» en 1924, con poemas y rondas para niños. En 1945 recibió el Premio Nobel de Literatura. Murió el 10 de enero de 1957. Completa: «Gabriela Mistral contribuyó a la cultura, porque en 1945 ___». | recibió el Premio Nobel de Literatura | las fichas del cuaderno repiten el dato pedido |
| `te01-oa-03:c01:ej-recovery-02` | Para hacer un portalápices, ¿eliges una lata o una botella de plástico limpia? | Una botella de plástico limpia | el ejemplo hace casi la misma elección |

## `texto-oficial-fragmento`

**aceptar** · fragmento breve de vocabulario o enumeración común, no el objetivo completo. Propuesta: conservar; es una decisión de derechos del titular. Se aplica en: ninguno.

Ejemplos: `texto_oficial:02550a9a1f50`, `texto_oficial:565a00d8e06e`, `texto_oficial:56e36b7234bd`.

## `cruces-dataset`

**corregir** · contenido de evaluación presente en entrenamiento en el dataset v1.0. Propuesta: partir por OA y sacar de evaluación toda entrada presente en entrenamiento. Se aplica en: modalidad L08.

Ejemplos: `cruce_identico:244803a8a228`, `cruce_identico:2a12ff5844f1`, `cruce_identico:3b74d502a448`.

## `etiquetas`

**corregir** · faltan habilidades o dificultad. Propuesta: etiquetar con criterio y verificador. Se aplica en: línea L03.

Ejemplos: `sin_dificultad:1eb2fc264b85`, `sin_dificultad:238ffdf94471`, `sin_dificultad:28547402e89c`.

## `texto-aplicado`

**aceptar** · se aplicaron textos aprobados y la regla lo sigue señalando por su forma. Propuesta: nada pendiente; la decisión cita el commit. Se aplica en: ninguno.

Ejemplos: `respuestas_en_conflicto:0b0fab4a1bac`, `respuestas_en_conflicto:0b9017921eab`, `respuestas_en_conflicto:18367484efab`.
