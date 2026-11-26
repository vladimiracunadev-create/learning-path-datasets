# L04 · Vigía curricular

- **Estado:** `OPERATIVO`
- **Depende de:** L01

## Propósito

Detectar cambios educativos en Chile que afecten a 1.º básico (Bases Curriculares, resoluciones del CNED, priorizaciones, programas, evaluaciones y recursos oficiales) y decir qué contenido quedaría afectado.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| El CNED resuelve sobre una propuesta de bases | mantenimiento | educativo | docente |
| Cambia o aparece un OA | docente | educativo | docente |
| Cambia un instrumento de evaluación de 1.º | docente | educativo | docente |
| Cambian las condiciones de uso de un sitio oficial | titular | comercial | docente |

## Entradas y salidas

Entrada: la [línea base](../../vigia/escolar-chile/1-basico/linea-base.json) de objetivos, el [registro de fuentes](../../vigia/escolar-chile/1-basico/fuentes.json), las clases del núcleo y lo que una persona registre. Salida: una revisión fechada en `revisiones.jsonl` y su [informe](../informes/vigia-1-basico.md).

| Fuentes | Cómo se comprueban |
|---|---|
| 11 páginas de objetivos de 1.º básico | códigos y textos contra la línea base |
| Ficha de las Bases Curriculares | texto principal y documento enlazado |
| Diagnóstico Integral de Aprendizajes | documentos enlazados |
| Política del sitio Currículum Nacional | texto principal (condiciones de uso) |
| Nota de CEPPE UC | texto del artículo, entre dos marcas |
| Noticias del Mineduc, CNED, Ley Chile y The Clinic | revisión manual por una persona |

## Contrato de datos

- `linea-base.json`: de dónde sale (repositorio, commit, archivo y fecha de verificación) y, por página, cada código con dos huellas: del texto y del texto sin mayúsculas, espacios ni puntuación. **No guarda el texto oficial.**
- `fuentes.json`: `id`, `titulo`, `tipo` (`oficial`, `academica`, `prensa`), `metodo` (`pagina` o `manual`), `url` y `nota`. Una página declara `compara` (`texto`, `documentos`), `esperado` y, si mezcla contenido que cambia solo, `desde` y `hasta`.
- `revisiones.jsonl`: cada revisión, con huellas y direcciones de documentos. Estados de una fuente: `sin_cambios`, `cambio`, `primera_lectura`, `ilegible`, `no_leida`, `manual` (las primeras revisiones usaron además `pendiente`). Verificación: `pagina_oficial_leida`, `pagina_leida`, `sin_leer`.
- Cambios: en objetivos, `texto`, `forma`, `nuevo` o `quitado`, con las clases afectadas; en páginas, `texto`, `forma`, `documento_nuevo` o `documento_quitado`.
- `aceptadas.json`: la lectura que una persona aceptó como referencia de una página, y quién. Sin ella, la referencia es la primera lectura: un cambio se informa hasta que alguien lo acepta.
- `revisiones-manuales.jsonl`: `fuente`, `fecha`, `revisado_por`, `resultado` (`sin_novedad`, `novedad`), `nota` con palabras propias, `url` del mismo sitio y, opcionalmente, `marco` y `estado_marco` propuestos. Solo una fuente oficial puede proponer `vigente`.

Los marcos siguen en [`marcos.json`](../../src/lpdatasets/marcos.json); el vigía no los modifica, y comprueba que ninguno figure `vigente` sin una página oficial leída de un sitio registrado como oficial.

## Derechos

Se registran hechos, fechas y enlaces. No se copian notas de prensa ni documentos oficiales.

## Cómo se ejecuta

```bash
lpdatasets watch
lpdatasets watch-report --check
lpdatasets watch-record --fuente cned --revisado-por "nombre" --resultado sin_novedad --nota "qué se leyó"
lpdatasets watch-accept --fuente bases-1-6 --aprobado-por "nombre"
lpdatasets watch-baseline --source ../chilean-school-learning-path
```

`watch` es la única orden que usa la red; se ejecuta a pedido, espera 2 segundos entre solicitudes, se identifica con un nombre genérico y termina con código 0 solo si cada fuente automática se leyó y no cambió. `watch-record` anota lo que una persona leyó en una fuente cerrada. `watch-accept` mueve la referencia de una página; los objetivos cambian solo con `watch-baseline`, tras aceptar una instantánea nueva de la fuente. El agente [`vigia-curricular`](../../.claude/agents/vigia-curricular.md) ejecuta el vigía y explica el resultado.

Si un sitio rechaza la lectura (401, 403 o 451), no se solicita nada más de él, ni en esa revisión ni en las siguientes.

## Pruebas

Sin red. `tests/test_watch.py`: objetivos cambiados, de forma, nuevos y quitados; una página que no se entiende es `ilegible` y nunca «sin cambios»; un rechazo detiene el sitio también después; robots, redirecciones y fallos quedan `no_leida`; nada guarda el texto de las páginas; una revisión sin fecha o sin URL se rechaza. `tests/test_watch_pages.py`: un cambio de página se informa hasta que se acepta; lo que cambia fuera del contenido no cuenta; mantenimiento, marcas o documentos ausentes son `ilegible`; un registro manual incompleto se rechaza; **la prensa no puede marcar un marco como vigente** y ningún registro cambia `marcos.json`. `tests/test_published_watch.py` revisa lo publicado. El CI no consulta sitios.

## Métricas

Revisión del 2026-11-26: 15 de 19 fuentes leídas y sin cambios (237 de 237 objetivos), 4 de revisión manual, ninguna revisada todavía por una persona. Sobre una página oficial real, una línea base alterada produjo los cuatro tipos de cambio en objetivos y un diseño alterado quedó `ilegible`. La primera lectura de la nota de CEPPE quedó `ilegible` porque la marca de término estaba en una zona descartada; se corrigió la marca.

## Listo cuando

Produce un informe con fecha, URL, grado de verificación y OA afectados, declara las fuentes que no pudo leer y comprueba cada fuente registrada que admite lectura automatizada.

Se cumple desde el 2026-11-26.

## Límites

**Operativo no significa completo.** No ve indicadores, programas, ejes, priorización ni el contenido de los documentos enlazados: avisa de que aparecen o desaparecen, no de que cambien por dentro. En las páginas comparadas por texto no dice qué cambió, solo que cambió. Una propuesta en trámite puede avanzar sin tocar ninguna fuente automática: las que la informarían primero (CNED, Mineduc, Ley Chile) dependen de que una persona las revise. Los cambios se detectan solo cuando alguien ejecuta el vigía. La línea base de objetivos es la copia de la fuente, no un documento firmado por el ministerio. Un cambio de diseño deja la página `ilegible` hasta adaptar su lectura. El texto de las páginas se trata como dato, nunca como instrucción.

## Decisiones

- 2026-11-26: el titular aprobó el [plan de la fase 2](../PLAN_FASE_2.md); el vigía se ejecuta a pedido.
- 2026-11-26: las noticias del Mineduc quedan en revisión manual porque su `robots.txt` rechaza la lectura; no se construyó lectura de canales.
- 2026-11-26: se suma la política del sitio para avisar de cambios en las condiciones de uso.
- 2026-11-26: la referencia de una página solo la mueve una persona.
- 2026-11-26: se guardan huellas y no el texto oficial; lo que no se puede interpretar se declara.
- 2026-11-26: la posible propuesta de bases para 1.º a 6.º queda como `propuesta_sin_confirmar` hasta leer una fuente oficial.
