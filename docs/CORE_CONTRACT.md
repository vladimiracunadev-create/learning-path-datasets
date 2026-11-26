# Contrato del núcleo (`nucleo-0.1`)

El núcleo representa el contenido **una vez**; las modalidades (dataset, RAG, MCP, agentes y las futuras) lo leen. Definición: [`schema/core.schema.json`](../schema/core.schema.json) y `src/lpdatasets/core.py`, comparadas entre sí en `tests/test_core.py`.

Estado: experimental. Aún **no hay contenido exportado** a este formato; ver [L01](lineas/L01-nucleo.md). El [esquema de registros v1.0](DATASET_SCHEMA.md) y el dataset publicado no cambian.

## Entidades

| Entidad | Qué es | Campos propios |
|---|---|---|
| `clase` | una clase de un OA | `asignatura`, `oa`, `numero`, `estado_editorial` (`desarrollada` o `integrada`), `titulo` |
| `item` | ejercicio, explicación, definición u otra pieza | `asignatura`, `tipo`, `publico`, `publico_solucion`, `contenido` (`enunciado`, `respuesta`, `razon`); opcionales `clase_id`, `habilidades`, `dificultad` |
| `recurso` | texto, imagen, audio o cualquier medio | `medio` (tipo MIME), `publico`, y `texto` o `uri` con `sha256`; `descripcion` obligatoria si no es texto; opcional `clase_id` |

## Campos comunes

| Campo | Significado |
|---|---|
| `contrato` | `nucleo-0.1` |
| `entidad` | `clase`, `item` o `recurso` |
| `id` | identificador estable |
| `marco` | marco curricular registrado |
| `nivel` | nivel que cubre ese marco |
| `procedencia` | `repo`, `commit` y `ruta` |
| `derechos` | `licencia`, `titular`, `origen`; `atribucion` en licencias CC BY; `autorizaciones` opcionales |
| `revision` | los mismos estados del esquema v1.0 |
| `extra` | campos propios; se quita cuando se oculta la solución |

## Marcos curriculares

Registro: [`marcos.json`](../src/lpdatasets/marcos.json).

| Marco | Estado | Verificación |
|---|---|---|
| `cl-bases-1-6` | `vigente` | página oficial leída |
| `cl-bases-1-6-propuesta-2026` | `propuesta_sin_confirmar` | resumen de buscador |
| `cl-propuesta-ingles-1b` | `propuesta_no_obligatoria` | resumen de buscador |
| `sin-marco-oficial` | `no_aplica` | no aplica |

Quien selecciona nombra los marcos que quiere; no hay valor por defecto que mezcle vigentes y propuestas.

## Derechos y usos

| Licencia | `personal` | `educativo` | `comercial` |
|---|:---:|:---:|:---:|
| `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0` | sí | sí | sí |
| `CC-BY-NC-4.0`, `CC-BY-NC-SA-4.0`, `MINEDUC-NO-COMERCIAL` | sí | sí | no |
| cualquier otra, u origen `desconocido` | no | no | no |

`educativo` significa uso educativo **sin fines comerciales**. Una autorización registrada (`uso` y `referencia` al permiso) habilita un uso adicional, por ejemplo cuando el titular concede una licencia comercial. `MINEDUC-NO-COMERCIAL` es una etiqueta interna para la política del sitio oficial, no una licencia publicada. Esta tabla es una política operativa, no asesoría legal. Permitir un uso no exime de atribuir ni de compartir igual.

## Selección

```python
from lpdatasets.core import select

visibles = select(entidades, uso="educativo", publico="estudiante", marcos={"cl-bases-1-6"})
```

`select` valida cada entidad, filtra por marco, uso y público y, si el público no figura en `publico_solucion`, quita `respuesta`, `razon` y `extra`. La ocultación solo actúa sobre los ítems: el enunciado, el `extra` de las clases y el texto de los recursos no se revisan. Un recurso con soluciones debe limitar su `publico`, y un enunciado que revele la respuesta se corrige en la limpieza.

## Cambiar el contrato

Un campo nuevo opcional o un tipo MIME nuevo no rompe nada. Quitar o redefinir un campo exige una versión nueva del contrato y una nota en el [CHANGELOG](../CHANGELOG.md).
