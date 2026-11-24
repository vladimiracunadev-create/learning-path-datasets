# Cómo sumar un programa de aprendizaje

Un *pack* es una función que lee un programa y emite registros del [esquema común](DATASET_SCHEMA.md).

## Opción rápida: programas en Markdown

Si el programa son archivos `.md`, el pack genérico basta:

```bash
lpdatasets export --pack markdown-course --source ../mi-programa \
  --pack-id mi-programa --dominio ciberseguridad --licencia "CC-BY-NC-SA-4.0" \
  --repo usuario/mi-programa --out datasets
```

Divide cada archivo por encabezados (`#`, `##`, `###`) y emite un registro `concepto` por sección con al menos 25 palabras. Es **experimental**: solo se probó con un programa sintético y no entiende la estructura propia de cada programa (ejercicios, rúbricas, glosarios).

## Opción completa: un adaptador propio

1. Crea `src/lpdatasets/packs/mi_pack.py` y decora una función generadora con `@register("mi-pack")`.
2. La función recibe `source` (carpeta del programa) y los parámetros que declares; emite diccionarios con **todos** los campos obligatorios, incluidas `fuente` (repo, commit, ruta) y `licencia`.
3. Calcula la partición con `partition_for(pack, clave)` usando una clave de **clase o unidad**, nunca de ejemplo suelto.
4. Importa el módulo en `packs/__init__.py::load_builtin`.
5. Escribe pruebas con una fuente sintética pequeña.
6. Exporta, valida y actualiza cifras:

```bash
lpdatasets export --pack mi-pack --source ../mi-programa --out datasets
lpdatasets validate
python scripts/docs_stats.py --write
```

## Antes de publicar un dataset nuevo

- Confirma que la licencia del programa permite redistribuir los datos derivados y regístrala en `DATA-LICENSE.md`.
- No incluyas textos de terceros ni datos personales.
- Declara el estado de revisión real; no marques revisión humana si no la hubo.
- Documenta exclusiones y límites en una tarjeta como [la del dataset escolar](DATASET_CARD_escolar-chile.md).
