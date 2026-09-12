"""Phase 1: find the copypasta before deciding what to do about it.

Detection is deliberately transparent rather than clever — reviews are normalised
(lowercased, punctuation and runs of whitespace collapsed) and grouped by exact
match on the result. Copypasta during a review-bomb is literally pasted, so this
catches the bulk of it while staying explainable in an interview, which a learned
near-duplicate model would not be.

Reports before it changes anything. Nothing here filters or reweights the corpus.

Run: python -m src.hygiene
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from src import config, pull_window

_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Casefold, strip punctuation and collapse whitespace, so pasted variants collide."""
    folded = unicodedata.normalize("NFKC", text or "").casefold()
    return _SPACE.sub(" ", _PUNCT.sub(" ", folded)).strip()


def iter_raw_reviews(appid: int):
    """Stream the corpus — 860k reviews with full text will not fit comfortably in memory."""
    path = pull_window.reviews_path(appid)
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


def week_of(iso_timestamp: str) -> str:
    from datetime import datetime

    moment = datetime.fromisoformat(iso_timestamp)
    year, week, _ = moment.isocalendar()
    return f"{year}-W{week:02d}"


@dataclass
class DuplicateReport:
    total: int = 0
    blank: int = 0
    distinct_texts: int = 0
    duplicated_reviews: int = 0
    groups_of_2_plus: int = 0
    largest_groups: list = field(default_factory=list)
    per_week: dict = field(default_factory=dict)
    short_reviews: int = 0

    @property
    def duplicate_share(self) -> float:
        return self.duplicated_reviews / self.total if self.total else 0.0

    def print_report(self) -> None:
        print("\n=== copypasta / duplicate scan ===")
        print(f"reviews scanned: {self.total:,}")
        print(f"blank after normalising: {self.blank:,}")
        print(f"distinct normalised texts: {self.distinct_texts:,}")
        print(
            f"reviews sharing their text with at least one other: "
            f"{self.duplicated_reviews:,} ({self.duplicate_share:.1%})"
        )
        print(f"repeated-text groups: {self.groups_of_2_plus:,}")
        print(f"reviews of 3 words or fewer: {self.short_reviews:,} "
              f"({self.short_reviews / max(self.total,1):.1%})")

        print("\n--- largest identical-text groups ---")
        for count, sample in self.largest_groups:
            shown = sample if len(sample) <= 90 else sample[:87] + "..."
            print(f"  {count:>7,}x  {shown!r}")

        print("\n--- duplicate share by week ---")
        for week in sorted(self.per_week):
            row = self.per_week[week]
            share = row["duplicated"] / row["total"] if row["total"] else 0.0
            marker = "  <-- spike" if row["total"] > 100_000 else ""
            print(f"  {week}  {row['total']:>7,} reviews  {share:>6.1%} duplicated{marker}")


def scan(appid: int | None = None, top_n: int = 12) -> DuplicateReport:
    appid = appid or config.TARGET_APPID
    report = DuplicateReport()

    counts: Counter = Counter()
    per_week_total: Counter = Counter()
    week_by_text: defaultdict = defaultdict(Counter)

    for raw in iter_raw_reviews(appid):
        report.total += 1
        text = normalise(raw.get("review", ""))
        week = week_of(raw["timestamp_created"])
        per_week_total[week] += 1

        if not text:
            report.blank += 1
            continue
        if len(text.split()) <= 3:
            report.short_reviews += 1

        counts[text] += 1
        week_by_text[text][week] += 1

    report.distinct_texts = len(counts)
    repeated = {text: n for text, n in counts.items() if n > 1}
    report.groups_of_2_plus = len(repeated)
    report.duplicated_reviews = sum(repeated.values())
    report.largest_groups = [(n, text) for text, n in counts.most_common(top_n)]

    per_week = {week: {"total": total, "duplicated": 0} for week, total in per_week_total.items()}
    for text in repeated:
        for week, n in week_by_text[text].items():
            per_week[week]["duplicated"] += n
    report.per_week = per_week

    return report


if __name__ == "__main__":
    scan().print_report()
