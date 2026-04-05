from datetime import UTC, date, datetime

from bip_scraper.diff import build_daily_report
from bip_scraper.models import CitySlug, CitySnapshot, DailySnapshot, LegalAct


def test_build_daily_report_counts_only_new_items() -> None:
    now = datetime(2026, 2, 16, 12, 0, tzinfo=UTC)
    old_act = LegalAct(
        stable_id="kat-2026-001",
        title="Old",
        published_at=now,
        source_url="https://example.com/old",
    )
    new_act = LegalAct(
        stable_id="kat-2026-002",
        title="New",
        published_at=now,
        source_url="https://example.com/new",
    )

    previous = DailySnapshot(
        run_date=date(2026, 2, 15),
        generated_at=now,
        cities={
            CitySlug.KATOWICE: CitySnapshot(
                city=CitySlug.KATOWICE,
                collected_at=now,
                acts=[old_act],
            ),
            CitySlug.CHORZOW: CitySnapshot(city=CitySlug.CHORZOW, collected_at=now, acts=[]),
            CitySlug.SWIETOCHLOWICE: CitySnapshot(
                city=CitySlug.SWIETOCHLOWICE, collected_at=now, acts=[]
            ),
            CitySlug.SIEMIANOWICE: CitySnapshot(
                city=CitySlug.SIEMIANOWICE,
                collected_at=now,
                acts=[],
            ),
        },
    )

    current = DailySnapshot(
        run_date=date(2026, 2, 16),
        generated_at=now,
        cities={
            CitySlug.KATOWICE: CitySnapshot(
                city=CitySlug.KATOWICE, collected_at=now, acts=[old_act, new_act]
            ),
            CitySlug.CHORZOW: CitySnapshot(city=CitySlug.CHORZOW, collected_at=now, acts=[]),
            CitySlug.SWIETOCHLOWICE: CitySnapshot(
                city=CitySlug.SWIETOCHLOWICE, collected_at=now, acts=[]
            ),
            CitySlug.SIEMIANOWICE: CitySnapshot(
                city=CitySlug.SIEMIANOWICE,
                collected_at=now,
                acts=[],
            ),
        },
    )

    report = build_daily_report(current, previous)
    assert report.total_new == 1
    katowice = next(
        city_diff
        for city_diff in report.city_diffs
        if city_diff.city == CitySlug.KATOWICE
    )
    assert katowice.new_count == 1
    assert katowice.new_acts[0].stable_id == "kat-2026-002"
