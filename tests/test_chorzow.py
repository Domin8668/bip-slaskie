from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.chorzow import ChorzowScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_chorzow_extracts_session_urls() -> None:
    scraper = ChorzowScraper()
    sessions_html = _read_fixture("chorzow_sessions.html")

    urls = scraper._parse_session_urls_from_html(sessions_html)

    assert len(urls) >= 2
    assert all("?kat=" in url for url in urls)
    assert any("kat=173885248227029298" in url for url in urls)
    assert any("kat=173885236812798835" in url for url in urls)


def test_chorzow_parses_acts() -> None:
    scraper = ChorzowScraper()
    acts_html = _read_fixture("chorzow_acts.html")

    acts = scraper._parse_session_acts(acts_html, now=datetime(2026, 1, 29, tzinfo=UTC))

    assert len(acts) == 2
    for act in acts:
        assert act.stable_id.startswith("chorzow-uchwala-")
        assert "UCHWAŁA" in act.title
        assert act.published_at.year == 2026
