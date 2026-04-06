from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.zabrze import ZabrzeScraper, _parse_api_url, _parse_documents
from bip_scraper.models import CitySlug

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_zabrze_city_slug() -> None:
    scraper = ZabrzeScraper()
    assert scraper.city == CitySlug.ZABRZE


def test_parse_api_url_extracts_url() -> None:
    html = _read_fixture("zabrze_page_2025.html")
    url = _parse_api_url(html)

    assert url == "https://bip.miastozabrze.pl/api/v1/document-list/693"


def test_parse_api_url_returns_none_on_missing() -> None:
    assert _parse_api_url("<html><body>no config here</body></html>") is None


def test_parse_documents_returns_acts() -> None:
    acts = _parse_documents(_read_fixture("zabrze_api.json"))

    assert len(acts) == 3
    for act in acts:
        assert act.stable_id.startswith("zabrze-")
        assert "Uchwała" in act.title


def test_parse_documents_first_act_fields() -> None:
    acts = _parse_documents(_read_fixture("zabrze_api.json"))

    act = acts[0]
    assert act.stable_id == "zabrze-24175"
    assert act.published_at == datetime(2026, 1, 5, 14, 39, 25, tzinfo=UTC)
    assert "XXVI/275/25" in act.title
    assert str(act.source_url) == "https://bip.miastozabrze.pl/doc/24175"


def test_parse_documents_source_url_format() -> None:
    acts = _parse_documents(_read_fixture("zabrze_api.json"))

    for act in acts:
        assert str(act.source_url).startswith("https://bip.miastozabrze.pl/doc/")


def test_parse_documents_empty_data() -> None:
    import json

    acts = _parse_documents(json.dumps({"data": []}))
    assert acts == []
