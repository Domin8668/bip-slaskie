from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.sosnowiec import SosnowiecScraper, _find_year_menus, _parse_articles_page
from bip_scraper.models import CitySlug

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_sosnowiec_city_slug() -> None:
    scraper = SosnowiecScraper()
    assert scraper.city == CitySlug.SOSNOWIEC


def test_find_year_menus_returns_mapping() -> None:
    import json

    menu_items = json.loads(_read_fixture("sosnowiec_menu.json"))
    year_menus = _find_year_menus(menu_items)

    assert year_menus[2025] == "7374"
    assert year_menus[2026] == "7437"
    # kadencja entry should also be found under year 2024
    assert 2024 in year_menus


def test_find_year_menus_empty() -> None:
    assert _find_year_menus([]) == {}


def test_parse_articles_page_returns_acts() -> None:
    acts = _parse_articles_page(_read_fixture("sosnowiec_articles.json"))

    assert len(acts) == 3
    for act in acts:
        assert act.stable_id.startswith("sosnowiec-")
        assert "Uchwała" in act.title


def test_parse_articles_page_first_act_fields() -> None:
    acts = _parse_articles_page(_read_fixture("sosnowiec_articles.json"))

    act = acts[0]
    assert act.stable_id == "sosnowiec-562029"
    assert act.published_at == datetime(2026, 1, 2, 8, 51, 42, tzinfo=UTC)
    assert "352/XXII/2025" in act.title
    assert str(act.source_url).startswith("https://bip.um.sosnowiec.pl/")


def test_parse_articles_page_source_url() -> None:
    acts = _parse_articles_page(_read_fixture("sosnowiec_articles.json"))

    act = acts[0]
    assert "562029" in str(act.source_url)


def test_parse_articles_page_empty_json() -> None:
    import json

    acts = _parse_articles_page(json.dumps({"articles": []}))
    assert acts == []
