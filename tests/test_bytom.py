from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.bytom import BytomScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_bytom_parse_session_acts() -> None:
    scraper = BytomScraper()
    acts = scraper._parse_session_acts(
        _read_fixture("bytom_acts.html"),
        now=datetime(2026, 3, 23, tzinfo=UTC),
    )

    assert len(acts) == 2
    assert acts[0].stable_id == "bytom-uchwala-13001"
    assert acts[1].stable_id == "bytom-uchwala-13000"
    assert acts[0].published_at == datetime(2026, 3, 23, tzinfo=UTC)
    assert "268" in acts[0].title
    assert "267" in acts[1].title
    assert str(acts[0].source_url).startswith("https://www.bytom.pl/bip/")


def test_bytom_parse_year_urls() -> None:
    scraper = BytomScraper()
    urls = scraper._parse_year_urls(
        _read_fixture("bytom_kadencja.html"),
        now=datetime(2026, 4, 5, tzinfo=UTC),
    )

    # Should include 2025 and 2026 (current year - 1 and current year)
    assert any("2026-rok" in u for u in urls)
    assert any("2025-rok" in u for u in urls)
    # Should NOT include older years
    assert not any("2024-rok" in u for u in urls)


def test_bytom_parse_session_urls() -> None:
    scraper = BytomScraper()
    urls = scraper._parse_session_urls(_read_fixture("bytom_year.html"))

    assert len(urls) == 2
    assert any("uchwaly-rady-miejskiej-z-26-stycznia" in u for u in urls)
    assert any("uchwaly-rady-miejskiej-z-23-marca" in u for u in urls)


def test_bytom_stable_id_prefix() -> None:
    scraper = BytomScraper()
    acts = scraper._parse_session_acts(
        _read_fixture("bytom_acts.html"),
        now=datetime(2026, 3, 23, tzinfo=UTC),
    )
    for act in acts:
        assert act.stable_id.startswith("bytom-uchwala-")
