"""Phase 0: pull the full launch window, persist it, and report what came back.

The pull is resumable by construction — every page is cached on disk by
(appid, cursor, window), so re-running after an interruption re-reads the cache at
about 50x the speed of the network and continues from where it stopped.

Run: python -m src.pull_window
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from src import config, steam_fetch


def reviews_path(appid: int) -> "object":
    return config.PROCESSED_DATA_DIR / f"reviews_{appid}.jsonl"


def save_reviews(reviews: list[dict], appid: int) -> None:
    path = reviews_path(appid)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for review in reviews:
            row = dict(review)
            for key in ("timestamp_created", "timestamp_updated"):
                if isinstance(row.get(key), datetime):
                    row[key] = row[key].isoformat()
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_reviews(appid: int) -> list[dict]:
    path = reviews_path(appid)
    if not path.exists():
        return []
    reviews = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            for key in ("timestamp_created", "timestamp_updated"):
                if row.get(key):
                    row[key] = datetime.fromisoformat(row[key])
            reviews.append(row)
    return reviews


@dataclass
class IntegrityReport:
    """The churn spec's 'check before locking in a dataset' rule, applied to Steam reviews."""

    total: int = 0
    duplicate_ids: int = 0
    out_of_window: int = 0
    empty_text: int = 0
    created_equals_updated: int = 0
    distinct_timestamps: int = 0
    modal_gap_seconds: int | None = None
    modal_gap_share: float = 0.0
    languages: dict = field(default_factory=dict)
    free_copies: int = 0
    non_steam_purchase: int = 0

    def print_report(self) -> None:
        print("\n--- integrity ---")
        print(f"reviews: {self.total:,}")
        print(f"duplicate ids: {self.duplicate_ids:,}")
        print(f"outside requested window: {self.out_of_window:,}")
        print(f"empty review text: {self.empty_text:,} ({self.empty_text / max(self.total,1):.1%})")
        print(
            f"created == updated: {self.created_equals_updated:,} "
            f"({self.created_equals_updated / max(self.total,1):.1%}) — expected high, most reviews are never edited"
        )
        print(f"distinct created timestamps: {self.distinct_timestamps:,}")
        if self.modal_gap_seconds is not None:
            print(
                f"most common gap between consecutive reviews: {self.modal_gap_seconds}s "
                f"({self.modal_gap_share:.1%} of gaps)"
            )
            if self.modal_gap_share > 0.5:
                print("  WARNING: a single gap dominating means suspiciously regular spacing — investigate")
        print(f"received_for_free: {self.free_copies:,}")
        print(f"not a Steam purchase: {self.non_steam_purchase:,}")
        top = sorted(self.languages.items(), key=lambda kv: -kv[1])[:6]
        print("top languages: " + ", ".join(f"{lang} {count:,}" for lang, count in top))


def check_integrity(reviews: list[dict], since: datetime, until: datetime) -> IntegrityReport:
    report = IntegrityReport(total=len(reviews))
    if not reviews:
        return report

    ids = [r["recommendationid"] for r in reviews]
    report.duplicate_ids = len(ids) - len(set(ids))

    created = sorted(r["timestamp_created"] for r in reviews)
    report.distinct_timestamps = len(set(created))
    report.out_of_window = sum(1 for t in created if not (since <= t <= until))
    report.empty_text = sum(1 for r in reviews if not (r.get("review") or "").strip())
    report.created_equals_updated = sum(
        1 for r in reviews if r.get("timestamp_updated") == r["timestamp_created"]
    )
    report.free_copies = sum(1 for r in reviews if r.get("received_for_free"))
    report.non_steam_purchase = sum(1 for r in reviews if not r.get("steam_purchase"))
    report.languages = dict(Counter(r.get("language") for r in reviews))

    # A synthetic or machine-generated corpus tends to show one gap value dominating.
    if len(created) > 1:
        gaps = Counter(
            int((created[i + 1] - created[i]).total_seconds()) for i in range(len(created) - 1)
        )
        gap, count = gaps.most_common(1)[0]
        report.modal_gap_seconds = gap
        report.modal_gap_share = count / (len(created) - 1)

    return report


def run(appid: int | None = None, launch_date: str | None = None) -> list[dict]:
    appid = appid or config.TARGET_APPID
    launch_date = launch_date or config.TARGET_LAUNCH_DATE
    if not appid or not launch_date:
        raise SystemExit("TARGET_APPID / TARGET_LAUNCH_DATE unset — Checkpoint 0 not decided.")

    since, until = steam_fetch.window_for_launch(launch_date)
    print(f"appid {appid}: pulling [{since.date()} .. {until.date()}]")

    pages = {"n": 0}

    def progress(payload):
        pages["n"] += 1
        if pages["n"] % 50 == 0:
            print(f"  {pages['n']} pages...", flush=True)

    reviews = steam_fetch.fetch_reviews(appid, since=since, until=until, on_page=progress)
    print(f"pulled {len(reviews):,} reviews across {pages['n']} pages")

    save_reviews(reviews, appid)
    print(f"saved to {reviews_path(appid)}")

    check_integrity(reviews, since, until).print_report()

    print("\n--- weekly volumes ---")
    for row in steam_fetch.weekly_volumes(reviews):
        print(f"  {row['week']}  {row['reviews']:>7,}  {row['positive_share']:>6.1%} positive")

    return reviews


if __name__ == "__main__":
    run()
