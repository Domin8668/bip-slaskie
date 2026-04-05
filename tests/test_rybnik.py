from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.rybnik import RybnikScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_rybnik_parse_acts_filters_recent() -> None:
    scraper = RybnikScraper()
    acts = scraper._parse_acts(
        _read_fixture("rybnik_acts.html"),
        now=datetime(2026, 4, 5, tzinfo=UTC),
    )

    # Old act (2020) must be excluded; 2026 acts must be included
    assert len(acts) == 2
    stable_ids = {a.stable_id for a in acts}
    assert "rybnik-uchwala-15873" in stable_ids
    assert "rybnik-uchwala-15868" in stable_ids
    assert "rybnik-uchwala-5000" not in stable_ids


def test_rybnik_parse_acts_fields() -> None:
    scraper = RybnikScraper()
    acts = scraper._parse_acts(
        _read_fixture("rybnik_acts.html"),
        now=datetime(2026, 4, 5, tzinfo=UTC),
    )

    act = next(a for a in acts if a.stable_id == "rybnik-uchwala-15873")
    assert act.published_at == datetime(2026, 3, 26, tzinfo=UTC)
    assert "425/XXIII/2026" in act.title
    assert "Skargi" in act.title
    assert str(act.source_url).startswith("https://bip.um.rybnik.eu/")


def test_rybnik_stable_id_prefix() -> None:
    scraper = RybnikScraper()
    acts = scraper._parse_acts(
        _read_fixture("rybnik_acts.html"),
        now=datetime(2026, 4, 5, tzinfo=UTC),
    )
    for act in acts:
        assert act.stable_id.startswith("rybnik-uchwala-")
