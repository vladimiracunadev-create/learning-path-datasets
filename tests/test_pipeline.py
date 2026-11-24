from __future__ import annotations

import json
from pathlib import Path

import pytest

from lpdatasets.build import build, read_jsonl, validate_datasets
from lpdatasets.vector import HashingEmbedder, build_index, search


def make(tmp_path: Path, course: Path) -> Path:
    return build("markdown-course", tmp_path / "out", source=course, pack_id="demo", dominio="mixto",
                 licencia="CC-BY-4.0", repo="local/demo")  # fmt: skip


def test_markdown_pack_builds_a_valid_dataset(tmp_path, mini_course):
    folder = make(tmp_path, mini_course)
    assert validate_datasets(tmp_path / "out") == []
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["total"] == 3
    assert manifest["por_tipo"] == {"concepto": 3}
    rows = read_jsonl(folder / "train.jsonl") + read_jsonl(folder / "eval.jsonl")
    assert {r["entrada"] for r in rows} == {"Redes > Direcciones IP", "Redes > Puertos", "Finanzas > Interés compuesto"}


def test_build_is_reproducible(tmp_path, mini_course):
    first = make(tmp_path / "a", mini_course)
    second = make(tmp_path / "b", mini_course)
    assert (first / "train.jsonl").read_bytes() == (second / "train.jsonl").read_bytes()


def test_validation_detects_tampering(tmp_path, mini_course):
    folder = make(tmp_path, mini_course)
    path = next(p for p in (folder / "train.jsonl", folder / "eval.jsonl") if p.stat().st_size)
    path.write_text(path.read_text(encoding="utf-8").replace("Redes", "Otra", 1), encoding="utf-8")
    assert any("sha256" in p for p in validate_datasets(tmp_path / "out"))


def test_numpy_index_searches_across_domains_with_filters(tmp_path, mini_course):
    make(tmp_path, mini_course)
    index = tmp_path / "idx"
    assert build_index(tmp_path / "out", index) == 3
    top = search(index, "qué es un puerto de red", k=1)[0]
    assert top["entrada"].endswith("Puertos")
    only = search(index, "interés sobre el capital", k=3, filters={"asignatura": "finanzas"})
    assert [r["asignatura"] for r in only] == ["finanzas"]


def test_qdrant_backend_matches_numpy(tmp_path, mini_course):
    pytest.importorskip("qdrant_client")
    make(tmp_path, mini_course)
    build_index(tmp_path / "out", tmp_path / "n")
    build_index(tmp_path / "out", tmp_path / "q", backend="qdrant")
    a = search(tmp_path / "n", "dirección IP de un equipo", k=2)
    b = search(tmp_path / "q", "dirección IP de un equipo", k=2)
    assert [r["id"] for r in a] == [r["id"] for r in b]


def test_hashing_embedder_is_deterministic_and_lexically_meaningful():
    emb = HashingEmbedder()
    v1, v2, v3 = emb.encode(
        ["contar objetos uno por uno", "contar objetos uno por uno", "la fotosíntesis de las plantas"]
    )
    assert (v1 == v2).all()
    related = emb.encode(["contar los objetos de uno en uno"])[0]
    assert float(v1 @ related) > float(v1 @ v3)
    assert abs(float(v1 @ v1) - 1.0) < 1e-5
