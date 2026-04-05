from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities.siemianowice import SiemianowiceScraper

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def test_siemianowice_parses_acts() -> None:
    scraper = SiemianowiceScraper()
    acts_html = _read_fixture("siemianowice_acts.html")

    acts = scraper._parse_acts_from_html(acts_html, now=datetime(2026, 1, 29, tzinfo=UTC))

    assert len(acts) == 3
    for act in acts:
        assert act.stable_id.startswith("siemianowice-uchwala-")
        assert "UCHWAŁA" in act.title
        assert act.source_url is not None

    # Check first act
    assert acts[0].title.startswith("UCHWAŁA Nr I/1/2026")
    assert acts[0].published_at.year == 2026
