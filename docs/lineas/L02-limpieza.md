# L02 · Limpieza de datos

- **Estado:** `EXPERIMENTAL`
- **Depende de:** L01

## Propósito

Detectar y resolver duplicados, respuestas en conflicto, fugas entre particiones, referencias a recursos que no están y etiquetas ausentes, dejando registro de cada cambio.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Quitar pares repetidos antes de entrenar | quien entrena | educativo | docente |
| Revisar una misma pregunta con dos respuestas | revisor | educativo | docente |
| Marcar un ejercicio que pide mirar una imagen inexistente | autor | educativo | estudiante |
| Registrar una revisión humana por muestreo | revisor | educativo | docente |

## Entradas y salidas

Entrada: el núcleo y, como línea base, el dataset v1.0. Salida: `nucleo/escolar-chile/1-basico/limpieza/hallazgos.jsonl` y el [informe de limpieza](../informes/limpieza-1-basico.md). Nunca edita los datos.

## Contrato de datos

Cada hallazgo guarda `id` estable, `regla`, `severidad`, `ambito`, `total`, `entidades`, `evidencia`, `accion_propuesta`, `estado`, `motivo` y `aprobado_por`. Las reglas agregadas de etiquetas guardan una muestra de 20 identificadores. Las decisiones van en `limpieza/decisiones.json`:

```json
{"decisiones": [{"id": "regla:abc123abc123", "estado": "aceptado", "motivo": "…", "aprobado_por": "…"}]}
```

Si las entidades de un hallazgo cambian, su identificador cambia y la decisión antigua se rechaza.

## Derechos

No cambia licencias ni procedencia. No eleva el estado de revisión sin una persona identificable que haya revisado.

## Cómo se ejecuta

```bash
lpdatasets clean-report
lpdatasets clean-proposals
lpdatasets clean-approve --lote duplicado-glosario --aprobado-por "nombre"
```

`clean-corrections` comprueba las redacciones nuevas de `limpieza/correcciones.json` simulando el cambio en una copia (no duplicar, no contradecir otra respuesta y no quedar respondidas por el cuaderno) y escribe las [correcciones propuestas](../informes/correcciones-1-basico.md). No las aplica.

```bash
lpdatasets clean-corrections
lpdatasets clean-approve-corrections --aprobado-por "nombre"
```

Después de aplicar en la fuente lo aprobado, el orden es:

```bash
lpdatasets core-export --source ../chilean-school-learning-path
lpdatasets export --pack escolar-chile --nivel 1-basico --source ../chilean-school-learning-path --out datasets
lpdatasets clean-mark-applied
lpdatasets clean-report
lpdatasets clean-proposals
lpdatasets clean-corrections
lpdatasets clean-doubts
```

`clean-mark-applied` va antes de `clean-report`: compara con los hallazgos anteriores y marca las correcciones presentes. Lo que dejó de aparecer se archiva en `limpieza/resueltos.jsonl` con su decisión; lo que sigue señalado y tiene aplicados todos los textos de su duda queda `resuelto`; una aceptación que cubría un texto cambiado se retira a `limpieza/retiradas.jsonl`. También retira los juicios sobre textos que ya no existen. Se detiene ante un texto inesperado o un hallazgo que desaparece sin explicación.

La aprobación de correcciones omite las que tienen una duda abierta, salvo que se nombren con `--incluir`, y queda ligada al texto: si la redacción cambia, deja de valer.

`clean-doubts` genera la [hoja de dudas](../informes/dudas-1-basico.md): una recomendación (mantener, reescribir o aprobar la redacción) por cada hallazgo que espera criterio, desde `limpieza/dudas.json`. Excluye etiquetas y cruces, que dependen de líneas posteriores. `clean-resolve-doubts` es el único paso que decide: registra «mantener» como decisión del hallazgo y aprueba los textos, sin aplicarlos; admite `--excluir`.

```bash
lpdatasets clean-doubts
lpdatasets clean-resolve-doubts --aprobado-por "nombre"
```

`clean-proposals` agrupa los hallazgos en lotes y escribe las [propuestas](../informes/propuestas-limpieza-1-basico.md). Combina reglas generales con los juicios de lectura guardados en `limpieza/revision.json`; lo que exige lectura y no la tiene queda en `sin-revisar`. `clean-approve` es el único paso que registra decisiones, solo admite lotes que proponen aceptar y exige el nombre de quien aprueba. Con `--check`, los dos informes se comprueban sin escribirse.

El agente [`limpiador-datos`](../../.claude/agents/limpiador-datos.md) prepara las propuestas de decisión; las aprueba una persona.

## Pruebas

`tests/test_cleaning.py` tiene un caso sintético por regla, comprueba el determinismo y rechaza decisiones incompletas u obsoletas. `tests/test_proposals.py` comprueba que lo no leído nunca se proponga aceptar y que la aprobación rechace lotes de corrección. `tests/test_corrections.py` rechaza redacciones obsoletas, repetidas o respondidas por el cuaderno, y comprueba qué se aprueba y cuándo una aprobación deja de valer. El CI comprueba que el informe publicado corresponda a los datos.

## Métricas

Primer informe, 2026-11-26: 1.140 hallazgos (tabla de reglas). Tras aprobar los lotes y aplicar las 59 correcciones aprobadas en dos tandas: **1.131 hallazgos, 1.066 aceptados, 19 resueltos que la regla sigue señalando y 46 pendientes**; 26 más dejaron de aparecer y están archivados.

| Pendientes | Hallazgos |
|---|---:|
| Etiquetas (L03) | 20 |
| Cruces del dataset (L08) | 19 |
| Proponen aceptar y esperan aprobación (6 nuevos y 1 aceptación retirada) | 7 |

Primer informe, por regla:

| Regla | Hallazgos | Afectados |
|---|---:|---:|
| Evaluación idéntica a entrenamiento (v1.0) | 9 | 27 |
| Evaluación con la entrada en entrenamiento (v1.0) | 10 | 203 |
| Duplicado exacto por asignatura | 151 | 348 |
| Respuestas en conflicto por asignatura y tipo | 328 | 856 |
| Solución contenida en el enunciado | 445 | 1.569 |
| Respuesta larga literal en el cuaderno | 165 | 201 |
| Coincidencia con texto oficial | 12 | 12 |
| Sin habilidades | 12 | 16.386 |
| Sin dificultad | 8 | 8.518 |

Las cifras de duplicados y conflictos difieren de la medición del plan porque ahora se agrupa por asignatura y tipo.

Propuestas del 2026-11-26:

| Veredicto propuesto | Hallazgos | Estado |
|---|---:|---|
| aceptar | 1.042 | aceptados |
| corregir | 63 | pendientes: 24 sobre 27 preguntas, 19 de cruces del dataset (L08) y 20 de etiquetas (L03) |
| decidir | 35 | pendientes: 19 de vocabulario, 11 de enunciado y 5 de cuaderno |

Las [correcciones](../informes/correcciones-1-basico.md) de las 27 preguntas, más una detectada al redactar, están escritas. El titular aprobó el 2026-11-26 las 24 sin duda abierta, que se **aplicaron en la fuente** (commit `3fd976d5`) y llegaron al núcleo y al dataset al volver a exportar; quedaron 4 sin aprobar. Esas 4 y otros 31 textos se aprobaron después al resolver las dudas y se aplicaron en una segunda tanda (commit `b3647111`): las 59 correcciones están aplicadas. En una primera verificación ciega, 19 de 28 quedaron sin observaciones; las otras 9 se cambiaron y otro verificador dejó 5 sin observaciones, 1 por corregir (aplicada, sin otra lectura) y 3 dudas.

Un segundo agente leyó a ciegas 136 casos: confirmó las 9 correcciones que se proponían entonces y objetó 15 de 116 casos que se proponía aceptar (3 defectos y 12 dudas). Esos 15 pasaron a `corregir` o `decidir`.

## Listo cuando

Hay un informe antes y después, cada hallazgo está resuelto o aceptado con motivo y no queda ningún registro de evaluación idéntico a uno de entrenamiento.

## Límites

Las 39 dudas se decidieron el 2026-11-26 (11 mantener, 25 reescribir y 3 aprobar). Las de «mantener» no tuvieron segunda lectura. En la primera ronda ciega se objetaron 18 de 34 textos nuevos, sobre todo definiciones: redactar glosarios sin criterio pedagógico es poco fiable. 

Las reglas encuentran problemas de forma; los errores pedagógicos requieren un lector, y muchos hallazgos «revisar» pueden ser legítimos. `recurso_ausente` dio 0: solo busca consignas que piden ver o escuchar un medio con ciertos verbos; en los ejemplos leídos las consignas describen la imagen con palabras, pero eso no descarta otros casos. Los aceptados se aprobaron por lote, no revisando caso a caso, y aceptar significa conservar el contenido: no es una revisión pedagógica. El informe «después» cubre las 59 correcciones aplicadas; quedan 46 pendientes. Los 19 resueltos con textos que la regla sigue señalando descansan en la aprobación del texto, no en otra lectura contra la regla. Algunas definiciones de «sentido» dicen «frase» y las clases suelen decir «oración». La regla del enunciado no ve una elección regalada con otro género o número (el texto dice «rígida» y se responde «Rígido»): se halló una al redactar y puede haber otras. Las propuestas son de agentes de IA, sin revisión humana ni una tercera lectura; la segunda lectura fue una muestra y los lotes clasificados por regla pueden contener defectos.

## Decisiones

- 2026-11-26: el agente `limpiador-datos` propone cambios y no borra sin registro.
- 2026-11-26: los cruces del dataset v1.0 se corrigen al construir la versión siguiente (L08).
- 2026-11-26: una corrección de contenido se aplica en la fuente y regenera el núcleo y el dataset v1.0; no se editan sus archivos.
- 2026-11-26: los hallazgos resueltos se archivan con el commit; un hallazgo nuevo no hereda la aprobación de otro.
- 2026-11-26: una aceptación no sobrevive al cambio de un texto que cubre; se retira y se vuelve a decidir.
- 2026-11-26: el titular aprobó los 15 hallazgos que quedaron proponiendo aceptar tras la reexportación (11 nuevos y 4 que cambiaron de lote).
- 2026-11-26: el titular aprobó todas las recomendaciones sobre dudas, incluidos los tres textos con observación de la segunda lectura.
- 2026-11-26: el titular autorizó aplicar los 35 textos en la fuente.
- 2026-11-26: las decisiones se aprueban por lote; los lotes de corrección siguen pendientes hasta aplicar el cambio.
- 2026-11-26: las correcciones se redactan y revisan aquí; el contenido se cambia en la fuente, con autorización expresa, y se vuelve a exportar.
- 2026-11-26: el titular (`vladimiracunadev-create`) aprobó los 10 lotes de aceptación, incluidas las 12 coincidencias breves con texto oficial.
