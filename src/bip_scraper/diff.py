from __future__ import annotations

from bip_scraper.models import CityDiff, CitySlug, DailyDiffReport, DailySnapshot


def _new_city_diff(
    city: CitySlug,
    current: DailySnapshot,
    previous: DailySnapshot | None,
) -> CityDiff:
    current_city = current.cities[city]
    previous_city = previous.cities.get(city) if previous is not None else None
    current_map = {act.stable_id: act for act in current_city.acts}
    previous_ids = set()
    if previous_city is not None:
        previous_ids = {act.stable_id for act in previous_city.acts}

    new_ids = sorted(current_map.keys() - previous_ids)
    return CityDiff(
        city=city,
        previous_count=len(previous_ids),
        current_count=len(current_map),
        new_count=len(new_ids),
        new_acts=[current_map[stable_id] for stable_id in new_ids],
    )


def build_daily_report(current: DailySnapshot, previous: DailySnapshot | None) -> DailyDiffReport:
    city_diffs = [_new_city_diff(city, current, previous) for city in sorted(current.cities.keys())]
    total_new = sum(city_diff.new_count for city_diff in city_diffs)
    compared_to_date = previous.run_date if previous is not None else None

    return DailyDiffReport(
        run_date=current.run_date,
        compared_to_date=compared_to_date,
        total_new=total_new,
        city_diffs=city_diffs,
    )
