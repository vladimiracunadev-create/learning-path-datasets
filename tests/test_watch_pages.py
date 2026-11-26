"""Páginas sin objetivos y registros manuales del vigía, sin red."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lpdatasets.core import load_marcos
from lpdatasets.watch import Page, accept, add_manual, report, summary
from lpdatasets.watch_manual import check_marcos
from lpdatasets.watch_pages import documents, snapshot
from tests.test_watch import HOST, setup, unchanged, watch

URL = f"{HOST}/bases"
BODY = "Bases Curriculares inventadas. " + "palabra " * 40
SOURCE = {"id": "bases", "titulo": "Bases", "tipo": "oficial", "metodo": "pagina", "url": URL}
SOURCE |= {"compara": ["texto", "documentos"], "esperado": ["Bases Curriculares"]}
PRESS = {"id": "diario", "titulo": "Diario", "tipo": "prensa", "metodo": "manual", "url": "https://diario.example/n"}
OFFICIAL = {"id": "consejo", "titulo": "Consejo", "tipo": "oficial", "metodo": "manual", "url": "https://c.example/"}


def page(body: str = BODY, links: tuple[str, ...] = ("a.pdf",), around: str = "menú") -> Page:
    anchors = "".join(f'<a href="/docs/{link}">ver</a>' for link in links)
    return Page(200, f"<html><body><nav>{around}</nav><main><p>{body}</p>{anchors}</main></body></html>")


def run_with(tmp_path: Path, first: Page | None = None):
    folder, doc = setup(tmp_path, [SOURCE, PRESS, OFFICIAL])

    def once(answer: Page, day: str = "2026-02-01") -> dict:
        web = unchanged()
        web.pages[URL] = answer
        return watch(folder, doc, web, day)

    if first:
        once(first, "2026-01-01")
    return folder, doc, once


def test_first_reading_sets_the_reference_without_storing_text(tmp_path: Path):
    folder, doc, once = run_with(tmp_path)
    results = once(page())
    assert results["bases"]["estado"] == "primera_lectura" and summary(results["_"])[1] == 0
    assert results["bases"]["pagina"]["documentos"] == [f"{HOST}/docs/a.pdf"]
    written = doc.read_text(encoding="utf-8") + (folder / "revisiones.jsonl").read_text(encoding="utf-8")
    assert "inventadas" not in written
    assert once(page(around="otro menú que cambia solo"), "2026-03-01")["bases"]["estado"] == "sin_cambios"


def test_a_change_is_reported_until_a_person_accepts_it(tmp_path: Path):
    folder, doc, once = run_with(tmp_path, page())
    new = page(BODY + "Ahora hay una resolución nueva.", ("b.pdf",))
    for day in ("2026-02-01", "2026-03-01"):
        results = once(new, day)
        assert [c["cambio"] for c in results["bases"]["cambios"]] == ["texto", "documento_nuevo", "documento_quitado"]
        assert summary(results["_"])[1] == 1
    assert f"<{HOST}/docs/b.pdf>" in doc.read_text(encoding="utf-8")
    accept(folder, "bases", "revisora")
    saved = json.loads((folder / "aceptadas.json").read_text(encoding="utf-8"))["bases"]
    assert saved["aprobado_por"] == "revisora" and saved["revision"] == "2026-03-01"
    assert once(new, "2026-04-01")["bases"]["estado"] == "sin_cambios"


def test_a_change_of_form_only_is_told_apart(tmp_path: Path):
    _, _, once = run_with(tmp_path, page())
    [change] = once(page(BODY.upper().replace("BASES CURRICULARES", "Bases Curriculares")))["bases"]["cambios"]
    assert change == {"cambio": "forma"}


@pytest.mark.parametrize(
    "broken",
    [
        page("Sitio en mantenimiento. " + "espere " * 40),
        page("Bases Curriculares."),
        page(links=()),
    ],
)
def test_an_unexpected_page_is_unreadable(tmp_path: Path, broken: Page):
    _, _, once = run_with(tmp_path, page())
    results = once(broken)
    assert results["bases"]["estado"] == "ilegible" and "cambios" not in results["bases"]
    assert summary(results["_"])[1] == 1


def test_only_the_text_between_the_marks_is_compared():
    source = SOURCE | {"compara": ["texto"], "desde": "Publicado:", "hasta": "También"}
    first = page("Publicado: hoy. " + BODY + "También: noticia uno").text
    later = page("Publicado: hoy. " + BODY + "También: noticia dos").text
    assert snapshot(source, first) == snapshot(source, later)
    for missing in ("Publicado:", "También"):
        with pytest.raises(ValueError, match="marca"):
            snapshot(source, first.replace(missing, "x"))
    with pytest.raises(SystemExit, match="compara"):
        snapshot(SOURCE | {"compara": ["imagenes"]}, first)


def test_document_addresses_are_safe_to_write():
    area = (
        '<a href="documentos/Como se aplica (2026).pdf?v=3">x</a><a href="http://otro.example/b.PDF#p">y</a>'
        '<a href="javascript:alert(1).pdf">z</a><a href="/pagina">w</a>'
    )
    assert documents(area, f"{HOST}/inicio/") == [
        f"{HOST}/inicio/documentos/Como%20se%20aplica%20%282026%29.pdf",
        "https://otro.example/b.PDF",
    ]


@pytest.mark.parametrize(
    ("source", "approver", "message"),
    [("bases", " ", "quien aprueba"), ("oa:artes", "r", "watch-baseline"), ("x", "r", "solo se aceptan")],
)
def test_acceptance_is_refused(tmp_path: Path, source: str, approver: str, message: str):
    folder, _, _ = run_with(tmp_path, page())
    with pytest.raises(SystemExit, match=message):
        accept(folder, source, approver)
    assert not (folder / "aceptadas.json").exists()


def test_an_unreadable_page_cannot_be_accepted(tmp_path: Path):
    folder, _, once = run_with(tmp_path, page())
    once(Page(500))
    with pytest.raises(SystemExit, match="no pudo leerla"):
        accept(folder, "bases", "revisora")


def record(source: str, **values) -> dict:
    entry = {"fuente": source, "fecha": "2026-02-02", "revisado_por": "persona", "resultado": "novedad"}
    return entry | {"nota": "leí la resolución"} | values


def test_manual_review_is_listed_and_changes_no_framework(tmp_path: Path):
    folder, doc, _ = run_with(tmp_path, page())
    before = json.dumps(load_marcos(), sort_keys=True)
    proposal = {"marco": "cl-bases-1-6-propuesta-2026", "estado_marco": "vigente"}
    saved = add_manual(folder, doc, record("consejo", **proposal), load_marcos())
    assert saved["url"] == OFFICIAL["url"]
    written = doc.read_text(encoding="utf-8")
    assert "2026-02-02, persona: novedad" in written and "(sin aplicar)" in written
    assert json.dumps(load_marcos(), sort_keys=True) == before
    assert report(folder, doc, check=True) == []


def test_press_cannot_mark_a_framework_as_current(tmp_path: Path):
    folder, doc, _ = run_with(tmp_path, page())
    proposal = {"marco": "cl-bases-1-6-propuesta-2026", "estado_marco": "vigente"}
    with pytest.raises(SystemExit, match="prensa no puede marcar"):
        add_manual(folder, doc, record("diario", **proposal), load_marcos())
    assert not (folder / "revisiones-manuales.jsonl").exists()
    allowed = proposal | {"estado_marco": "propuesta_sin_confirmar"}
    add_manual(folder, doc, record("diario", **allowed), load_marcos())


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"fecha": "ayer"}, "fecha"),
        ({"revisado_por": " "}, "quién revisó"),
        ({"nota": ""}, "qué se leyó"),
        ({"resultado": "bien"}, "resultado"),
        ({"url": ""}, "dirección"),
        ({"url": "https://otro.example/x"}, "mismo sitio"),
        ({"marco": "inventado", "estado_marco": "vigente"}, "marco registrado"),
        ({"estado_marco": "vigente"}, "marco registrado"),
        ({"fuente": "nadie"}, "no es una fuente"),
    ],
)
def test_incomplete_manual_records_are_rejected(tmp_path: Path, values: dict, message: str):
    folder, doc, _ = run_with(tmp_path, page())
    with pytest.raises(SystemExit, match=message):
        add_manual(folder, doc, record("consejo") | values, load_marcos())


def test_a_current_framework_needs_an_official_page_that_was_read():
    sources = {"o": OFFICIAL, "p": PRESS}
    good = {"estado": "vigente", "verificacion": "pagina_oficial_leida", "url": "https://c.example/bases"}
    assert check_marcos({"a": good}, sources) == []
    assert "sin una página oficial leída" in check_marcos({"a": good | {"verificacion": "resumen"}}, sources)[0]
    assert "sitio oficial" in check_marcos({"a": good | {"url": PRESS["url"]}}, sources)[0]
    assert check_marcos({"a": good | {"estado": "propuesta_sin_confirmar", "url": PRESS["url"]}}, sources) == []
