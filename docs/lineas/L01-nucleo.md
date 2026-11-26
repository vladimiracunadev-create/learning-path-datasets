# L01 · Núcleo de contenido

- **Estado:** `OPERATIVO`
- **Depende de:** nada; las demás líneas dependen de esta

## Propósito

Representar el contenido de 1.º básico una sola vez, como clases, ítems y recursos con marco curricular, derechos, revisión y procedencia, para que cada modalidad lo lea sin volver a interpretar la fuente.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Ver una clase completa con su OA | docente | educativo | docente |
| Entregar un ejercicio sin la solución | estudiante acompañado | educativo | estudiante |
| Saber si un contenido puede usarse en un producto pagado | titular | comercial | docente |
| Separar bases vigentes de una propuesta | mantenimiento | educativo | docente |
| Agregar una imagen o un audio a una clase | autor | personal | estudiante |

## Entradas y salidas

Entrada: un commit de `chilean-school-learning-path` sin cambios pendientes (catálogo, fichas, cuadernos del estudiante y diccionarios). Salida en `nucleo/escolar-chile/1-basico/`: `clases.jsonl`, `items.jsonl`, `recursos.jsonl` y `manifest.json` con SHA-256 y cobertura.

| Contenido exportado | Cantidad |
|---|---:|
| Clases (562 desarrolladas y 325 integradas) | 887 |
| Clases excluidas (Pueblos Originarios), declaradas en el manifiesto | 147 |
| OA representados de 237 | 204 |
| Ítems, con los mismos identificadores que el dataset v1.0 | 16.386 |
| Recursos: guías docentes (887), cuadernos (562) y orientaciones por OA (204) | 1.653 |

## Contrato de datos

[Contrato `nucleo-0.1`](../CORE_CONTRACT.md). Cada recurso declara su `extra.rol`:

| Rol | Contiene | Público |
|---|---|---|
| `guia_docente` | planificación, solucionario y notas docentes de una clase | docente |
| `cuaderno_estudiante` | explicación, ejemplos y preguntas, sin solucionario | estudiante, docente, familia |
| `orientacion_oa` | orientación pedagógica de un OA | docente |

En los ítems, `ejercicio_cerrado`, `autoevaluacion` y `actividad_abierta` muestran la solución solo al docente.

## Derechos

El contenido pedagógico original es CC BY-NC-SA 4.0, con atribución. El texto oficial de los OA no se copia. Las experiencias integradas lo citaban literalmente en la fuente: sus títulos, guías y orientaciones lo sustituyen por «texto oficial no incluido» y el código (el manifiesto cuenta cuántas entidades y tramos). Se omiten tramos de seis o más palabras; fragmentos más cortos pueden quedar. En el resto, una coincidencia de ocho o más palabras no se altera: se marca para revisión (L02). Lengua y Cultura de Pueblos Originarios queda excluida.

## Cómo se ejecuta

```bash
lpdatasets core-export --source ../chilean-school-learning-path
lpdatasets core-validate
```

La exportación carga los cuadernos desde la fuente y puede tardar varios minutos.

## Pruebas

`tests/test_core.py` (contrato), `tests/test_core_export.py` (fuente sintética: cobertura, omisión de texto oficial, separación del solucionario y determinismo) y `tests/test_published_core.py` (el núcleo publicado, conciliado con el dataset v1.0). El CI no vuelve a exportar desde la fuente real.

## Métricas

887 de 1.034 entradas representadas y 147 excluidas con motivo; 0 entidades inválidas; dos exportaciones del commit `668559a65254` produjeron bytes idénticos (comprobado el 2026-11-26). El núcleo actual proviene del commit `3fd976d50bb2`, con las mismas cifras de cobertura.

## Listo cuando

Las 691 clases desarrolladas y las 343 experiencias integradas están representadas o excluidas con motivo declarado, y dos exportaciones del mismo commit producen los mismos bytes.

## Límites

El contrato puede cambiar mientras sea `0.1`. Validar la forma no comprueba que el contenido sea correcto. Solo cubre 1.º básico. Los 33 OA sin representación son los de la asignatura excluida. No hay imágenes ni audio. Las habilidades siguen vacías.

## Decisiones

- 2026-11-26: el núcleo es independiente del esquema de registros v1.0, que no cambia; el dataset publicado sigue siendo válido.
- 2026-11-26: las particiones de entrenamiento no son parte del núcleo; las decide cada modalidad.
- 2026-11-26: el núcleo de 1.º básico se versiona en Git (unos 31 MB, 2,5 MB comprimido) para que el CI lo valide; sumar niveles exigirá publicarlo fuera de Git.
- 2026-11-26: el cuaderno se separa del solucionario por la estructura de la ficha; si no se puede separar, la exportación falla.
