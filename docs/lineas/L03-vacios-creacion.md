# L03 · Vacíos y creación de contenido

- **Estado:** `EXPERIMENTAL`
- **Depende de:** L01 y L04

## Propósito

Encontrar lo que falta para 1.º básico, buscar información confiable y crear contenido propio que la cubra, con verificación independiente.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Audio para quien aún no lee | autor | educativo | estudiante |
| Imagen o lámina que una consigna pide | autor | educativo | estudiante |
| Ítems de evaluación por OA | docente | educativo | docente |
| Guía breve para el adulto que acompaña | familia | personal | familia |
| Adecuaciones de acceso (diseño universal) | docente | educativo | docente |
| Texto de lectura propio en vez de un enlace | autor | educativo | estudiante |
| Etiquetar habilidades y dificultad con un criterio declarado | autor | educativo | docente |

## Entradas y salidas

Entrada: vacíos medidos sobre el núcleo y fuentes con licencia conocida; además, los hallazgos de etiquetas que [L02](L02-limpieza.md) le asignó: 10 de tareas sin habilidades, uno por asignatura. Salida: recursos, ítems y etiquetas nuevas, más una ficha de cada fuente consultada.

## Contrato de datos

Entidades `recurso` e `item` del núcleo. Todo recurso que no sea texto lleva `descripcion` como texto alternativo.

Lo nuevo vive en la **capa de aportes**, `aportes/<pack>/<nivel>/*.jsonl`, una pieza por línea. El núcleo publicado no se modifica.

| Campo | Contenido |
|---|---|
| `id` | `aporte:<pack>:<nivel>:<nombre>` |
| `tipo` | `entidad` (ítem o recurso nuevo) o `etiqueta` |
| `autor` | `nombre` y `tipo` (`ia` o `persona`) |
| `fuentes` | al menos una: `ref`, `uso` (`derivado` o `consulta`) y, si es derivado, `licencia` |
| `derechos` | como en el núcleo; no pueden permitir más usos que las fuentes derivadas |
| `pieza` | en entidades: la clase a la que pertenece y los campos propios; marco, nivel, asignatura, revisión y procedencia los pone la combinación |
| `clase` o `item`, `campo`, `valor`, `tipos` | en etiquetas: a qué ítems, qué campo (`habilidades` o `dificultad`) y con qué valor |
| `verificacion` | `por` (distinto del autor), `tipo`, `veredicto`, `nota`, `fecha` y huellas |
| `aprobacion` | `por`: la persona que aprueba, y las mismas huellas |

Estados: `borrador`, `verificada`, `observada`, `aprobada` y `caducada`. **Solo entra lo aprobado.** Las huellas cubren la pieza y el texto de la fuente al que se refiere: si cualquiera cambia, la pieza caduca. Una etiqueta solo llena campos que la fuente dejó vacíos, y las habilidades salen de [`vocabulario.json`](../../aportes/escolar-chile/1-basico/vocabulario.json) (los 21 objetivos de habilidad oficiales de Matemática, Historia y Ciencias Naturales). Un archivo que no es texto se guarda dentro de la carpeta de aportes y se declara con su `sha256`.

## Derechos

Primero contenido propio. El material de terceros solo entra con licencia compatible y registrada; si la licencia es desconocida, la entidad queda sin usos permitidos. Un enlace no concede permiso para copiar.

## Cómo se ejecuta

```bash
lpdatasets contrib-report
lpdatasets contrib-verify --aporte ID --por "quién" --tipo ia --veredicto aprobado --nota "qué se comprobó"
lpdatasets contrib-approve --aporte ID --aprobado-por "nombre"
lpdatasets contrib-export --out .nucleo-compuesto
```

`contrib-export` escribe una copia del núcleo combinada con las piezas aprobadas; sin ninguna, es idéntica byte a byte al publicado. Su [informe](../informes/aportes-1-basico.md) lista cada pieza: 82 etiquetas de habilidades de Matemática, 60 aprobadas y 22 observadas.

Falta crear contenido: las skills y agentes previstos son `investigador-fuentes`, `autor-contenido`, `extractor-conocimiento` y `verificador-independiente`. Vacíos medidos y pasos: [plan de la fase 2](../PLAN_FASE_2.md), aprobado.

## Pruebas

`tests/test_contributions.py`: nada entra sin verificación y aprobación; quien escribe no verifica; un cambio en la pieza o en la fuente la hace caducar; las licencias no pueden ampliar usos; las etiquetas no sobrescriben la fuente ni se pisan; las respuestas ocultas siguen ocultas; los archivos conservan su huella y no salen de la carpeta; dos combinaciones dan los mismos bytes. `tests/test_published_contributions.py` comprueba lo publicado y que el núcleo no cambie.

Exigidas para el contenido (pasos 2.4 a 2.6): los ítems calculables se resuelven por cálculo.

## Métricas

Piloto de habilidades en Matemática, 2026-11-26. Dos lectores de IA asignaron por separado de 0 a 3 de los 10 objetivos de habilidad a cada una de las 83 clases; se fijó antes de comparar que solo entra lo que ambos asignaron. Criterio: la mayoría de las tareas de la clase, o su actividad central, exigen ejercerla.

| Resultado | Clases |
|---|---:|
| Asignaron lo mismo | 41 |
| Coinciden en parte | 19 |
| No coinciden (pieza observada, no entra) | 22 |
| Ninguno asignó | 1 |

El titular aprobó el 2026-11-26 las 60 piezas verificadas: 1.200 de las 1.660 tareas de Matemática tienen habilidades en la copia combinada. Habilidades que entran, por clases: modelar con sumas, restas y orden (g) 29, representar (i) 15, describir con lenguaje matemático (d) 11, comunicar relaciones (e) 6, a 3, h 3, j 1; b, c y f no entran en ninguna.

Clases con sus recursos disponibles sobre clases que los piden; OA con ítems de evaluación sobre 237; porcentaje revisado por una persona.

## Listo cuando

Cada vacío del [plan](../PLAN_1_BASICO.md) y cada hallazgo de etiquetas recibido está cubierto o declarado como no cubierto, y cada pieza nueva tiene autor, fuente y verificación.

## Límites

En el piloto, el autor leyó una muestra de cada clase (unas 8 de sus 20 tareas) y el verificador, todas: la regla de coincidencia protege contra asignar de más, no contra omitir. Son dos lecturas de IA que pueden compartir errores; ninguna persona revisó las etiquetas. Se asignan por clase, así que no cada tarea ejercita cada habilidad listada. Los dos lectores contaron como «modelar» (g) el cálculo sin situación; con un criterio más estricto, varias de esas clases quedarían sin etiqueta.

La capa comprueba forma, derechos y trazabilidad, **no si el contenido es correcto**: eso depende de quien verifica y de quien aprueba, y los nombres anotados no se autentican. La limpieza y las modalidades todavía leen el núcleo publicado, no el combinado.

El contenido creado con IA no tiene valor de revisión humana. No sustituye a docentes ni a educadores tradicionales.

## Decisiones

- 2026-11-26: al cerrar la fase 1, los hallazgos de etiquetas pasan a esta línea.
- 2026-11-26: lo nuevo vive en una capa de aportes de este repositorio; la fuente no se toca para agregarlo.
- 2026-11-26: el titular aprobó las 60 etiquetas en que coincidieron las dos lecturas; las 22 observadas no entran.
- 2026-11-26: el piloto de etiquetas y creación es en Matemática.
- 2026-11-26: las habilidades usan solo los objetivos de habilidad oficiales donde existen; en el resto se declaran sin cubrir.
- 2026-11-26: el titular o un docente revisa una muestra de cada piloto.
- 2026-11-26: los aportes se combinan en una copia; el núcleo publicado sigue siendo solo lo que vino de la fuente.
- 2026-11-26: solo entra una pieza verificada y aprobada por una persona sobre el texto actual.
- 2026-11-26: quien verifica no es quien escribió.
- 2026-11-26: las evaluaciones oficiales sirven de referencia; sus ítems no se copian.
