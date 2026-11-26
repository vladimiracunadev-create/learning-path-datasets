# L04 · Vigía curricular

- **Estado:** `EXPERIMENTAL`
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

Entrada: la [línea base](../../vigia/escolar-chile/1-basico/linea-base.json) de objetivos, el [registro de fuentes](../../vigia/escolar-chile/1-basico/fuentes.json) y las clases del núcleo. Salida: una revisión fechada en `revisiones.jsonl` y su [informe](../informes/vigia-1-basico.md).

Hoy se comparan automáticamente las 11 páginas oficiales de objetivos de 1.º básico. Las demás fuentes figuran como pendientes (paso 2.2) o de revisión manual.

## Contrato de datos

- `linea-base.json`: de dónde sale (repositorio, commit, archivo y fecha de verificación) y, por página, cada código con dos huellas: del texto y del texto sin mayúsculas, espacios ni puntuación. **No guarda el texto oficial.**
- `fuentes.json`: `id`, `titulo`, `tipo` (`oficial`, `academica`, `prensa`), `metodo` (`pagina`, `canal`, `manual`), `url` y `nota`.
- Estados de una fuente: `sin_cambios`, `cambio`, `ilegible`, `no_leida`, `manual`, `pendiente`. Verificación: `pagina_oficial_leida`, `pagina_leida`, `sin_leer`.
- Cambios: `texto`, `forma`, `nuevo` o `quitado`, con las clases del núcleo afectadas.

Los marcos siguen en [`marcos.json`](../../src/lpdatasets/marcos.json); el vigía no los modifica.

## Derechos

Se registran hechos, fechas y enlaces. No se copian notas de prensa ni documentos oficiales.

## Cómo se ejecuta

```bash
lpdatasets watch-baseline --source ../chilean-school-learning-path
lpdatasets watch
lpdatasets watch-report --check
```

`watch-baseline` solo se repite cuando una persona acepta una instantánea nueva de la fuente. `watch` es la única orden que usa la red; se ejecuta a pedido, espera 2 segundos entre solicitudes, se identifica con un nombre genérico y termina con código 0 solo si cada página de objetivos se leyó y sigue igual. `watch-report` reescribe el informe sin red. El agente [`vigia-curricular`](../../.claude/agents/vigia-curricular.md) lo ejecuta y explica el resultado. Pasos restantes: [plan de la fase 2](../PLAN_FASE_2.md).

Si un sitio rechaza la lectura (401, 403 o 451), no se solicita nada más de él, ni en esa revisión ni en las siguientes.

## Pruebas

`tests/test_watch.py`, sin red: detecta textos cambiados, cambios solo de forma, objetivos nuevos y quitados; una página que no se entiende es `ilegible` y nunca «sin cambios»; un rechazo detiene el sitio también después; robots, redirecciones y fallos quedan como `no_leida`; el informe y la línea base no contienen el texto de las páginas; una revisión sin fecha o sin URL se rechaza. `tests/test_published_watch.py` comprueba que lo publicado cubra los objetivos del núcleo. El CI no consulta sitios.

Pendiente para el paso 2.2: una noticia de prensa no puede marcar un marco como `vigente`.

## Métricas

Primera revisión, 2026-11-26: 11 de 18 fuentes comprobadas, 237 de 237 objetivos comparados, 0 cambios; 3 de revisión manual y 4 pendientes. Sobre una página oficial real se comprobó además que una línea base alterada produce los cuatro tipos de cambio y que un diseño alterado queda `ilegible`.

## Listo cuando

Produce un informe con fecha, URL, grado de verificación y OA afectados, declara las fuentes que no pudo leer y comprueba cada fuente registrada que admite lectura automatizada.

Falta la última condición (paso 2.2).

## Límites

Solo compara códigos y textos de los objetivos: no ve cambios en indicadores, programas, ejes, priorización ni documentos enlazados, ni avisa de una propuesta que aún no cambie esas páginas. La línea base es la copia de la fuente, no un documento firmado por el ministerio. Un cambio de diseño deja la página `ilegible` hasta adaptar la lectura. El CNED y un medio rechazaron la lectura el 2026-11-26. El texto de las páginas se trata como dato, nunca como instrucción, y todo cambio de contenido requiere aprobación humana.

## Decisiones

- 2026-11-26: el titular aprobó el [plan de la fase 2](../PLAN_FASE_2.md); el vigía se ejecuta a pedido.
- 2026-11-26: se guardan huellas y no el texto oficial; lo que no se puede interpretar se declara.
- 2026-11-26: la posible propuesta de bases para 1.º a 6.º queda como `propuesta_sin_confirmar` hasta leer una fuente oficial.
