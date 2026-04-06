from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.rudaslaska import RudaSlaskaScraper
from bip_scraper.models import CitySlug

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_rudaslaska_parse_year_urls_filters_years() -> None:
    scraper = RudaSlaskaScraper()
    now = datetime(2026, 4, 5, tzinfo=UTC)
    urls = scraper._parse_year_urls(_read_fixture("rudaslaska_root.html"), now=now)

    assert any("2025" in u for u in urls)
    assert any("2026" in u for u in urls)
    assert not any("2023" in u for u in urls)
    assert not any("2022" in u for u in urls)


def test_rudaslaska_parse_year_urls_absolute() -> None:
    scraper = RudaSlaskaScraper()
    now = datetime(2026, 4, 5, tzinfo=UTC)
    urls = scraper._parse_year_urls(_read_fixture("rudaslaska_root.html"), now=now)

    for url in urls:
        assert url.startswith("https://rudaslaska.bip.info.pl")


def test_rudaslaska_parse_session_urls_returns_pairs() -> None:
    scraper = RudaSlaskaScraper()
    items = scraper._parse_session_urls(_read_fixture("rudaslaska_year.html"))

    assert len(items) == 2
    urls, dates = zip(*items, strict=False)
    assert all(u.startswith("https://rudaslaska.bip.info.pl") for u in urls)
    assert datetime(2026, 3, 26, tzinfo=UTC) in dates
    assert datetime(2026, 1, 29, tzinfo=UTC) in dates


def test_rudaslaska_parse_session_acts_returns_acts() -> None:
    scraper = RudaSlaskaScraper()
    session_date = datetime(2026, 3, 26, tzinfo=UTC)
    acts = scraper._parse_session_acts(
        _read_fixture("rudaslaska_session.html"), session_date=session_date
    )

    # Only 2 uchwały; "Sprawozdanie" and the link without dokument.php must be skipped
    assert len(acts) == 2
    for act in acts:
        assert act.stable_id.startswith("rudaslaska-uchwala-")
        assert act.published_at == session_date


def test_rudaslaska_parse_session_acts_fields() -> None:
    scraper = RudaSlaskaScraper()
    session_date = datetime(2026, 3, 26, tzinfo=UTC)
    acts = scraper._parse_session_acts(
        _read_fixture("rudaslaska_session.html"), session_date=session_date
    )

    act = acts[0]
    assert act.stable_id == "rudaslaska-uchwala-11111"
    assert "Uchwała" in act.title
    assert (
        str(act.source_url) == "https://rudaslaska.bip.info.pl/dokument.php?iddok=11111&idmp=3&r=o"
    )


def test_rudaslaska_parse_session_acts_skips_non_uchwaly() -> None:
    scraper = RudaSlaskaScraper()
    session_date = datetime(2026, 3, 26, tzinfo=UTC)
    acts = scraper._parse_session_acts(
        _read_fixture("rudaslaska_session.html"), session_date=session_date
    )

    stable_ids = {a.stable_id for a in acts}
    assert "rudaslaska-uchwala-11113" not in stable_ids


def test_rudaslaska_stable_id_prefix() -> None:
    scraper = RudaSlaskaScraper()
    session_date = datetime(2026, 3, 26, tzinfo=UTC)
    acts = scraper._parse_session_acts(
        _read_fixture("rudaslaska_session.html"), session_date=session_date
    )

    for act in acts:
        assert act.stable_id.startswith("rudaslaska-uchwala-")


def test_rudaslaska_city_slug() -> None:
    scraper = RudaSlaskaScraper()
    assert scraper.city == CitySlug.RUDASLASKA
