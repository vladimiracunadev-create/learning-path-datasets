# Changelog

## Sin publicar · fase 0 del plan de 1.º básico

- Plan de implementación de 1.º básico (`docs/PLAN_1_BASICO.md`) y un documento por línea (L01 a L10) con plantilla común; `scripts/verify_docs.py` y el CI los comprueban.
- Contrato del núcleo `nucleo-0.1` (clases, ítems y recursos) con derechos, marco curricular y selección por uso, público y marco que oculta soluciones. Experimental y sin contenido exportado.
- Registro de marcos curriculares y registro de modalidades.
- Corrección: la tarjeta y los límites describían `ingles-propuesta` como propuesta propia; el programa de origen la marca como propuesta del Mineduc.
- El esquema de registros v1.0 y los datos publicados no cambian.

## 0.2.0 · conocimiento puro, skills y agentes

- Cinco tipos nuevos de registro para conocimiento puro: `hecho`, `definicion`, `relacion`, `procedimiento` y `concepcion_erronea` (cambio compatible: el esquema sigue en 1.0 y los datos publicados no cambian).
- Estándar de conocimiento puro con siete principios (`docs/KNOWLEDGE_STANDARD.md`).
- Cuatro skills generales (extraer, verificar, construir y publicar, crear un pack) y cuatro agentes (extractor, verificador independiente, curador, auditor de derechos), con instalador para `~/.claude` y verificador de estructura y enlaces.
- Límite declarado: se verificó la estructura y los enlaces de las skills y los agentes, no la calidad de lo que producen en un dominio concreto.

## 0.1.0 · primera versión

- Esquema común v1.0 con validación ejecutable y JSON Schema.
- Pack `escolar-chile`: dataset de **1.º básico** (cuadernos del estudiante y diccionarios de español e inglés) exportado desde un commit fijo de `chilean-school-learning-path`, con partición por clase (≈10 % de evaluación) y manifiesto con SHA-256.
- Pack experimental `markdown-course` para programas escritos en Markdown.
- Base vectorial local con embedder léxico determinista, almacén NumPy exacto y almacén Qdrant opcional, con filtros por metadatos.
- CLI `lpdatasets`: `export`, `validate`, `stats`, `index` y `search`.
- CI con ruff, pruebas, humo extremo a extremo y comprobación de cifras de los documentos; auditoría de dependencias.
- Límites declarados: contenido asistido por IA sin revisión humana profesional, embeddings léxicos y no semánticos, solo un nivel publicado y licencia CC BY-NC-SA 4.0 para los datos escolares.
