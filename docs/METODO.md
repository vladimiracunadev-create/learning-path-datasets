# Método, decisiones y aprendizajes

Registro de **qué se hizo, por qué, cómo se comprobó y qué cambió en el camino**, para reutilizarlo con otros tipos de datos. El caso trabajado es 1.º básico; cifras al **2026-11-26**.

Regla de mantenimiento: cada avance actualiza este documento en el mismo cambio. `tests/test_method.py` falla si aparece un módulo, un script o una orden que aquí no se mencione; **no** comprueba que la explicación sea correcta o suficiente.

Documentos que complementa: [plan](PLAN_1_BASICO.md), [líneas](lineas/README.md) (detalle y estado de cada una), [contrato del núcleo](CORE_CONTRACT.md) y [límites y derechos](LIMITS_AND_RIGHTS.md).

## 1. Qué se pidió

El contenido de aprendizaje debe servir de varias formas (dataset, RAG, MCP, entrenamiento o ajuste de modelos, skills y agentes, y formas futuras), con el alcance actual **solo en 1.º básico**, buscando y creando lo que falte, documentando cada línea y subiendo cada avance a `main` en verde.

## 2. Principios y su fundamento

| Principio | Por qué | Dónde se hace cumplir |
|---|---|---|
| El centro es el contenido; el dataset es una salida | pares sueltos de pregunta y respuesta no sirven para recuperar clases completas ni para futuras formas de uso | contrato del núcleo, `select()` |
| Cada pieza lleva marco, derechos, revisión y procedencia | permite cualquier uso sin perder las condiciones ni mezclar bases vigentes con propuestas | `core.py`, `schema/core.schema.json` |
| Una sola puerta de salida | si cada modalidad leyera los archivos, cada una tendría que repetir permisos y ocultar soluciones | `modalities.py`, `select()` |
| Fallar antes que adivinar | una separación dudosa entre cuaderno y solucionario revelaría respuestas | el adaptador detiene la exportación |
| Proponer, no modificar | una regla automática se equivoca; borrar en silencio no se puede auditar | limpieza, propuestas y correcciones |
| Decide una persona | los agentes de IA no sustituyen la revisión | `clean-approve`, `clean-approve-corrections` |
| Quien verifica no es quien escribió | el autor confirma sus propios supuestos | lecturas ciegas por otros agentes |
| Decir el grado de verificación | un resumen de buscador no es una fuente leída | `marcos.json`, plan |
| Salidas deterministas y comprobadas en CI | un informe desactualizado engaña | órdenes `--check` en el CI |

## 3. Lo realizado

### 3.1 Diagnóstico antes de construir

- **Qué:** lectura de este repositorio y de la fuente, y medición de cobertura, duplicados y cruces.
- **Por qué:** saber qué había antes de prometer salidas nuevas.
- **Resultado:** 1.º básico tiene 237 OA y 1.034 entradas de clase (691 desarrolladas y 343 integradas). El dataset v1.0 exportaba 562; 129 desarrolladas están excluidas (Pueblos Originarios). El lector de la fuente no admite 3.º y 4.º medio, que usan otras carpetas.
- **Límite:** las mediciones por palabras clave solo indican dónde mirar.

### 3.2 Base documentada (commit `de82c2f`)

- **Qué:** plan, diez líneas con una plantilla común, contrato `nucleo-0.1`, marcos curriculares y registro de modalidades.
- **Por qué:** fijar el contrato antes de producir datos permite sumar usos sin rediseñar.
- **Cómo se comprobó:** el validador de Python y el JSON Schema se prueban con los mismos ejemplos válidos e inválidos; una modalidad ficticia confirma que recibe datos filtrados; `verify_docs.py` rechaza líneas sin documento o sin secciones.
- **Descartado:** cambiar el esquema v1.0 del dataset publicado; el núcleo es independiente.

### 3.3 Esquema visual (commit `d0393d8`)

- **Qué:** `docs_diagram.py` dibuja el flujo y el estado de cada fase desde `lineas.json`.
- **Por qué:** un dibujo hecho a mano se desactualiza; generado y comprobado, no.

### 3.4 Núcleo de 1.º básico (commit `05434b3`)

- **Qué:** `core-export` produce 887 clases, 16.386 ítems y 1.653 recursos (guías docentes, cuadernos y orientaciones por OA); `core-validate` los comprueba.
- **Cómo:** las clases salen del catálogo; los ítems reutilizan el lector del dataset v1.0 para que concilien por identificador; cada ficha se separa en planificación, cuaderno y solucionario.
- **Cómo se comprobó:** 887 representadas más 147 excluidas suman 1.034; los 16.386 ítems coinciden en identificador y contenido con el dataset; dos exportaciones dieron los mismos bytes; el estudiante no recibe guías ni respuestas de ejercicios.
- **Texto oficial:** las experiencias integradas citaban literalmente los OA. Se sustituyeron tramos de seis o más palabras por el código (521 entidades, 1.519 tramos). En el resto, coincidencias de ocho o más palabras se marcan sin alterar. También se comprobó que los 6 OA de menos de 8 palabras no aparecieran completos.
- **Decisión:** versionar el núcleo en Git (unos 31 MB, 2,5 MB comprimido) para validarlo en CI; con más niveles habrá que publicarlo aparte.

### 3.5 Reglas de limpieza (mismo commit)

- **Qué:** `clean-report` aplica once reglas; primer resultado, 1.140 hallazgos.
- **Por qué:** medir antes de corregir y dejar cada hallazgo con identificador estable.
- **Cómo se comprobó:** un caso sintético por regla y resultado independiente del orden.
- **Límite:** son reglas de forma; `recurso_ausente` dio 0, lo que no demuestra que no falten recursos.

### 3.6 Propuestas por lote (commit `b8725b9`)

- **Qué:** `clean-proposals` repartió los hallazgos en lotes: 1.042 aceptar, 63 corregir y 35 decidir.
- **Por qué:** 1.140 decisiones una a una no son practicables; por lotes sí, si cada lote declara cómo se clasificó (regla o lectura) y lo no leído nunca se propone aceptar.
- **Cómo:** reglas generales más juicios individuales guardados en `limpieza/revision.json`.
- **Segunda lectura ciega (136 casos):** confirmó las 9 correcciones propuestas entonces; de 116 casos que se daban por buenos objetó 15 (3 defectos y 12 dudas). Se aplicaron y se endurecieron dos reglas.
- **Límite:** los lotes finales no tuvieron tercera lectura.

### 3.7 Aprobación de lotes (commit `59936ff`)

El titular aprobó los 10 lotes de aceptación: 1.042 hallazgos aceptados y 98 pendientes. Aceptar significa conservar; no es revisión pedagógica y el estado de revisión de los datos no cambia.

### 3.8 Correcciones (commit `a23fc61`)

- **Qué:** redacción nueva de 27 preguntas y una más detectada al redactar.
- **Cómo:** se procuró cambiar lo mínimo (en algunas hubo que mover el foco de la pregunta); `clean-corrections` simula cada cambio en una copia y rechaza duplicados, conflictos o respuestas entregadas por el cuaderno.
- **Lecturas ciegas:** primera ronda, 19 sin observaciones, 6 por corregir y 3 dudas; segunda, sobre las 9 cambiadas, 5 sin observaciones, 1 por corregir y 3 dudas. La última corrección aplicada no tuvo otra lectura.
- **Descartado:** seguir iterando sin fin; lo que quedó discutible se entrega a la persona marcado como duda.

### 3.9 Aprobación de correcciones (commit `797d7e2`)

- **Qué:** `clean-approve-corrections` registró 24 aprobadas por el titular; 4 con duda abierta quedan sin aprobar.
- **Por qué por fila y con huella:** si un texto aprobado cambia, la aprobación deja de valer.
- **Dónde se cambia:** el contenido nace en la fuente (módulos `student_content_*.py`), así que aplicar exige autorización para ese repositorio.

### 3.10 Aplicación en la fuente y reexportación

- **Qué:** con autorización del titular, las 24 se escribieron en 17 módulos de la fuente (commit `3fd976d5`) y aquí se regeneraron núcleo, dataset v1.0 e informes.
- **Cómo:** se localizó cada terna pregunta, respuesta y razón y se exigió que apareciera una sola vez antes de escribir; se usó el entorno del propio proyecto, con sus versiones fijadas; se regeneró y validó en el orden de su CI.
- **Cómo se comprobó:** en la fuente, 111 pruebas, 64 PDF, segunda generación sin diferencias y las 46 líneas cambiadas en las fichas explicadas por las correcciones; sus tres workflows terminaron bien. Aquí, el dataset cambia exactamente en esos 24 registros (además del commit de origen) y coincide con el núcleo.
- **Efecto en la limpieza:** 16 hallazgos resueltos, 11 nuevos (el resto de grupos anteriores) y 4 que cambiaron de lote porque su grupo conserva la pregunta corregida; los 15 proponen aceptar y esperan aprobación. Se simuló antes de exportar para saber si alguna aprobación quedaba huérfana: ninguna.
- **Límite:** el cambio en la fuente no es revisión profesional.

## 4. Cambios de criterio en el camino

| Antes | Después | Motivo |
|---|---|---|
| El dataset en el centro | núcleo con salidas derivadas | se pidieron usos variados y futuros |
| Cifras de la fuente que no cuadraban (14.826 y 12.096 clases) | en 1.º básico cuadran: 1.034 = 691 + 343 | las integradas son entradas sin cuaderno propio |
| «Inglés es una propuesta propia» | propuesta del Mineduc | así la marca el catálogo de la fuente |
| 282 duplicados y 525 conflictos medidos al inicio | 151 y 328 hallazgos | ahora se agrupa por asignatura y tipo |
| Contrato sin idioma | campo opcional `idioma` | el dataset lo necesita; un campo opcional no rompe nada |
| Toda elección «¿A o B?» es legítima | se lee si lo afirmado antes ya dice la respuesta | pasaban preguntas autorrespondidas |
| Respuesta presente en el cuaderno equivale a enseñanza | si está en un ejemplo o error comentado, se lee | un ejemplo respondía la misma pregunta |
| Juicios por ítem compartidos entre reglas | un juicio por regla e ítem | un defecto de enunciado no es un defecto de cuaderno |
| Aprobación única del documento de correcciones | aprobación por fila ligada al texto | permitir aprobar una parte |
| La respuesta nueva no puede aparecer en el cuaderno | puede estar en su propio enunciado | las preguntas de elección la contienen |
| El dataset v1.0 no se modifica | se regenera cuando cambia el contenido de la fuente | publicar defectos ya corregidos no tiene sentido; los cruces siguen para la versión siguiente |
| Un hallazgo corregido simplemente desaparece | se archiva con el commit que lo resolvió | permite mostrar antes y después |

## 5. Trampas encontradas y qué hacer con datos nuevos

| Trampa | Cómo se detectó | Qué hacer |
|---|---|---|
| Texto de terceros copiado dentro de contenido propio | comparación de tramos de palabras con la redacción oficial | comparar siempre antes de publicar; decidir omitir, citar o excluir |
| Soluciones y notas docentes después del cuaderno | lectura del final de una ficha completa | leer unidades enteras antes de escribir el adaptador |
| Regla que acepta de más | segunda lectura ciega | medir cada regla con casos leídos y declarar cómo se clasificó |
| Cambio de género que esconde la respuesta («rígida», «Rígido») | al redactar; **la regla aún no lo detecta** | no suponer que la búsqueda literal cubre variantes |
| Regla con cero hallazgos | lectura de ejemplos | informar el alcance de la regla, no «no hay problemas» |
| Cruces entre entrenamiento y evaluación pese a partir por clase | comparar entradas entre particiones | partir por una unidad mayor y filtrar entradas compartidas |
| Misma palabra con definiciones distintas | regla de conflictos y lectura | entregar siempre la pieza con su contexto |
| Sitios que bloquean la lectura automatizada | el CNED y un medio respondieron con rechazo | marcar «sin confirmar» y revisar a mano |
| Aplicar un cambio altera la composición de los grupos | simulación antes de exportar | esperar identificadores nuevos y pedir su decisión; no heredar la anterior |
| Regenerar un proyecto ajeno con otras versiones de librerías | comparación con sus versiones fijadas | usar el entorno del propio proyecto |
| Condiciones de uso contradictorias | política del sitio frente a la etiqueta de un recurso | registrarlo como no resuelto; decide quien tiene los derechos |

## 6. Cómo aplicarlo a otro tipo de datos

| Paso | Entregable | Se reutiliza | Hay que escribir o decidir |
|---|---|---|---|
| 1. Inventario | unidades, cifras y exclusiones | método de medición | qué es una unidad en ese dominio |
| 2. Derechos | licencia por tipo de contenido | tabla de usos, `allows_use` | licencias nuevas y texto de terceros |
| 3. Marco y público | entrada en `marcos.json` | validador | marco del dominio y públicos (hoy escolares) |
| 4. Adaptador | entidades del núcleo | `core.py`, `core_build.py` | lectura de la fuente y separación de soluciones |
| 5. Conciliación | representadas más excluidas suman el total | manifiesto y `core-validate` | motivos de exclusión; otra salida con la que cruzar |
| 6. Limpieza | hallazgos | duplicados, conflictos, cruces, etiquetas | reglas propias del contenido e idioma |
| 7. Lectura | juicios y muestra ciega | formato de revisión y protocolo | criterios de calidad y muestra declarada |
| 8. Propuestas y aprobación | lotes y decisiones | mecanismo de aprobación | textos y lotes del dominio |
| 9. Correcciones | antes y después aprobados y aplicados | simulación, huella y registro de lo aplicado | comprobaciones del dominio y cómo se cambia la fuente |
| 10. Modalidades | salidas | `run()` | la modalidad y su documento de línea |

Protocolo de lectura ciega usado: archivo solo con las preguntas y su contexto; el lector resuelve y guarda sus respuestas antes de abrir las propuestas; veredicto por caso; se mezclan casos con defecto conocido como control, y por eso las tasas de la muestra no se extrapolan.

## 7. Qué es genérico y qué es específico

| Pieza | Alcance | Detalle |
|---|---|---|
| `schema.py`, `build.py` | casi genéricos | el registro v1.0 exige `nivel`, `asignatura` y `unidad` |
| `vector.py` | genérico | búsqueda léxica, no semántica |
| `core.py` | genérico con sesgo escolar | públicos `estudiante`, `docente`, `familia`; exige marco registrado |
| `core_build.py` | genérico | el manifiesto exige datos de cobertura |
| `modalities.py` | genérico | sin ninguna modalidad real todavía |
| `markdown_course.py` | genérico, experimental | adaptador de Markdown al dataset, no al núcleo |
| `escolar_chile.py`, `core_escolar.py` | específicos | una fuente y, en el núcleo, solo 1.º básico |
| `cleaning.py` | mixto | duplicados, conflictos, cruces y etiquetas son generales; las demás suponen cuadernos y español |
| `proposals.py`, `corrections.py` | mecanismo genérico, reglas específicas | reconocen formas del español y los encabezados «Ejemplos resueltos» y «Ejercicios» |
| `cli.py` | genérico con valores por defecto | las rutas de informes apuntan a 1.º básico |
| `verify_docs.py` | casi genérico | comprueba enlaces de documentos con nombre fijo |
| `docs_diagram.py` | específico | título y posiciones del esquema de 1.º básico; las líneas nuevas se apilan solas |
| `docs_stats.py` | casi genérico | calcula desde cualquier manifiesto, pero actualiza documentos de nombre fijo |
| `verify_assets.py`, `install_claude_assets.py`, `smoke.py` | genéricos | skills y agentes, instalación y prueba de extremo a extremo |

### Lo que fallaría hoy con un segundo conjunto

- `clean-report`, `clean-proposals`, `clean-corrections` y sus aprobaciones exigen **un único núcleo** en la carpeta: con dos, se detienen.
- Los informes tienen nombres y títulos fijos de 1.º básico.
- Un dominio sin cuadernos necesita sus propios roles de recurso y reglas.

Resolver esto es el primer trabajo antes de sumar datos de otro tipo.

## 8. Órdenes y herramientas

| Orden | Para qué |
|---|---|
| `lpdatasets export`, `validate`, `stats` | dataset v1.0 |
| `lpdatasets index`, `search` | base vectorial local |
| `lpdatasets core-export`, `core-validate` | núcleo |
| `lpdatasets clean-report`, `clean-proposals`, `clean-corrections` | hallazgos, lotes y redacciones; con `--check` no escriben |
| `lpdatasets clean-approve`, `clean-approve-corrections` | únicas que registran aprobaciones |
| `lpdatasets clean-mark-applied` | tras reexportar, registra lo aplicado y archiva lo resuelto |

Skills: `dataset-conocimiento-extraer`, `dataset-verificar`, `dataset-construir-publicar` y `dataset-pack-nuevo`. Agentes: `extractor-conocimiento`, `verificador-independiente`, `curador-datasets`, `auditor-derechos-datos` y `limpiador-datos`. En este trabajo, las lecturas ciegas las hizo `verificador-independiente`; las propuestas se prepararon sin delegar en `limpiador-datos`, que sigue sin probarse en un lote real.

## 9. Lo que no está hecho

- Ninguna persona ha revisado el contenido.
- Quedan 93 hallazgos pendientes y 4 correcciones sin aprobar.
- Líneas L03 a L09 sin implementación nueva; ninguna modalidad real.
- La posible nueva propuesta curricular sigue sin confirmación oficial.
- Las condiciones de reutilización de los textos oficiales necesitan una respuesta de su titular; esto no es asesoría legal.
