"""Línea L04: cómo se resume una página sin objetivos: el texto de su zona principal y los documentos que enlaza.

Solo guarda huellas y direcciones de documentos, nunca el texto. Cada fuente dice qué se compara (`texto`,
`documentos` o ambos) y, si la página mezcla contenido que cambia solo, entre qué marcas (`desde`, `hasta`) está lo
que importa.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

PARTS = {"texto": "huella", "documentos": "documentos"}  # lo que se compara → dónde queda en la lectura
MIN_WORDS = 30
LONGEST = 300
DOCUMENT = re.compile(r"""href=["']([^"'<>]+?\.(?:pdf|docx?|xlsx?|pptx?|zip))(?:[?#][^"']*)?["']""", re.I)
AROUND = re.compile(r"<(script|style|nav|header|footer|aside)\b[\s\S]*?</\1>", re.I)


def fingerprints(text: str) -> dict[str, str]:
    """Huella exacta y huella sin forma (ignora mayúsculas, espacios y puntuación)."""
    exact = " ".join(unicodedata.normalize("NFC", text).split())
    return {"huella": _hash(exact), "huella_sin_forma": _hash(re.sub(r"\W+", "", exact.lower()))}


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def visible(page: str) -> str:
    """Texto visible de una página, sin programas ni estilos."""
    clean = re.sub(r"<(script|style)\b[\s\S]*?</\1>", " ", page, flags=re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", clean)).split())


def zone(page: str) -> str:
    """La zona principal de la página: `main`, si no `article`, si no `body`."""
    for tag in ("main", "article", "body"):
        found = re.search(rf"<{tag}\b[\s\S]*</{tag}>", page, re.I)
        if found:
            return found[0]
    return page


def documents(area: str, base: str) -> list[str]:
    """Direcciones de los documentos enlazados, sin consulta y codificadas para escribirlas sin riesgo."""
    found = set()
    for raw in DOCUMENT.findall(area):
        url = urljoin(base, html.unescape(raw.strip()))
        if urlsplit(url).scheme not in ("http", "https"):
            continue
        url = quote("https:" + url.partition(":")[2], safe=":/%-._~")
        if len(url) <= LONGEST:
            found.add(url)
    return sorted(found)


def snapshot(source: dict[str, Any], page: str) -> dict[str, Any]:
    """Resumen comparable de una página; `ValueError` si no es la que se esperaba."""
    wanted = source.get("compara") or []
    if not wanted or set(wanted) - set(PARTS):
        raise SystemExit(f"{source['id']}: «compara» necesita {' o '.join(PARTS)}")
    area = zone(page)
    text = visible(AROUND.sub(" ", area))
    for key, label in (("desde", "inicio"), ("hasta", "término")):
        if key in source:
            at = text.find(source[key])
            if at < 0:
                raise ValueError(f"no aparece la marca de {label} del contenido")
            text = text[at:] if key == "desde" else text[:at]
    searched = text if "texto" in wanted else visible(page)
    if any(phrase not in searched for phrase in source.get("esperado", [])):
        raise ValueError("no aparece lo que identifica a la página")
    result: dict[str, Any] = {}
    if "texto" in wanted:
        if len(text.split()) < MIN_WORDS:
            raise ValueError("el contenido tiene muy pocas palabras")
        result |= fingerprints(text)
    if "documentos" in wanted:
        result["documentos"] = documents(area, source["url"])
        if not result["documentos"]:
            raise ValueError("no se encontró ningún documento enlazado")
    return result


def comparable(reading: dict[str, Any], source: dict[str, Any]) -> bool:
    return all(PARTS[part] in reading for part in source.get("compara", []))


def compare_page(reference: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    """Estado de una página frente a su referencia."""
    if reference is None:
        return {"estado": "primera_lectura", "pagina": current}
    changes: list[dict[str, str]] = []
    if "huella" in current and current["huella"] != reference["huella"]:
        same = current["huella_sin_forma"] == reference["huella_sin_forma"]
        changes.append({"cambio": "forma" if same else "texto"})
    if "documentos" in current:
        before, now = set(reference["documentos"]), set(current["documentos"])
        changes += [{"cambio": "documento_nuevo", "documento": url} for url in sorted(now - before)]
        changes += [{"cambio": "documento_quitado", "documento": url} for url in sorted(before - now)]
    result: dict[str, Any] = {"estado": "cambio" if changes else "sin_cambios", "pagina": current}
    if changes:
        result["cambios"] = changes
    return result
