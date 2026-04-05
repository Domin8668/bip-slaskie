from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.katowice import KatowiceScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_katowice_extracts_session_urls() -> None:
    scraper = KatowiceScraper()
    session_html = _read_fixture("katowice_sessions.html")

    urls = scraper._load_session_urls_from_html(session_html, limit=2)

    assert len(urls) == 2
    assert urls[0].endswith("ids=630&menu=660")
    assert urls[1].endswith("ids=629&menu=660")


def test_katowice_parses_acts() -> None:
    scraper = KatowiceScraper()
    acts_html = _read_fixture("katowice_acts.html")

    acts = scraper._parse_session_acts(acts_html, now=datetime(2026, 2, 16, tzinfo=UTC))

    assert len(acts) == 2
    assert acts[0].stable_id == "katowice-uchwala-150375"
    assert acts[0].published_at == datetime(2026, 1, 29, tzinfo=UTC)
    assert acts[0].source_url.path.endswith("dokument.aspx")
