from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.tychy import TychyScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_tychy_parse_month_acts() -> None:
    scraper = TychyScraper()
    acts = scraper._parse_month_acts(
        _read_fixture("tychy_acts.html"),
        now=datetime(2026, 3, 26, tzinfo=UTC),
    )

    assert len(acts) == 2
    assert acts[0].stable_id == "tychy-uchwala-78661"
    assert acts[1].stable_id == "tychy-uchwala-78660"
    assert acts[0].published_at == datetime(2026, 3, 26, tzinfo=UTC)
    assert "XX/372/26" in acts[0].title
    assert str(acts[0].source_url).startswith("https://bip.umtychy.pl/")


def test_tychy_parse_month_urls_filters_years() -> None:
    scraper = TychyScraper()
    urls = scraper._parse_month_urls(
        _read_fixture("tychy_index.html"),
        now=datetime(2026, 4, 5, tzinfo=UTC),
    )

    # Should include months from 2025 and 2026 (kadencja 32)
    assert any("/32/2026/" in u for u in urls)
    assert any("/32/2025/" in u for u in urls)
    # Should not include years older than now.year - 1
    assert not any("/32/2024/" in u for u in urls)


def test_tychy_stable_id_prefix() -> None:
    scraper = TychyScraper()
    acts = scraper._parse_month_acts(
        _read_fixture("tychy_acts.html"),
        now=datetime(2026, 3, 26, tzinfo=UTC),
    )
    for act in acts:
        assert act.stable_id.startswith("tychy-uchwala-")
