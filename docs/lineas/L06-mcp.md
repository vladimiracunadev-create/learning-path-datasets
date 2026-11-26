# L06 · Servidor MCP

- **Estado:** `PLANIFICADO`
- **Depende de:** L01 y L05

## Propósito

Ofrecer el contenido a asistentes compatibles con el Model Context Protocol, con consultas precisas y citas.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Listar asignaturas y OA de 1.º | docente | educativo | docente |
| Obtener una clase completa | docente | educativo | docente |
| Pedir ejercicios por OA y dificultad | docente | educativo | docente |
| Pedir material para acompañar en casa | familia | personal | familia |

## Entradas y salidas

Entrada: selección del núcleo e índice de L05. Salida: herramientas de solo lectura, recursos por identificador y plantillas de consulta.

## Contrato de datos

Herramientas previstas: `listar_oa`, `buscar`, `obtener_clase`, `ejercicios_por_oa`. Cada respuesta incluye identificador, marco, licencia y atribución.

## Derechos

El servidor se configura con un uso y un público, y solo carga lo que esa selección permite.

## Cómo se ejecuta

No implementado.

## Pruebas

Exigidas: cada herramienta con datos sintéticos, error claro ante identificadores inexistentes y ausencia de soluciones en la vista de estudiante.

## Métricas

Herramientas con prueba sobre herramientas publicadas; respuestas con cita (objetivo: todas); tiempo de respuesta local.

## Listo cuando

Un asistente compatible usa el servidor local y las pruebas confirman citas y permisos.

## Límites

Primero local y de solo lectura. Un servidor remoto exigiría autenticación y una decisión aparte.

## Decisiones

- 2026-11-26: tomar como base la especificación 2026-07-28 y confirmar su vigencia al implementar.
