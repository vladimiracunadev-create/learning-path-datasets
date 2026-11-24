# Esquema de registros (v1.0)

Un archivo `.jsonl` tiene un objeto JSON por línea, con claves ordenadas y sin espacios sobrantes, de modo que dos exportaciones iguales producen bytes idénticos. La definición formal está en [`schema/record.schema.json`](../schema/record.schema.json) y la validación ejecutable en `src/lpdatasets/schema.py`; ambas se comprueban entre sí en las pruebas.

## Campos

| Campo | Tipo | Obligatorio | Significado |
|---|---|:---:|---|
| `schema` | `"1.0"` | sí | versión del esquema |
| `id` | texto | sí | identificador estable y único |
| `pack` | texto | sí | adaptador de origen (`escolar-chile`, `markdown-course`…) |
| `dominio` | texto | sí | área de conocimiento (`educacion-escolar`…) |
| `nivel` | texto | sí | nivel o etapa (`1-basico`) |
| `asignatura` | texto | sí | asignatura, tema o archivo |
| `unidad` | texto | sí | código de objetivo, módulo o archivo de origen |
| `clase` | entero o nulo | no | número de clase dentro de la unidad |
| `tipo` | enumeración | sí | ver tabla de tipos |
| `dificultad` | 1–5 o nulo | no | 1 recuperación … 5 desafío |
| `entrada` | texto | sí | pregunta, enunciado, contexto o término |
| `salida` | texto | sí | respuesta, explicación o definición |
| `razon` | texto o nulo | no | justificación o pasos de la respuesta |
| `idioma` | texto | sí | código de idioma (`es`, `en`) |
| `habilidades` | lista de texto | no | etiquetas de habilidad (hoy vacías) |
| `verificable` | booleano | sí | verdadero si la respuesta puede comprobarse por cálculo |
| `fuente` | objeto | sí | `repo`, `commit` y `ruta` de origen |
| `licencia` | texto | sí | licencia del contenido |
| `revision` | enumeración | sí | `ia_asistida_sin_revision_humana`, `revision_humana_parcial`, `revision_humana_completa`, `no_aplica` |
| `particion` | `train` o `eval` | sí | partición asignada |
| `extra` | objeto | no | campos propios del tipo (IPA, sílabas, sinónimos…) |

## Tipos

| Tipo | `entrada` | `salida` |
|---|---|---|
| `explicacion` | objetivo de la clase | explicación completa |
| `ejemplo_resuelto` | título y problema | respuesta; los pasos van en `razon` |
| `ejercicio_cerrado` | enunciado | respuesta; la justificación va en `razon` |
| `autoevaluacion` | pregunta de cierre | respuesta |
| `error_comun` | error frecuente | corrección; el porqué va en `razon` |
| `actividad_abierta` | consigna | ejemplo de respuesta; los criterios van en `razon` |
| `vocabulario` | término | definición |
| `diccionario_es` / `diccionario_en` | palabra | significado o traducción; el detalle va en `extra` |
| `concepto` | recorrido de encabezados | texto de la sección |

## Particiones

La partición se calcula con un hash determinista del pack y de la **clase** (no del ejemplo), de modo que todos los registros de una clase caen en el mismo lado y no hay fuga entre entrenamiento y evaluación dentro de una clase. Cerca del 10 % de las clases va a `eval`. Los diccionarios no se parten: van en `train`.

## Manifiesto

Cada carpeta de dataset incluye `manifest.json` con commit de origen, licencias, estado de revisión, conteos por tipo, asignatura e idioma, y el SHA-256 de cada archivo. `lpdatasets validate` lo comprueba.
