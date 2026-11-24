# Hoja de ruta

Lo que sigue es una intención, no una promesa de fechas. Cada punto se incorpora cuando tiene pruebas y documentación.

## Próximo

1. **Los otros once niveles escolares** (2.º básico a 4.º medio) del pack `escolar-chile`, un nivel por vez, con su propia tarjeta de cambios.
2. **Packs para otros programas de aprendizaje** del ecosistema, probando primero el adaptador genérico `markdown-course` sobre cada repositorio real y escribiendo un adaptador propio donde haga falta (ejercicios, rúbricas, glosarios).
3. **Etiquetado de habilidades** (`habilidades`) a partir de los objetivos de aprendizaje.

## Después

4. **Embeddings semánticos** como embedder opcional, con una prueba de calidad de recuperación y la medición de su costo.
5. **Conjuntos de evaluación más estrictos**: partición por objetivo de aprendizaje y detección de contenido casi duplicado entre `train` y `eval`.
6. **Revisión humana por muestreo**, con un campo que registre quién revisó qué y cuándo, y estados de revisión reales en el manifiesto.
7. **Versiones publicadas** (releases) con los JSONL y los índices como activos descargables, fuera de Git.
8. **Formatos de entrenamiento**: exportar a conversación (`messages`) y a pares instrucción-respuesta desde el mismo esquema.

## Fuera de alcance

Entrenar o distribuir modelos; reemplazar la revisión pedagógica; datos con información personal.
