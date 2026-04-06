from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from bip_scraper.cities import ALL_CITY_SCRAPERS
from bip_scraper.config import Settings
from bip_scraper.diff import build_daily_report
from bip_scraper.models import CitySlug, CitySnapshot, DailySnapshot
from bip_scraper.notify import post_via_api, post_via_webhook
from bip_scraper.reporting import format_mattermost_report
from bip_scraper.snapshot import load_snapshot, save_snapshot


def build_snapshot(now: datetime) -> DailySnapshot:
    city_snapshots: dict[CitySlug, CitySnapshot] = {}
    for scraper in ALL_CITY_SCRAPERS:
        acts = scraper.scrape_acts(now=now)
        city_snapshots[scraper.city] = CitySnapshot(
            city=scraper.city,
            collected_at=now,
            acts=acts,
        )
    return DailySnapshot(run_date=now.date(), generated_at=now, cities=city_snapshots)


def notify_mattermost(settings: Settings, message: str) -> None:
    if settings.mattermost_mode == "disabled":
        return
    if settings.mattermost_mode == "webhook":
        post_via_webhook(
            webhook_url=str(settings.mattermost_webhook_url),
            message=message,
            timeout_seconds=settings.request_timeout_seconds,
        )
        return
    post_via_api(
        api_base_url=str(settings.mattermost_api_url),
        token=settings.mattermost_token or "",
        channel_id=settings.mattermost_channel_id or "",
        message=message,
        timeout_seconds=settings.request_timeout_seconds,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BIP Śląskie daily scraper and report runner")
    parser.add_argument("--output", type=Path, required=True, help="Path to current snapshot JSON")
    parser.add_argument(
        "--previous", type=Path, required=True, help="Path to previous snapshot JSON"
    )
    parser.add_argument(
        "--report", type=Path, required=True, help="Path to output daily report JSON"
    )
    parser.add_argument("--notify", action="store_true", help="Post report to Mattermost")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    now = datetime.now(tz=UTC)
    settings = Settings()
    current_snapshot = build_snapshot(now)
    previous_snapshot = load_snapshot(args.previous)
    daily_report = build_daily_report(current_snapshot, previous_snapshot)

    save_snapshot(args.output, current_snapshot)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(daily_report.model_dump_json(indent=2), encoding="utf-8")

    if args.notify:
        notify_mattermost(settings, format_mattermost_report(daily_report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
