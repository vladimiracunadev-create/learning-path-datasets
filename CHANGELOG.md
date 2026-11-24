# Changelog

## 0.1.0 · primera versión

- Esquema común v1.0 con validación ejecutable y JSON Schema.
- Pack `escolar-chile`: dataset de **1.º básico** (cuadernos del estudiante y diccionarios de español e inglés) exportado desde un commit fijo de `chilean-school-learning-path`, con partición por clase (≈10 % de evaluación) y manifiesto con SHA-256.
- Pack experimental `markdown-course` para programas escritos en Markdown.
- Base vectorial local con embedder léxico determinista, almacén NumPy exacto y almacén Qdrant opcional, con filtros por metadatos.
- CLI `lpdatasets`: `export`, `validate`, `stats`, `index` y `search`.
- CI con ruff, pruebas, humo extremo a extremo y comprobación de cifras de los documentos; auditoría de dependencias.
- Límites declarados: contenido asistido por IA sin revisión humana profesional, embeddings léxicos y no semánticos, solo un nivel publicado y licencia CC BY-NC-SA 4.0 para los datos escolares.
