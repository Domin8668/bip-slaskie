from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.cities.base import normalized_href as _normalized_href
from bip_scraper.models import CitySlug, LegalAct

SESSION_LIST_URL = "https://bip.katowice.eu/RadaMiasta/Uchwaly/uchwalone_ses.aspx"
SESSION_LINK_RE = re.compile(r"uchwalone\.aspx\?ids=\d+&menu=660", re.IGNORECASE)
DATE_RE = re.compile(r"Data:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})")
HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


class KatowiceScraper(BaseScraper):
    @property
    def city(self) -> CitySlug:
        return CitySlug.KATOWICE

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        session_urls = self._load_session_urls(limit=2)
        if not session_urls:
            raise RuntimeError("Katowice scraper: no session URLs discovered")

        acts: dict[str, LegalAct] = {}
        for session_url in session_urls:
            session_html = self._get_text(session_url)
            for act in self._parse_session_acts(session_html, now=now):
                acts[act.stable_id] = act

        if not acts:
            raise RuntimeError("Katowice scraper: no legal acts parsed from session pages")
        return sorted(acts.values(), key=lambda item: item.stable_id)

    def _load_session_urls(self, *, limit: int) -> list[str]:
        page_html = self._get_text(SESSION_LIST_URL)
        return self._load_session_urls_from_html(page_html, limit=limit)

    def _load_session_urls_from_html(self, page_html: str, *, limit: int) -> list[str]:
        soup = BeautifulSoup(page_html, "html.parser")
        urls: list[str] = []
        for anchor in soup.select("a[href]"):
            href = _normalized_href(anchor.get("href"))
            if not SESSION_LINK_RE.search(href):
                continue
            absolute_url = urljoin(SESSION_LIST_URL, href)
            if absolute_url not in urls:
                urls.append(absolute_url)
            if len(urls) >= limit:
                break
        return urls

    def _parse_session_acts(self, session_html: str, *, now: datetime) -> list[LegalAct]:
        soup = BeautifulSoup(session_html, "html.parser")
        results: list[LegalAct] = []
        for card in soup.select("div.tekstboks"):
            link = card.select_one("a[href*='dokument.aspx?idr=']")
            if link is None:
                continue

            href = _normalized_href(link.get("href"))
            source_url = urljoin(SESSION_LIST_URL, href)
            document_id = _extract_document_id(source_url)
            if document_id is None:
                continue

            text = card.get_text(" ", strip=True)
            published_at = _extract_published_at(text, fallback=now)
            number = _extract_resolution_number(text)
            title = link.get_text(" ", strip=True)
            title_with_number = f"{number} — {title}" if number else title
            results.append(
                LegalAct(
                    stable_id=f"katowice-uchwala-{document_id}",
                    title=title_with_number,
                    published_at=published_at,
                    source_url=HTTP_URL_ADAPTER.validate_python(source_url),
                )
            )
        return results


def _extract_document_id(url: str) -> str | None:
    parsed = urlparse(url)
    identifier = parse_qs(parsed.query).get("idr", [])
    if not identifier:
        return None
    return identifier[0]


def _extract_resolution_number(text: str) -> str | None:
    marker = "Nr:"
    marker_pos = text.find(marker)
    if marker_pos < 0:
        return None
    tail = text[marker_pos + len(marker) :].strip()
    if not tail:
        return None
    return tail.split(" ", maxsplit=1)[0].strip()


def _extract_published_at(text: str, *, fallback: datetime) -> datetime:
    match = DATE_RE.search(text)
    if match is None:
        return fallback
    return datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
