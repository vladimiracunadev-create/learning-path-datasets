# L10 · Modalidad nueva

- **Estado:** `EXPERIMENTAL`
- **Depende de:** L01

## Propósito

Que una forma de uso que hoy no existe se agregue sin rediseñar el núcleo ni tocar las demás modalidades.

## Casos

| Caso | Usuario | Uso | Público |
|---|---|---|---|
| Fichas imprimibles | docente | educativo | estudiante |
| Tarjetas de repaso | familia | personal | familia |
| Narraciones en audio | autor | educativo | estudiante |
| Aplicación o servicio de un tercero | titular | comercial | docente |

## Entradas y salidas

Entrada: lo que entrega `select()` para un uso, un público y unos marcos. Salida: lo que la modalidad escriba en su carpeta de destino.

## Contrato de datos

Una modalidad es una clase con el atributo `linea` y el método `build(entities, out)`, registrada en `src/lpdatasets/modalities.py`. Pasos para agregar una:

1. Copia la [plantilla](_PLANTILLA.md), complétala y regístrala en `lineas.json`.
2. Escribe la clase en un módulo propio y decórala con `@register("nombre")`.
3. Ejecútala con `run(...)`, que filtra por uso, público y marco antes de entregarle datos.
4. Agrega pruebas con datos sintéticos.

```python
from lpdatasets.modalities import register

@register("fichas")
class Fichas:
    linea = "L11"

    def build(self, entities, out):
        ...
        return len(entities)
```

## Derechos

`run()` solo entrega entidades cuyo uso está permitido y quita las soluciones a los públicos que no deben verlas. Una modalidad que lea archivos del núcleo por su cuenta se salta ese control y no se acepta.

## Cómo se ejecuta

```python
from lpdatasets.modalities import run

run("fichas", entities, out, uso="educativo", publico="estudiante", marcos={"cl-bases-1-6"})
```

## Pruebas

Existentes: `tests/test_modalities.py`, con una modalidad ficticia que recibe datos ya filtrados.

## Métricas

Archivos del núcleo modificados al agregar una modalidad (objetivo: 0).

## Listo cuando

Una modalidad real, como fichas imprimibles, se agrega desde la plantilla sin modificar el núcleo.

## Límites

No hay todavía ninguna modalidad real registrada ni un comando de línea para ejecutarlas. El [núcleo](L01-nucleo.md) ya tiene datos con los que probar la primera.

## Decisiones

- 2026-11-26: la selección es el único punto de entrada de datos a una modalidad.
