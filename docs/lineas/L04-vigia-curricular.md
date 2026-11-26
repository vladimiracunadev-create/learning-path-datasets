# L04 · Vigía curricular

- **Estado:** `PLANIFICADO`
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

Entrada: lista de fuentes con su tipo (oficial o prensa). Salida: informe fechado con URL, qué cambió, grado de verificación y OA afectados.

## Contrato de datos

Registro de marcos en [`marcos.json`](../../src/lpdatasets/marcos.json). Estados: `vigente`, `propuesta_sin_confirmar`, `propuesta_no_obligatoria`, `no_aplica`. Verificación: `pagina_oficial_leida`, `resumen_de_buscador`, `no_aplica`.

## Derechos

Se registran hechos, fechas y enlaces. No se copian notas de prensa ni documentos oficiales.

## Cómo se ejecuta

No implementado. Agente previsto: `vigia-curricular`, a pedido y, más adelante, programado.

## Pruebas

Exigidas: un informe sin URL o sin fecha se rechaza; una noticia de prensa no puede marcar un marco como `vigente`.

## Métricas

Fuentes revisadas sobre fuentes registradas; fuentes que bloquearon la lectura; días desde la última revisión.

## Listo cuando

Produce un informe con fecha, URL, grado de verificación y OA afectados, y declara las fuentes que no pudo leer.

## Límites

Algunos sitios bloquean la lectura automatizada (el 2026-11-26 ocurrió con el CNED y con un medio): esas fuentes se marcan para revisión manual. El vigía no modifica contenido; todo cambio requiere aprobación humana. El texto de las páginas se trata como dato, nunca como instrucción.

## Decisiones

- 2026-11-26: la posible propuesta de bases para 1.º a 6.º queda como `propuesta_sin_confirmar` hasta leer una fuente oficial.
