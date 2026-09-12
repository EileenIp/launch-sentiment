"""Phase 2: draw the 200-review validation set for Eileen to hand-label.

Deliberately blind: the CSV carries the review text and nothing else. Steam's own
thumbs-up flag is NOT included, because seeing it would anchor the labels to the
thing the scorers are being validated against. The flag is rejoined by id after
labelling, from the corpus.

Seeded, so the same 200 reviews come back on every run.

Run: python -m src.sample_validation
"""
from __future__ import annotations

import csv
import random

from src import config, hygiene, pull_window

SAMPLE_SIZE = 200
VALIDATION_DIR = config.PROJECT_ROOT / "data" / "validation"
SAMPLE_PATH = VALIDATION_DIR / "validation_sample.csv"

LABEL_GUIDE = "positive | negative | mixed-neutral"


def eligible_reviews(appid: int):
    """Reviews eligible for hand-labelling: in a scored language, and substantive.

    Both filters are Eileen's Phase 1 decisions (see config): English only, because
    VADER cannot meaningfully score anything else, and 5+ words, because shorter
    reviews are trivially classified by every scorer and so cannot discriminate
    between them.
    """
    for review in hygiene.iter_raw_reviews(appid):
        if review.get("language") not in config.SCORING_LANGUAGES:
            continue
        text = (review.get("review") or "").strip()
        if len(text.split()) < config.VALIDATION_MIN_WORDS:
            continue
        yield review["recommendationid"], text, review["timestamp_created"]


def draw(appid: int | None = None, size: int = SAMPLE_SIZE, seed: int | None = None):
    appid = appid or config.TARGET_APPID
    seed = config.RANDOM_SEED if seed is None else seed

    population = list(eligible_reviews(appid))
    rng = random.Random(seed)
    sample = rng.sample(population, size)
    # Chronological order reads more naturally than random order when labelling.
    sample.sort(key=lambda row: row[2])
    return sample, len(population)


def write_sample(sample, path=SAMPLE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["recommendationid", "review", "label"])
        for rid, text, _ in sample:
            writer.writerow([rid, text, ""])


def describe(sample, population_size: int) -> None:
    words = [len(text.split()) for _, text, _ in sample]
    trivial = sum(1 for count in words if count <= 3)
    weeks = {}
    for _, _, created in sample:
        week = hygiene.week_of(created)
        weeks[week] = weeks.get(week, 0) + 1

    print(f"drew {len(sample)} of {population_size:,} reviews with text (seed {config.RANDOM_SEED})")
    print(f"median length: {sorted(words)[len(words)//2]} words")
    print(f"three words or fewer: {trivial} ({trivial/len(sample):.0%})")
    print("\nweeks represented (top 6):")
    for week, count in sorted(weeks.items(), key=lambda kv: -kv[1])[:6]:
        print(f"  {week}  {count}")


if __name__ == "__main__":
    sample, population_size = draw()
    write_sample(sample)
    describe(sample, population_size)
    print(f"\nwrote {SAMPLE_PATH}")
    print(f"fill the 'label' column with: {LABEL_GUIDE}")
