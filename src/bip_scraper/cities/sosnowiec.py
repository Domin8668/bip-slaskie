"""Scraper for Sosnowiec BIP uchwały Rady Miejskiej.

BIP URL: https://bip.um.sosnowiec.pl/m,6126,uchwaly.html

The Sosnowiec BIP uses the Madkom CMS and exposes a JSON REST API.
The full navigation tree (including year sub-menus) is available at:
  GET /api/menu/6126

Year sub-menus are nested children of menu item 6126 (Uchwały), accessible
via a recursive traversal of the nested "children" arrays in the response.
Articles for each year are fetched from:
  GET /api/menu/{menuId}/articles?limit=100&offset={offset}&archived=0
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime

from pydantic import HttpUrl, TypeAdapter

from bip_scraper.cities.base import BaseScraper
from bip_scraper.models import CitySlug, LegalAct

BASE_URL = "https://bip.um.sosnowiec.pl"
_MENU_API_URL = f"{BASE_URL}/api/menu/6126"
_HTTP_URL_ADAPTER: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


class SosnowiecScraper(BaseScraper):
    """Scraper for Sosnowiec BIP council resolutions."""

    @property
    def city(self) -> CitySlug:
        return CitySlug.SOSNOWIEC

    def scrape_acts(self, *, now: datetime) -> list[LegalAct]:
        menu_items: list[dict] = json.loads(self._get_text(_MENU_API_URL))
        year_menus = _find_year_menus(menu_items)
        acts: dict[str, LegalAct] = {}
        for year in (now.year, now.year - 1):
            menu_id = year_menus.get(year)
            if not menu_id:
                continue
            offset = 0
            while True:
                url = f"{BASE_URL}/api/menu/{menu_id}/articles?limit=100&offset={offset}&archived=0"
                new_acts = _parse_articles_page(self._get_text(url))
                for act in new_acts:
                    acts[act.stable_id] = act
                if len(new_acts) < 100:
                    break
                offset += 100
        if not acts:
            raise RuntimeError("Sosnowiec scraper: no legal acts found")
        return sorted(acts.values(), key=lambda a: a.stable_id)


def _find_year_menus(items: list[dict]) -> dict[int, str]:
    """Recursively find ``{year: menu_id}`` pairs from the nested menu tree."""
    result: dict[int, str] = {}
    for item in items:
        link = item.get("link") or ""
        m = re.search(r"m,(\d+),rok-(\d{4})", link)
        if m:
            result[int(m.group(2))] = m.group(1)
        children = item.get("children") or []
        result.update(_find_year_menus(children))
    return result


def _parse_articles_page(json_text: str) -> list[LegalAct]:
    """Parse a page of articles from the JSON API response."""
    data: dict = json.loads(json_text)
    results: list[LegalAct] = []
    for article in data.get("articles", []):
        act = _parse_article(article)
        if act:
            results.append(act)
    return results


def _parse_article(article: dict) -> LegalAct | None:
    article_id = article.get("id", "")
    link = article.get("link", "")
    fields = {f["fieldId"]: f["value"] for f in article.get("columnFields", [])}
    title = (fields.get(22) or "").strip()
    date_str = (fields.get(26) or "").strip()
    if not article_id or not title or not date_str:
        return None
    try:
        published_at = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return None
    source_url = f"{BASE_URL}/{link}"
    return LegalAct(
        stable_id=f"sosnowiec-{article_id}",
        title=title,
        published_at=published_at,
        source_url=_HTTP_URL_ADAPTER.validate_python(source_url),
    )
