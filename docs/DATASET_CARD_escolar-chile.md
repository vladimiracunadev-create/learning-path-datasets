# Tarjeta del dataset · `escolar-chile`

## Resumen

Ejemplos de aprendizaje derivados del cuaderno del estudiante y de los diccionarios de [chilean-school-learning-path](https://github.com/vladimiracunadev-create/chilean-school-learning-path), un currículo escolar chileno abierto. Hoy está publicado **1.º básico**.

<!-- STATS:BEGIN -->

| Dataset | Registros | Entrenamiento | Evaluación | Clases (entr. / eval.) | Verificables por cálculo |
|---|---:|---:|---:|---:|---:|
| `escolar-chile` · 1-basico | 16.386 | 14.589 | 1.797 | 498 / 64 | 427 |

**Total publicado:** 16.386 registros en 1 dataset(s).

Tipos en `escolar-chile` · 1-basico: actividad_abierta 562, autoevaluacion 1.686, diccionario_en 214, diccionario_es 355, ejemplo_resuelto 1.131, ejercicio_cerrado 7.868, error_comun 1.124, explicacion 562, vocabulario 2.884.

<!-- STATS:END -->

## Composición

- **Cuadernos del estudiante:** por cada clase, la explicación, el vocabulario, los ejemplos resueltos, los errores frecuentes, los ejercicios cerrados por nivel de dificultad (recuperación, comprensión, aplicación, razonamiento y desafío), los ejercicios de contexto, la autoevaluación y la actividad abierta con sus criterios.
- **Diccionarios de 1.º básico:** español (sílabas, clase, significado, sinónimos, antónimos y ejemplo; los verbos con presente, ayer y mañana) e inglés (IPA, cómo suena, traducción, significado y ejemplo traducido). Se publican con `asignatura` `lengua-es` y `lengua-en`.
- **Asignaturas:** artes visuales, ciencias naturales, educación física y salud, historia, geografía y ciencias sociales, inglés (propuesta propia), lenguaje y comunicación, matemática, música, orientación y tecnología, más los diccionarios.

## Uso previsto

Ajuste fino y evaluación de modelos pequeños o especializados en lenguaje y razonamiento elementales; recuperación de contenido de apoyo (RAG); pruebas de humo de procesos de entrenamiento. Siempre con las limitaciones de licencia y de calidad de abajo.

## Uso no previsto

Evaluar el rendimiento de estudiantes reales; sustituir material oficial; entrenar sin considerar la licencia no comercial; presentar un modelo como «equivalente a un estudiante» sin una evaluación propia y validada.

## Procedencia y reproducción

Cada registro lleva el repositorio, el commit y la ruta de origen. La exportación es determinista: con el mismo commit de origen produce los mismos bytes.

```bash
lpdatasets export --pack escolar-chile --nivel 1-basico --source ../chilean-school-learning-path --out datasets
lpdatasets validate
```

## Particiones

Cerca del 10 % de las clases (no de los ejemplos) se reserva para evaluación (`eval`). Los diccionarios no se parten y van en `train`.

## Limitaciones conocidas

- Contenido asistido por IA, **sin revisión humana profesional** (`ia_asistida_sin_revision_humana`).
- La proporción de ejercicios verificables por cálculo es baja (ver la tabla de arriba).
- Se excluye «Lengua y Cultura de los Pueblos Originarios Ancestrales» (requiere educador tradicional).
- `ingles-propuesta` es una propuesta propia, no un currículo oficial.
- Una clase puede repetir ideas de otra; la evaluación no está libre de cercanía de contenido con el entrenamiento.
- El campo `habilidades` está vacío: aún no hay etiquetado de habilidades.
- Solo 1.º básico; los otros once niveles están planificados.

## Licencia

Datos: **CC BY-NC-SA 4.0**, con atribución a «Trayectoria Escolar Chile», de Vladimir Acuña. Detalle en [`DATA-LICENSE.md`](../DATA-LICENSE.md) y [`LIMITS_AND_RIGHTS.md`](LIMITS_AND_RIGHTS.md).
