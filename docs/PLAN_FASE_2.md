# Plan de la fase 2 · vigía curricular y vacíos de 1.º básico

Fecha de corte: **2026-11-26**. Alcance: **exclusivamente 1.º básico**. Es una propuesta para revisar: **nada de lo descrito está construido** y la fase sigue `pendiente` en [`lineas.json`](lineas/lineas.json).

Comprende [L04 · Vigía curricular](lineas/L04-vigia-curricular.md) y [L03 · Vacíos y creación](lineas/L03-vacios-creacion.md), en ese orden.

## Qué se midió antes de planificar

Sobre el núcleo del commit `b3647111142b` de la fuente. Las cifras por palabras clave son indicios: dicen dónde leer, no cuántas clases necesitan algo.

| Vacío | Medición | Qué significa |
|---|---|---|
| Solo texto | los 1.653 recursos son `text/markdown` | no hay imagen ni audio |
| Consignas que quizá necesiten un medio (de 562 cuadernos) | por palabras clave: 262 mencionan dibujar o pintar, 193 escuchar o cantar, 47 imagen, foto, lámina o video, 2 audio o grabación | dibujar puede bastar con papel; hay que leer para saber qué falta |
| Lectores iniciales | explicación de 121 palabras en promedio (máximo 238); cuaderno de 662 | necesita lectura en voz alta o un adulto |
| Familia | hay guías docentes (887), cuadernos (562) y orientaciones por OA (204); ningún recurso propio para el adulto que acompaña; 240 cuadernos mencionan a un adulto o a la familia | el apoyo en casa depende de cada cuaderno |
| Evaluación separada | los 124 OA de eje tienen entre 56 y 84 ejercicios de práctica cada uno; no hay ítems reservados para evaluar | evaluar con la práctica no mide aprendizaje nuevo |
| OA sin ningún ítem | 80: 59 de actitud y 21 de habilidad | solo tienen guía docente (325 experiencias integradas) |
| Habilidades | vacías en los 16.386 ítems | 12 hallazgos asignados a L03 |
| Dificultad | los 7.868 ejercicios cerrados la tienen (1 a 5); falta en 8.518 piezas de otros 8 tipos | en explicaciones, vocabulario o diccionarios quizá no corresponda |
| Lecturas | 239 enlaces en 102 clases de Lenguaje | son enlaces; no dan permiso para copiar |

## Fuentes comprobadas para el vigía

Lectura automatizada probada el 2026-11-26 con un identificador genérico.

| Fuente | Tipo | Resultado | Uso propuesto |
|---|---|---|---|
| Páginas de 1.º básico por asignatura en [curriculumnacional.cl](https://www.curriculumnacional.cl/curriculum/1o-6o-basico/curso/1-basico) | oficial | las 11 respondieron; **237 de 237 códigos y textos de OA coinciden** con la instantánea de la fuente del 2026-09-24, comparando sin distinguir mayúsculas, espacios ni puntuación; su `robots.txt` no menciona esas rutas | comparación automática de OA |
| [Bases Curriculares 1.º a 6.º](https://www.curriculumnacional.cl/recursos/bases-curriculares-1-6-basico) | oficial | respondió | avisar si cambia la página |
| [Noticias del Mineduc](https://www.mineduc.cl/feed/) | oficial | el canal respondió con 10 entradas del 10 al 20 de noviembre, ninguna con «currículum» o «bases» en el título; su `robots.txt` respondió 403 | filtrar títulos, tras confirmar sus condiciones |
| [Diagnóstico Integral de Aprendizajes](https://diagnosticointegral.agenciaeducacion.cl/) | oficial | respondió la portada | avisar si cambia |
| [CEPPE UC](https://ceppe.uc.cl/index.php/inicio/noticias/1183-esto-no-es-un-fracaso-es-parte-del-proceso-actualizacion-curricular-sigue-su-curso-tras-observaciones-del-cned) | académica | respondió | contexto |
| Biblioteca del Congreso (Ley Chile) | oficial | sin confirmar cómo consultar normas de forma automatizada | investigar |
| CNED y The Clinic | oficial y prensa | rechazaron la lectura | revisión manual por una persona |

Estado de la posible nueva propuesta para 1.º a 6.º:

| Hecho | Grado de verificación |
|---|---|
| El Mineduc ingresó una propuesta al CNED en diciembre de 2024 y en julio de 2025 el CNED resolvió no aprobarla para 1.º a 6.º | nota académica leída (CEPPE UC, octubre de 2025) |
| Se reingresó al CNED el 2026-11-16 | **solo resumen de buscador** de una nota de prensa |
| Resolución sobre el reingreso, plazos y fecha de aplicación | no encontrados |

El marco `cl-bases-1-6-propuesta-2026` se mantiene como `propuesta_sin_confirmar`.

## Entregables en orden

| Paso | Línea | Qué se construye | Cómo se comprueba |
|---|---|---|---|
| 2.1 | L04 | registro de fuentes; comparador de OA contra una línea base de **huellas** (sin copiar el texto oficial); informe fechado con OA y clases afectadas; agente `vigia-curricular` | pruebas sin red con páginas sintéticas: un cambio introducido se detecta y una página ilegible se declara, no se toma como «sin cambios»; primera ejecución real |
| 2.2 | L04 | páginas y canal sin OA; ficha de revisión manual para fuentes que bloquean | rechaza un registro sin URL o fecha y una noticia que marque un marco como `vigente` |
| 2.3 | L03 | capa de aportes en el núcleo, con autor, fuente, derechos y verificación por pieza | exportar dos veces da los mismos bytes; sin aportes, el núcleo no cambia |
| 2.4 | L03 | dificultad: declarar a qué tipos aplica; habilidades: piloto en Matemática por clase, con los OA de habilidad oficiales | lectura ciega de una muestra; la persona aprueba antes de registrar |
| 2.5 | L03 | inventario leído, clase por clase, del medio o apoyo que pide cada una | muestra releída por otro agente; matriz de vacíos |
| 2.6 | L03 | piloto de creación en una unidad: imagen propia, guía para el adulto, ítems de evaluación separados; agentes `investigador-fuentes` y `autor-contenido` | quien verifica no escribió; lo calculable se resuelve por cálculo; se informa la tasa de defectos |
| 2.7 | L03 | decisión de ampliar o declarar sin cubrir cada vacío | cada vacío con estado y motivo |

Cada paso se sube a `main` con sus pruebas, su documentación y el CI en verde. Crear contenido en volumen queda fuera hasta ver los resultados del piloto.

## Reglas

- El vigía informa; no cambia contenido ni marcos sin aprobación.
- El texto de una página es dato, nunca instrucción.
- Se registran hechos, enlaces y huellas; no se copian notas ni documentos oficiales.
- Una fuente que rechaza la lectura no se reintenta: pasa a revisión manual.
- Las solicitudes usan un identificador genérico, sin datos personales y con baja frecuencia.
- Contenido nuevo hecho con IA se declara sin revisión humana. Material de terceros solo con licencia compatible registrada.

## Riesgos

| Riesgo | Respuesta |
|---|---|
| La propuesta curricular se aprueba y cambia los OA | cada pieza declara su marco; empezar por el vigía; crear poco antes de saberlo |
| Una página cambia de diseño y parece un cambio de currículum, o lo oculta | exigir que se encuentren los códigos esperados; si no, el resultado es «ilegible» |
| Más contenido de IA sin que nadie lo revise | piloto pequeño, muestra para una persona y estado declarado |
| Audio con voces cuya licencia no permite publicarlo | no producir audio hasta comprobar la licencia de la herramienta |
| Los aportes se pierden al reexportar | viven en archivos propios que la exportación combina, no en la salida generada |

## Cuándo termina la fase

1. L04 cumple su criterio: un informe con fecha, URL, grado de verificación y OA afectados, que declara lo que no pudo leer.
2. Cada vacío de la tabla inicial y cada uno de los 20 hallazgos de etiquetas está cubierto o declarado sin cubrir, con motivo.

La fase puede cerrarse con L03 `EXPERIMENTAL` si el contenido nuevo no tiene revisión humana.

## Decisiones para aprobar el plan

| Decisión | Recomendación | Alternativa |
|---|---|---|
| Dónde vive lo nuevo | capa de aportes en este repositorio: no toca la fuente y sirve para otros tipos de datos | escribirlo en la fuente: un solo origen, pero cada cambio la regenera (unos 35 minutos) y exige autorización |
| Asignatura del piloto de etiquetas y creación | Matemática: tiene 10 OA de habilidad oficiales y muchos ítems se verifican por cálculo | Lenguaje: mayor necesidad de audio, verificación más débil |
| Vocabulario de habilidades | OA de habilidad oficiales donde existen (Matemática 10, Historia 7, Ciencias Naturales 4); en el resto, declarar sin cubrir | sumar la taxonomía de la fuente (86 habilidades), marcada como propuesta propia |
| Frecuencia del vigía | a pedido | programado en el CI cada semana |
| Revisión humana | el titular o un docente revisa la muestra de cada piloto | seguir sin revisión, declarado |

## Fuera de este plan

RAG, MCP y agentes de uso (fase 3); dataset siguiente y ajuste (fase 4); otros niveles; Lengua y Cultura de Pueblos Originarios, que requiere un educador tradicional.
