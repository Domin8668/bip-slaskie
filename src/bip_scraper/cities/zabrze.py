"""Scraper for Zabrze BIP uchwały Rady Miasta.

BIP URL: https://bip.miastozabrze.pl/rm/rm_uchwaly/rm_uchwaly_{year}

The Zabrze BIP uses a Vue.js SPA. Each year's static HTML page embeds the
JSON API endpoint in a ``v-document-list`` component config attribute.
The API returns all resolutions for that year in a single JSON response.

Note: bip.miastozabrze.pl uses a self-signed TLS certificate, so SSL
verification is disabled for requests to this host.
"""

from __future__ import annotations

import html as html_module
import json
import re
from datetime import UTC, datetime

from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.miastozabrze.pl"
_HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class ZabrzeScraper(BaseScraper):
    """Scraper for Zabrze BIP council resolutions."""

    _verify_ssl = False  # bip.miastozabrze.pl uses a self-signed TLS certificate

    @property
    def city(self) -> CitySlug:
        return CitySlug.ZABRZE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        acts: dict[str, LegalAct] = {}
        for year in (now.year, now.year - 1):
            page_html = self._get_text(f"{BASE_URL}/rm/rm_uchwaly/rm_uchwaly_{year}")
            api_url = _parse_api_url(page_html)
            if not api_url:
                continue
            api_json = self._get_text(f"{api_url}?q=")
            for act in _parse_documents(api_json):
                acts[act.stable_id] = act
        if not acts:
            raise RuntimeError("Zabrze scraper: no legal acts found")
        return sorted(acts.values(), key=lambda a: a.stable_id)


def _parse_api_url(page_html: str) -> str | None:
    """Extract the API ``loadURL`` from the ``v-document-list`` component config."""
    unescaped = html_module.unescape(page_html)
    m = re.search(r'"loadURL":"(https?:[^"]+)"', unescaped)
    if not m:
        return None
    return m.group(1).replace(r"\/", "/").replace(r"\\", "")


def _parse_documents(json_text: str) -> list[LegalAct]:
    """Parse legal acts from the document-list API JSON response."""
    data: dict = json.loads(json_text)
    results: list[LegalAct] = []
    for doc in data.get("data", []):
        act = _parse_document(doc)
        if act:
            results.append(act)
    return results


def _parse_document(doc: dict) -> LegalAct | None:
    doc_id = doc.get("doc_id")
    title = (doc.get("dscrpt") or "").strip()
    pubdat = (doc.get("pubdat") or "").strip()
    if not doc_id or not title or not pubdat:
        return None
    try:
        published_at = datetime.strptime(pubdat[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return None
    source_url = f"{BASE_URL}/doc/{doc_id}"
    return LegalAct(
        stable_id=f"zabrze-{doc_id}",
        title=title,
        published_at=published_at,
        source_url=_HTTP_URL_ADAPTER.validate_python(source_url),
    )
