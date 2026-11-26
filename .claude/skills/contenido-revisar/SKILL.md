---
name: contenido-revisar
description: >-
  Revisa, evalúa y corrige los contenidos de un programa de aprendizaje (explicaciones, ejemplos, ejercicios,
  soluciones, glosarios y guías) sin romper la lógica del repositorio: busca errores, respuestas incoherentes,
  datos faltantes, soluciones regaladas y contenido fuera de nivel, redacta correcciones, las hace verificar por
  otro contexto, pide aprobación y las aplica en la fuente. Úsalo cuando el usuario pida "revisa los contenidos",
  "busca errores en el curso", "corrige las preguntas", "evalúa la calidad del material" o "mejora los contenidos
  sin romper el repositorio". Sirve para cualquier materia y nivel.
---

# Revisar y corregir contenidos

El [prompt maestro](prompt-maestro.md) es el procedimiento completo, con fases, reglas y puntos de detención. Úsalo así o entrégalo a otra sesión. El [catálogo de defectos](catalogo-defectos.md) define qué buscar. Si el repositorio es Trayectoria Escolar Chile, parte de su [perfil](perfil-trayectoria-escolar-chile.md); para otro, escribe su perfil en la fase 0.

## Quién hace qué

| Paso | Agente | Límite |
|---|---|---|
| Entender el repositorio y buscar defectos | `auditor-contenidos` | no edita |
| Redactar correcciones y aplicarlas | `corrector-contenidos` | aplica solo lo aprobado |
| Verificar a ciegas | `verificador-independiente` | contexto distinto al que redactó |
| Decidir | una persona | aprueba cada texto y cada cambio en el repositorio |

## Recorrido

1. **Fase 0.** Entiende fuente, salidas generadas, funciones que componen texto, validadores y sus puntos ciegos, y mide la línea base.
2. **Alcance.** Una asignatura o módulo y un nivel; di el volumen y el costo antes de empezar.
3. **Buscar y evaluar.** Comprobaciones automáticas y lectura completa, resolviendo antes de mirar la respuesta.
4. **Corregir.** Cambio mínimo, mismo objetivo, nivel e identificador.
5. **Verificar a ciegas**, corregir lo observado y marcar lo que quede sin releer.
6. **Aprobar** con antes y después.
7. **Aplicar** por posición estructural, regenerar dos veces, explicar cada diferencia y publicar con autorización.
8. **Informar** cobertura, resultados, errores propios y pendientes.

## Entregables

- `hallazgos`: unidad, pieza, categoría, certeza, cita y motivo.
- `correcciones`: pieza, antes, después, qué cambia, lecturas y aprobación.
- `informe`: cobertura, no corregido con su motivo y lo que no se verificó.

## Límites

Es un procedimiento para un asistente: no garantiza que encuentre los defectos ni sustituye a una persona especialista en la materia y el nivel.
