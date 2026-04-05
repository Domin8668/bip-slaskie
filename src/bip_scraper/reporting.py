from __future__ import annotations

from bip_scraper.models import DailyDiffReport


def format_mattermost_report(report: DailyDiffReport) -> str:
    baseline = report.compared_to_date.isoformat() if report.compared_to_date else "no baseline"
    lines = [
        f"BIP daily report ({report.run_date.isoformat()}, compare: {baseline})",
        f"Total new legal acts: {report.total_new}",
    ]
    for city_diff in report.city_diffs:
        lines.append(f"- {city_diff.city.value}: {city_diff.new_count}")
    return "\n".join(lines)
