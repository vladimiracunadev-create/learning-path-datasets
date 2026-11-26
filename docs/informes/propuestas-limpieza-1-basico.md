# Propuestas de limpieza · 1.º básico

Generado con `lpdatasets clean-proposals`; no se edita a mano. **Nada está decidido hasta que una persona lo apruebe.**

Primera lectura: asistente de IA; sin revisión humana (2026-11-26).

| Veredicto propuesto | Lotes | Hallazgos | Pendientes |
|---|---:|---:|---:|
| aceptar | 10 | 1042 | 1042 |
| corregir | 4 | 63 | 63 |
| decidir | 3 | 35 | 35 |

## Lotes

| Lote | Veredicto | Hallazgos | Afectados | Cómo se clasificó | Pendientes |
|---|---|---:|---:|---|---:|
| `duplicado-glosario` | aceptar | 138 | 322 | por regla | 138 |
| `duplicado-repaso` | aceptar | 13 | 26 | leído | 13 |
| `vocabulario-variantes` | aceptar | 266 | 688 | leído | 266 |
| `vocabulario-acepciones` | aceptar | 30 | 73 | leído | 30 |
| `vocabulario-redaccion` | decidir | 19 | 69 | leído | 19 |
| `conflicto-contexto` | aceptar | 13 | 26 | leído | 13 |
| `enunciado-opciones` | aceptar | 307 | 962 | por regla | 307 |
| `enunciado-comprension` | aceptar | 112 | 488 | leído | 112 |
| `enunciado-decidir` | decidir | 11 | 52 | leído | 11 |
| `enunciado-corregir` | corregir | 15 | 67 | leído | 15 |
| `cuaderno-propio-enunciado` | aceptar | 25 | 28 | por regla | 25 |
| `cuaderno-ensenanza` | aceptar | 126 | 153 | leído y por regla | 126 |
| `cuaderno-corregir` | corregir | 9 | 13 | leído | 9 |
| `cuaderno-decidir` | decidir | 5 | 7 | leído | 5 |
| `texto-oficial-fragmento` | aceptar | 12 | 12 | leído | 12 |
| `cruces-dataset` | corregir | 19 | 230 | por regla | 19 |
| `etiquetas` | corregir | 20 | 24904 | por regla | 20 |

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

- `respuestas_en_conflicto:0b0fab4a1bac`: «ritmo»: «la velocidad de los sonidos o pasos» describe más bien el tempo
- `respuestas_en_conflicto:0b9017921eab`: «repetir»: las definiciones describen acciones de ejercicios distintos
- `respuestas_en_conflicto:18367484efab`: «sentido»: «que se entiende» no define sentido
- `respuestas_en_conflicto:1ceb62b948d5`: «permiso»: las definiciones describen una frase o un acto previo, no qué es un permiso
- `respuestas_en_conflicto:25ca145d512f`: «comprobar»: varias definiciones son pasos de un ejercicio concreto
- `respuestas_en_conflicto:27dc831f9895`: «clasificar»: «ordenar según un criterio» confunde clasificar con ordenar
- `respuestas_en_conflicto:4855254e7dd4`: «cero»: «el número más pequeño al contar» puede confundir, porque contar suele empezar en uno
- `respuestas_en_conflicto:4993c127d4fc`: «dato»: las definiciones usan criterios distintos; un dato no tiene que ser importante
- `respuestas_en_conflicto:4b3d5f381649`: «orden»: una definición describe cómo contar, no qué es orden
- `respuestas_en_conflicto:50631ae00456`: «regla»: mezcla el instrumento con descripciones muy particulares de un patrón
- `respuestas_en_conflicto:5a3b3c2996c6`: «no convencional»: define un adjetivo sin decir de qué: instrumento o notación
- `respuestas_en_conflicto:5ab83c4506ca`: «vigoroso»: define el esfuerzo solo por la forma de hablar
- `respuestas_en_conflicto:6d53b9c147bb`: «palabra»: «sílabas que dicen algo» es impreciso
- `respuestas_en_conflicto:7f926afc505c`: «sílaba»: «letras que suenan juntas» es impreciso
- `respuestas_en_conflicto:939bfa6fcbfe`: «generalizar»: ambas definiciones lo presentan solo como algo negativo
- `respuestas_en_conflicto:a38d3eadd73f`: «leer»: limita leer a decir en voz alta
- `respuestas_en_conflicto:a6f663882921`: «restar»: «bajar con la regla» solo se entiende en una actividad concreta
- `respuestas_en_conflicto:e0983b929fd0`: «total»: «cuántas marcas hay en una fila» es muy particular
- `respuestas_en_conflicto:e8307ecff340`: «fondo»: «se dibuja arriba y pequeño» no define fondo en general

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
| `mu01-oa-02:c03:ej-apply-02` | Suena una nota que sube de grave a aguda. ¿Cómo es tu línea: sube o baja? | Sube | el enunciado dice «sube» y pregunta si la línea sube o baja |
| `ar01-oa-02:c05:ej-understand-03` | En una composición con líneas rectas negras y rectángulos de colores, ¿la textura es protagonista o el color y la línea? | El color y la línea | se puede acertar repitiendo palabras de la descripción |
| `le01-oa-13:c01:ej-challenge-02` | Escribe una frase que diga qué hay en tu mesa (por ejemplo, «Hay un vaso»). | Por ejemplo: Hay un vaso | el ejemplo del enunciado es una respuesta válida; puede ser un apoyo |
| `te01-oa-01:c03:ej-apply-01` | Dibujas una caja para 8 fichas. Mide 12 cm de largo y 6 cm de ancho. ¿Qué dos medidas escribes en el dibujo? | 12 cm de largo y 6 cm de ancho | las medidas ya están dadas y solo se copian |
| `te01-oa-01:c03:ej-challenge-01` | Tu marcador mide 15 cm de largo y 3 cm de ancho. Escribe cómo pondrías las medidas, con unidades, junto al dibujo. | 15 cm de largo y 3 cm de ancho | las medidas ya están dadas y solo se copian |
| `hi01-oa-06:c04:ej-recovery-02` | Pedro dice que baila el 16 de julio. ¿Qué mes dice? | julio | basta repetir un dato dicho en la misma frase |
| `hi01-oa-06:c02:ej-challenge-01` | Santiago se fundó el 12 de febrero de 1541. Si la ciudad celebra su aniversario cada 12 de febrero, ¿en qué mes cae el aniversario? | febrero | basta repetir un dato dicho en la misma frase |
| `ma01-oa-18:c04:ej-recovery-01` | La cinta marcada con la puerta sobra al llegar a la mesa. ¿Cuál es más corto? | La mesa | redacción confusa para 6 años |
| `ma01-oa-18:c04:ej-recovery-02` | La cinta marcada con la puerta falta al llegar a la ventana. ¿Cuál mide más, la puerta o la ventana? | La ventana | redacción confusa para 6 años |
| `hi01-oa-03:c02:ej-recovery-01` | Mateo nació en Arica. ¿Cuál es su lugar de nacimiento? | Arica | basta repetir un dato dicho en la misma frase |
| `te01-oa-05:c03:ej-recovery-02` | Una mesa grande se dibuja ¿grande o muy pequeña? | Grande | la respuesta repite el adjetivo del enunciado |
| `ma01-oa-16:c01:ej-apply-01` | Luis tardó 12 aplausos en armar una torre. ¿Cuánto duró? | 12 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-apply-02` | Sofía tardó 9 aplausos en lavarse las manos. ¿Cuánto duró? | 9 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-apply-03` | Camila se ató los cordones en 6 pulsos. ¿Cuánto duró? | 6 pulsos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-contexto-01` | Mientras la profesora escribe la fecha en la pizarra, cuento 11 aplausos. ¿Cuánto duró? | 11 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-01` | Una niña camina hasta la puerta y cuento 5 aplausos. ¿Cuánto duró? | 5 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-02` | Un niño dibuja un círculo en 7 aplausos. ¿Cuánto duró? | 7 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `ma01-oa-16:c01:ej-recovery-03` | Una niña tarda 3 aplausos en cerrar su mochila. ¿Cuánto duró? | 3 aplausos | la duración ya está dicha; practica la unidad, pero casi se copia |
| `le01-oa-12:c04:ej-understand-01` | Escuchaste el cuento de la hormiga. ¿Quién es el personaje? | La hormiga | basta repetir un dato dicho en la misma frase |

## `enunciado-corregir`

**corregir** · la pregunta entrega su propia respuesta. Propuesta: reescribir en la fuente. Se aplica en: fuente.

| Ítem | Enunciado | Respuesta | Motivo |
|---|---|---|---|
| `ma01-oa-17:c04:auto-01` | ¿Qué mes es el 1 de enero? | Enero | pregunta el mes de una fecha que ya nombra el mes |
| `le01-oa-17:c03:ej-apply-03` | Completa con una rima de «luna»: «Brilla la luna / en la ___.» (por ejemplo, laguna) | Por ejemplo: laguna | el ejemplo del enunciado es la respuesta: basta copiarlo |
| `le01-oa-16:c04:ej-apply-01` | Completa con una palabra: «La torta estaba ___.» (por ejemplo, rica) | Por ejemplo: rica | el ejemplo del enunciado es la respuesta: basta copiarlo |
| `hi01-oa-09:c03:ej-apply-02` | Puerto Natales es una localidad de Magallanes y de la Antártica Chilena. ¿Es una región o una localidad? | Una localidad | afirma que es una localidad y pregunta si es región o localidad |
| `hi01-oa-12:c01:ej-apply-03` | Para llegar desde Chile a Japón por mar se cruza el océano Pacífico. ¿Qué país de la lista está al otro lado de ese océano: Noruega o Japón? | Japón | dice que se va a Japón y pregunta qué país está al otro lado |
| `le01-oa-14:c02:ej-apply-02` | Completa con qué hace: «El niño ____.» (por ejemplo, juega) | Por ejemplo: juega | el ejemplo del enunciado es la respuesta: basta copiarlo |
| `cn01-oa-08:c03:ej-recovery-01` | Tabla: la pelota es flexible. ¿A qué grupo va: flexible o rígido? | Flexible | afirma que la pelota es flexible y pregunta si es flexible o rígida |
| `cn01-oa-08:c03:ej-recovery-02` | Tabla: el vaso es transparente. ¿A qué grupo va: transparente u opaco? | Transparente | afirma que el vaso es transparente y pregunta si lo es |
| `mu01-oa-03:c01:ej-apply-01` | Un adulto toca una pandereta rápida y fuerte. Escribe qué observarías sobre su rapidez y su fuerza. | Rápida y fuerte | el enunciado dice la rapidez y la fuerza que pide observar |
| `ar01-oa-01:c01:ej-recovery-01` | Una concha es redonda, tiene rayitas que salen desde un punto y es de color crema. ¿Qué forma tiene? | Redonda | la descripción ya nombra lo que se pregunta |
| `en01-oa-13:c03:ej-recovery-01` | Ordena: I / like / red. Escribe la oración. | I like red. | pide ordenar palabras que ya vienen en el orden correcto |
| `hi01-oa-05:c03:ej-recovery-03` | ¿En qué mes es el 12 de octubre? | octubre | pregunta el mes de una fecha que ya nombra el mes |
| `mu01-oa-07:c03:ej-apply-02` | Describe una lluvia que sonaba suave y larga con dos cualidades. | Suave y larga | el enunciado dice las dos cualidades que pide describir |
| `hi01-oa-13:c05:auto-02` | Escribe una parte que debe tener: qué, quién o cuándo. | Qué, quién o cuándo | pide una parte y la respuesta enumera las tres opciones que da el enunciado |
| `ef01-oa-09:c05:ej-challenge-02` | Haces tu propia alternativa: sin agua para tomar en la plaza. Respuesta posible: avisar a un adulto y pedir agua segura. ¿A quién avisas? | A un adulto | el enunciado incluye la respuesta posible y luego la pregunta |
| `cn01-oa-08:c01:auto-03` | ¿De qué material es un vaso de vidrio? | Vidrio | la pregunta nombra la respuesta: «un vaso de vidrio» y pide el material |
| `cn01-oa-08:c01:ej-recovery-01` | Una botella de vidrio. ¿Cuál es el material? | Vidrio | la descripción ya nombra lo que se pregunta |
| `cn01-oa-08:c01:ej-recovery-03` | Una pelota de goma. ¿Cuál es el material? | Goma | la descripción ya nombra lo que se pregunta |

## `cuaderno-propio-enunciado`

**aceptar** · la respuesta aparece en el cuaderno solo porque está en su propio enunciado. Propuesta: conservar; se juzga en la regla del enunciado. Se aplica en: ninguno.

Ejemplos: `solucion_en_cuaderno:08b98cdf8f86`, `solucion_en_cuaderno:0fcce8bb5c71`, `solucion_en_cuaderno:0fd3875893bb`.

## `cuaderno-ensenanza`

**aceptar** · la respuesta es el contenido que la clase enseña antes de preguntar. Propuesta: conservar. Se aplica en: ninguno.

Ejemplos: `solucion_en_cuaderno:01fea5ddc6d9`, `solucion_en_cuaderno:03ad553d1174`, `solucion_en_cuaderno:03b7bcf761bc`.

## `cuaderno-corregir`

**corregir** · otro ejercicio o ejemplo entrega la respuesta. Propuesta: cambiar uno de los dos. Se aplica en: fuente.

| Ítem | Enunciado | Respuesta | Motivo |
|---|---|---|---|
| `cn01-oa-03:c02:ej-understand-01` | ¿Qué dos trabajos hace la raíz? | Sujeta la planta y absorbe agua | un ejemplo resuelto responde esta misma pregunta |
| `te01-oa-04:c01:ej-apply-03` | Un portalápices debe quedar derecho. Escribe un criterio observable. | Queda derecho al poner 5 lápices | la actividad abierta del cuaderno da esa respuesta |
| `mu01-oa-06:c04:ej-apply-01` | Completa: Me gustó que ___ porque se oyó ___. Usa «tocaste suave» y «el silencio». | Me gustó que tocaras suave porque se oyó el silencio | el ejemplo da exactamente el mismo comentario |
| `hi01-oa-03:c02:ej-apply-01` | Arica está al norte, Valparaíso al centro y Punta Arenas al sur. Ordena de norte a sur: Valparaíso, Arica, Punta Arenas. | Arica, Valparaíso, Punta Arenas | el ejemplo resuelve el mismo orden con las mismas ciudades |
| `hi01-oa-08:c04:ej-contexto-01` | Un niño nuevo llega a la entrada (A3) y debe llegar a la sala (C1). La profesora le da un papel con el plano. ¿Qué recorrido escribe ella? | Sube 2 casillas y avanza 2 a la derecha | el ejemplo resuelve el mismo recorrido |
| `le01-oa-24:c02:ej-understand-03` | ¿Qué tres partes tiene una buena explicación de una palabra? | Palabra, significado y ejemplo | el ejercicio A1 nombra la respuesta de C3 |
| `hi01-oa-06:c04:ej-apply-01` | Reescribe bien: «Todos hacen mingas». Usa «según Elena». | Según Elena, en Chiloé se hacen mingas | el ejemplo reescribe la misma frase |
| `le01-oa-21:c03:ej-recovery-01` | Ana dijo: «Me gusta el patio». ¿Qué frase muestra que escuché: «Tú dijiste que te gusta el patio» o «Yo tengo un perro»? | Tú dijiste que te gusta el patio | el ejemplo responde la misma situación |
| `en01-oa-11:c04:ej-challenge-02` | Escribe en inglés la presentación completa de tu pelota roja con el nombre Tom: saludo, nombre, objeto, color y agradecimiento. | Hello! I am Tom. This is my ball. It is red. Thank you! | el ejemplo usa el mismo modelo y la misma respuesta |

## `cuaderno-decidir`

**decidir** · el cuaderno puede adelantar la respuesta. Propuesta: decidir caso a caso. Se aplica en: fuente.

| Ítem | Enunciado | Respuesta | Motivo |
|---|---|---|---|
| `hi01-oa-01:c01:ej-understand-01` | Ordena de primero a último: viernes, lunes, jueves, martes, miércoles. | lunes, martes, miércoles, jueves, viernes | el ejemplo recita el orden que se pide |
| `hi01-oa-07:c05:ej-apply-01` | Gabriela Mistral se llamaba Lucila Godoy Alcayaga. Nació el 7 de abril de 1889 en Vicuña, en el valle de Elqui. Fue maestra. Publicó el libro «Ternura» en 1924, con poemas y rondas para niños. En 1945 recibió el Premio Nobel de Literatura. Murió el 10 de enero de 1957. Completa: «Gabriela Mistral contribuyó a la cultura, porque en 1945 ___». | recibió el Premio Nobel de Literatura | las fichas del cuaderno repiten el dato pedido |
| `ma01-oa-13:c04:ej-recovery-03` | ¿Desde dónde parto a contar? | Desde la esquina de arriba a la izquierda | la pregunta es ambigua fuera del plano que enseña la clase |
| `le01-oa-17:c05:ej-recovery-01` | Escucha: El zorro y la luna. Una noche, un zorro vio la luna reflejada en un charco. Pensó que era un queso redondo y brillante. Saltó para atraparla y cayó en el agua fría. Salió mojado y con mucho frío. La luna seguía en el cielo, tranquila. Desde esa noche, el zorro miró dos veces antes de saltar. ¿Cómo terminó el cuento? | El zorro miró dos veces antes de saltar | un ejemplo resume cómo terminó el cuento |
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
