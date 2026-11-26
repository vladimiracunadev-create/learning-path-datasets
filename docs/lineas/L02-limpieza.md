# L02 · Limpieza de datos

- **Estado:** `PLANIFICADO`
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

Entrada: entidades del núcleo (y, como línea base, el dataset v1.0). Salida: informe de hallazgos y propuesta de cambios; nunca edición silenciosa.

## Contrato de datos

Cada hallazgo guarda identificador de la entidad, regla, evidencia, acción propuesta y quién la aprobó.

## Derechos

No cambia licencias ni procedencia. No eleva el estado de revisión sin una persona identificable que haya revisado.

## Cómo se ejecuta

No implementado.

## Pruebas

Exigidas: un caso sintético por cada regla y la comprobación de que la limpieza es determinista.

## Métricas

Línea base del dataset v1.0 al 2026-11-26: 282 pares repetidos; 27 registros de evaluación idénticos a uno de entrenamiento; 203 de 1.797 registros de evaluación con la entrada presente en entrenamiento; 525 entradas con respuestas distintas; 2.499 salidas de 3 caracteres o menos; 8.518 registros sin `dificultad`. Las salidas cortas y parte de los conflictos pueden ser legítimos.

## Listo cuando

Hay un informe antes y después, cada hallazgo está resuelto o aceptado con motivo y no queda ningún registro de evaluación idéntico a uno de entrenamiento.

## Límites

Las reglas encuentran problemas de forma; los errores pedagógicos requieren un lector.

## Decisiones

- 2026-11-26: el agente `limpiador-datos` propondrá cambios y no borrará sin registro.
