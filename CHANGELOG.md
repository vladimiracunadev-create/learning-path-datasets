# Changelog

## Sin publicar · fase 1 del plan de 1.º básico

- Núcleo de 1.º básico en `nucleo/`: 887 clases, 16.386 ítems y 1.653 recursos, con 147 clases excluidas y declaradas. Comandos `core-export` y `core-validate`.
- El texto oficial de los OA citado por las experiencias integradas se sustituye por su código.
- Informe de limpieza (`clean-report`) con 1.140 hallazgos pendientes y agente `limpiador-datos`.
- Propuestas de limpieza por lote (`clean-proposals`) y registro de aprobaciones (`clean-approve`).
- Aprobados por el titular los 10 lotes de aceptación: 1.042 hallazgos aceptados y 98 pendientes. El contenido no cambia.
- Correcciones propuestas para 28 preguntas (`clean-corrections`), con dos rondas de verificación ciega. El titular aprobó 24.
- Las 24 se aplicaron en la fuente (commit `3fd976d5`) y se volvieron a exportar el núcleo y el dataset v1.0: cambian esos 24 registros y el commit de origen. 16 hallazgos quedan resueltos y archivados; 15 (11 nuevos y 4 que cambiaron de lote) esperan aprobación y hay 93 pendientes. Orden `clean-mark-applied`.
- El titular aprobó esos 15: 1.057 hallazgos aceptados y 78 pendientes.
- Hoja de dudas (`clean-doubts`): 39 recomendaciones y textos propuestos, con dos rondas de verificación ciega.
- El titular aprobó todas las recomendaciones (`clean-resolve-doubts`): 11 hallazgos mantenidos y 35 textos aprobados, sin aplicar. 1.068 aceptados y 67 pendientes.
- `clean-mark-applied` cierra lo resuelto, archiva decisiones con sus hallazgos y retira aceptaciones sobre textos cambiados; lote `texto-aplicado`.
- Los 35 textos se aplicaron en la fuente (commit `b3647111`) y se volvieron a exportar el núcleo y el dataset v1.0: cambian esos 35 registros y el commit de origen. 1.131 hallazgos: 1.066 aceptados, 19 resueltos y 46 pendientes, 7 de ellos por aprobar.
- El titular aprobó esos 7: 1.073 hallazgos aceptados, 19 resueltos y 39 pendientes, todos de etiquetas (L03) o cruces (L08).
- Fase 1 cerrada: el criterio sobre cruces pasa a L08 y las etiquetas quedan en L03. L02 sigue experimental, sin revisión humana.
- Plan de la fase 2 (`docs/PLAN_FASE_2.md`), pendiente de aprobación; no incluye código nuevo.
- Plan de la fase 2 aprobado. Vigía curricular (paso 2.1): órdenes `watch-baseline`, `watch` y `watch-report`, agente `vigia-curricular`; primera revisión con 237 objetivos sin cambios.
- Vigía curricular (paso 2.2): páginas sin objetivos, órdenes `watch-record` y `watch-accept`, comprobación de marcos vigentes; 15 de 19 fuentes leídas. L04 pasa a operativo.
- Capa de aportes (paso 2.3): órdenes `contrib-report`, `contrib-verify`, `contrib-approve` y `contrib-export`; vocabulario de 21 habilidades oficiales. Sin piezas todavía.
- Paso 2.4 (por aprobar): habilidades solo en tareas y dificultad solo en ejercicios cerrados; la limpieza lee los aportes; orden `clean-mark-contributed`; 82 etiquetas de Matemática, 60 verificadas por doble lectura. 49 hallazgos pendientes.
- Documento de método (`docs/METODO.md`): lo realizado, sus fundamentos, cambios de criterio y cómo reutilizarlo; el CI exige que nombre cada módulo, script, orden, skill y agente.
- Campo opcional `idioma` en el contrato `nucleo-0.1`.
- El lector de la fuente busca el archivo de cada OA una sola vez; el dataset v1.0 no cambia.

## Sin publicar · fase 0 del plan de 1.º básico

- Plan de implementación de 1.º básico (`docs/PLAN_1_BASICO.md`) y un documento por línea (L01 a L10) con plantilla común; `scripts/verify_docs.py` y el CI los comprueban.
- Contrato del núcleo `nucleo-0.1` (clases, ítems y recursos) con derechos, marco curricular y selección por uso, público y marco que oculta soluciones. Experimental y sin contenido exportado.
- Registro de marcos curriculares y registro de modalidades.
- Esquema SVG de lo que se construye, generado desde `lineas.json` y comprobado en el CI.
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
