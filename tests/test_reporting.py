from datetime import date

from bip_scraper.models import CityDiff, CitySlug, DailyDiffReport
from bip_scraper.reporting import format_mattermost_report


def test_format_mattermost_report_includes_totals_and_city_rows() -> None:
    report = DailyDiffReport(
        run_date=date(2026, 2, 16),
        compared_to_date=date(2026, 2, 15),
        total_new=3,
        city_diffs=[
            CityDiff(
                city=CitySlug.KATOWICE,
                previous_count=10,
                current_count=12,
                new_count=2,
                new_acts=[],
            ),
            CityDiff(
                city=CitySlug.CHORZOW,
                previous_count=6,
                current_count=7,
                new_count=1,
                new_acts=[],
            ),
        ],
    )

    message = format_mattermost_report(report)

    assert "Total new legal acts: 3" in message
    assert "- katowice: 2" in message
    assert "- chorzow: 1" in message
