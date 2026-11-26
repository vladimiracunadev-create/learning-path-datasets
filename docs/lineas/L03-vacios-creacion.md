# L03 · Vacíos y creación de contenido

- **Estado:** `PLANIFICADO`
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

## Entradas y salidas

Entrada: vacíos medidos sobre el núcleo y fuentes con licencia conocida. Salida: recursos e ítems nuevos, más una ficha de cada fuente consultada.

## Contrato de datos

Entidades `recurso` e `item` del núcleo. Todo recurso que no sea texto lleva `descripcion` como texto alternativo.

## Derechos

Primero contenido propio. El material de terceros solo entra con licencia compatible y registrada; si la licencia es desconocida, la entidad queda sin usos permitidos. Un enlace no concede permiso para copiar.

## Cómo se ejecuta

No implementado. Skills y agentes previstos: `investigador-fuentes`, `autor-contenido`, `extractor-conocimiento` y `verificador-independiente`.

## Pruebas

Exigidas: ninguna pieza sin fuente, derechos y verificación; los ítems calculables se resuelven por cálculo.

## Métricas

Clases con sus recursos disponibles sobre clases que los piden; OA con ítems de evaluación sobre 237; porcentaje revisado por una persona.

## Listo cuando

Cada vacío del [plan](../PLAN_1_BASICO.md) está cubierto o declarado como no cubierto, y cada pieza nueva tiene autor, fuente y verificación.

## Límites

El contenido creado con IA no tiene valor de revisión humana. No sustituye a docentes ni a educadores tradicionales.

## Decisiones

- 2026-11-26: quien verifica no es quien escribió.
- 2026-11-26: las evaluaciones oficiales sirven de referencia; sus ítems no se copian.
