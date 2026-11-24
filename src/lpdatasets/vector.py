"""Base vectorial local: embeddings deterministas, almacén NumPy exacto y almacén Qdrant opcional.

El embedder por defecto es léxico (hashing de palabras, bigramas y fragmentos de letras): no requiere
descargas ni red y da resultados repetibles, pero NO es semántico. Para búsqueda semántica real se puede
inyectar otro embedder con la misma interfaz (`dim` y `encode`).
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
import zlib
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from .build import manifests, read_jsonl
from .schema import text_for_embedding

DIM = 384
META_FIELDS = ("id", "pack", "dominio", "nivel", "asignatura", "unidad", "clase", "tipo", "particion", "idioma")
WORD = re.compile(r"[a-z0-9ñ]+")


class Embedder(Protocol):
    dim: int

    def encode(self, texts: Iterable[str]) -> np.ndarray: ...


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


class HashingEmbedder:
    """Embedding léxico determinista (feature hashing con signo, sublineal, norma L2)."""

    name = "hashing-v1"

    def __init__(self, dim: int = DIM) -> None:
        self.dim = dim

    def _features(self, text: str) -> dict[str, float]:
        words = WORD.findall(normalize(text))
        feats: dict[str, float] = {}

        def add(key: str, weight: float) -> None:
            feats[key] = feats.get(key, 0.0) + weight

        for w in words:
            add("w:" + w, 1.0)
            padded = f"^{w}$"
            for n in (3, 4, 5):
                for i in range(len(padded) - n + 1):
                    add("c:" + padded[i : i + n], 0.25)
        for a, b in zip(words, words[1:], strict=False):
            add(f"b:{a}_{b}", 0.6)
        return feats

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        rows = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            for key, weight in self._features(text).items():
                h = zlib.crc32(key.encode("utf-8"))
                sign = 1.0 if (h >> 16) & 1 else -1.0
                vec[h % self.dim] += sign * math.log1p(weight)
            norm = float(np.linalg.norm(vec))
            rows.append(vec / norm if norm else vec)
        return np.vstack(rows) if rows else np.zeros((0, self.dim), dtype=np.float32)


def _matches(meta: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, want in filters.items():
        have = meta.get(key)
        if isinstance(want, (list, tuple, set)):
            if have not in want:
                return False
        elif have != want:
            return False
    return True


class NumpyStore:
    """Almacén exacto por coseno: `vectors.npy` + `meta.jsonl` + `config.json`."""

    backend = "numpy"

    def __init__(self, vectors: np.ndarray, metas: list[dict[str, Any]], embedder: str) -> None:
        self.vectors, self.metas, self.embedder = vectors, metas, embedder

    def save(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        np.save(folder / "vectors.npy", self.vectors.astype(np.float32))
        (folder / "meta.jsonl").write_text(
            "".join(json.dumps(m, ensure_ascii=False, sort_keys=True) + "\n" for m in self.metas),
            encoding="utf-8",
            newline="\n",
        )
        config = {
            "backend": self.backend,
            "dim": int(self.vectors.shape[1]),
            "count": len(self.metas),
            "embedder": self.embedder,
        }
        (folder / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")

    @classmethod
    def load(cls, folder: Path) -> NumpyStore:
        config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
        vectors = np.load(folder / "vectors.npy")
        metas = [json.loads(x) for x in (folder / "meta.jsonl").read_text(encoding="utf-8").splitlines() if x]
        return cls(vectors, metas, config["embedder"])

    def query(self, vector: np.ndarray, k: int = 5, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not len(self.metas):
            return []
        scores = self.vectors @ vector.astype(np.float32)
        if filters:
            mask = np.array([_matches(m, filters) for m in self.metas])
            scores = np.where(mask, scores, -np.inf)
        order = np.argsort(-scores, kind="stable")[:k]
        return [{"score": float(scores[i]), **self.metas[i]} for i in order if np.isfinite(scores[i])]


class QdrantStore:
    """Base vectorial Qdrant en modo local (archivos en disco); requiere el extra `qdrant`."""

    backend = "qdrant"
    COLLECTION = "learning_path_datasets"

    def __init__(self, folder: Path) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:  # pragma: no cover - depende del extra
            raise SystemExit("falta qdrant-client: instala con `pip install .[qdrant]`") from exc
        self.folder = folder
        self.client = QdrantClient(path=str(folder))

    def build(self, vectors: np.ndarray, metas: list[dict[str, Any]]) -> None:
        from qdrant_client import models

        if self.client.collection_exists(self.COLLECTION):
            self.client.delete_collection(self.COLLECTION)
        self.client.create_collection(
            self.COLLECTION,
            vectors_config=models.VectorParams(size=int(vectors.shape[1]), distance=models.Distance.COSINE),
        )
        batch = 512
        for start in range(0, len(metas), batch):
            points = [
                models.PointStruct(id=i, vector=vectors[i].tolist(), payload=metas[i])
                for i in range(start, min(start + batch, len(metas)))
            ]
            self.client.upsert(self.COLLECTION, points=points)

    def query(self, vector: np.ndarray, k: int = 5, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from qdrant_client import models

        flt = None
        if filters:
            must = []
            for key, want in filters.items():
                match = (
                    models.MatchAny(any=list(want))
                    if isinstance(want, (list, tuple, set))
                    else models.MatchValue(value=want)
                )
                must.append(models.FieldCondition(key=key, match=match))
            flt = models.Filter(must=must)
        res = self.client.query_points(self.COLLECTION, query=vector.tolist(), limit=k, query_filter=flt)
        return [{"score": float(p.score), **(p.payload or {})} for p in res.points]

    def close(self) -> None:
        self.client.close()


def collect(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mpath in manifests(root):
        for name in json.loads(mpath.read_text(encoding="utf-8"))["archivos"]:
            rows += read_jsonl(mpath.parent / name)
    return rows


def build_index(
    datasets: Path,
    out: Path,
    backend: str = "numpy",
    embedder: Embedder | None = None,
    splits: tuple[str, ...] = ("train", "eval"),
) -> int:
    """Indexa los datasets; devuelve la cantidad de registros indexados."""
    embedder = embedder or HashingEmbedder()
    rows = [r for r in collect(datasets) if r["particion"] in splits]
    if not rows:
        raise SystemExit("no hay registros para indexar")
    rows.sort(key=lambda r: r["id"])
    metas = []
    for r in rows:
        meta = {k: r.get(k) for k in META_FIELDS}
        meta.update(entrada=r["entrada"], salida=r["salida"])
        metas.append(meta)
    vectors = np.vstack(
        [embedder.encode([text_for_embedding(r) for r in rows[i : i + 512]]) for i in range(0, len(rows), 512)]
    )
    name = getattr(embedder, "name", type(embedder).__name__)
    if backend == "numpy":
        NumpyStore(vectors, metas, name).save(out)
    elif backend == "qdrant":
        out.mkdir(parents=True, exist_ok=True)
        store = QdrantStore(out / "qdrant")
        store.build(vectors, metas)
        store.close()
        (out / "config.json").write_text(
            json.dumps(
                {"backend": "qdrant", "dim": int(vectors.shape[1]), "count": len(metas), "embedder": name}, indent=2
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    else:
        raise SystemExit(f"backend desconocido: {backend}")
    return len(rows)


def search(
    index: Path, query: str, k: int = 5, filters: dict[str, Any] | None = None, embedder: Embedder | None = None
) -> list[dict[str, Any]]:
    config = json.loads((index / "config.json").read_text(encoding="utf-8"))
    embedder = embedder or HashingEmbedder(config["dim"])
    vector = embedder.encode([query])[0]
    if config["backend"] == "numpy":
        return NumpyStore.load(index).query(vector, k, filters)
    store = QdrantStore(index / "qdrant")
    try:
        return store.query(vector, k, filters)
    finally:
        store.close()
