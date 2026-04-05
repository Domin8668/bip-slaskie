from __future__ import annotations

from pathlib import Path

from bip_scraper.models import DailySnapshot


def save_snapshot(path: Path, snapshot: DailySnapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        snapshot.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )


def load_snapshot(path: Path) -> DailySnapshot | None:
    if not path.exists():
        return None
    return DailySnapshot.model_validate_json(path.read_text(encoding="utf-8"))
