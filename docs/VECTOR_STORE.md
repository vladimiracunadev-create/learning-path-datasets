# Base vectorial

`lpdatasets index` construye una base vectorial local con todos los registros de `datasets/` (o solo las particiones que pidas) y `lpdatasets search` la consulta con filtros por metadatos.

```bash
lpdatasets index --out .vector                      # NumPy exacto, sin dependencias extra
lpdatasets index --out .vector-q --backend qdrant   # Qdrant en modo local (extra "qdrant")
lpdatasets index --splits train                     # solo entrenamiento, para RAG sin tocar la evaluación

lpdatasets search "qué es un puerto" --dominio inteligencia-artificial -k 5
lpdatasets search "dog" --tipo diccionario_en --json
```

Filtros disponibles: `--pack`, `--dominio`, `--nivel`, `--asignatura`, `--tipo`, `--particion`, `--idioma`. Como todos los programas comparten el mismo esquema, una consulta puede cruzar conocimientos o acotarse a uno.

## Almacenes

| Almacén | Cómo busca | Cuándo usarlo |
|---|---|---|
| `numpy` (por defecto) | coseno exacto sobre `vectors.npy`, metadatos en `meta.jsonl` | datasets de hasta cientos de miles de registros; sin dependencias extra |
| `qdrant` | Qdrant en modo local, coseno, filtros por carga útil | cuando se quiere una base de datos vectorial con filtrado nativo |

Con los mismos vectores, los dos devuelven los mismos resultados: hay una prueba de equivalencia. La construcción de Qdrant es bastante más lenta que la de NumPy para el dataset completo.

## Embeddings: qué hay y qué no

El embedder por defecto, `hashing-v1`, es **léxico**: codifica palabras, bigramas y fragmentos de letras con *feature hashing* y normaliza. Es determinista, no descarga modelos y funciona sin red, pero **no entiende significado**: encuentra textos que comparten palabras, no sinónimos ni paráfrasis.

Para búsqueda semántica hay que inyectar un embedder con la misma interfaz (`dim` y `encode(textos) -> np.ndarray` normalizado) en `build_index` y `search`. Esa integración está **planificada y no verificada** en este repositorio.

## Índices y versiones

Los índices no se versionan (`.vector*/` está en `.gitignore`): se reconstruyen desde `datasets/`. El `config.json` de cada índice registra el embedder usado; un índice solo es consultable con el mismo embedder.
