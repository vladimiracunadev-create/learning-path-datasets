# L09 · Ajuste de modelos

- **Estado:** `PLANIFICADO`
- **Depende de:** L08 y L05

## Propósito

Comprobar si ajustar un modelo abierto pequeño mejora el estilo, el nivel y el formato de sus respuestas para 1.º básico frente a usarlo sin ajuste o con recuperación.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Explicar en lenguaje adecuado a 6 años | quien entrena | educativo | docente |
| Producir ejercicios con el formato del proyecto | quien entrena | educativo | docente |
| Comparar modelo base, base con RAG y ajustado | quien evalúa | educativo | docente |

## Entradas y salidas

Entrada: datos de L08 y un modelo base con licencia revisada. Salida: informe comparativo y configuración reproducible. Los pesos no se publican desde este repositorio sin una decisión aparte.

## Contrato de datos

Formato `messages` con partición por OA. El informe registra modelo, versión, semilla, parámetros y SHA-256 de los datos.

## Derechos

Los datos son CC BY-NC-SA 4.0. Si un modelo entrenado cuenta como adaptación o uso comercial es una cuestión legal que este repositorio no resuelve.

## Cómo se ejecuta

No implementado. Requiere una GPU adecuada, local o en la nube, por decidir.

## Pruebas

Exigidas: línea base medida antes de ajustar y evaluación sobre contenido no usado en el entrenamiento.

## Métricas

Exactitud en ítems calculables, adecuación al nivel según rúbrica revisada por una persona y errores introducidos por el ajuste.

## Listo cuando

Existe la comparación de las tres variantes con los mismos casos y una recomendación sustentada, aunque sea no ajustar.

## Límites

Un modelo aprende como verdad los errores de los datos, que hoy no tienen revisión humana. No se plantea entrenar un modelo desde cero.

## Decisiones

- 2026-11-26: los hechos se apoyan en recuperación; el ajuste busca estilo y formato.
