"""Phase 3: apply the theme taxonomy and report how much it actually covers.

The number that matters here is the share of negative reviews matching no theme.
A keyword taxonomy that leaves 40% in "other" is not a taxonomy, it is a filter —
so this reports the miss rate first and surfaces the most common words among the
misses, which is what tells Eileen where the gaps are.

Run: python -m src.classify_themes
"""
from __future__ import annotations

import re
from collections import Counter

from src import config, hygiene, mine_themes, taxonomy

_WORD_EDGE = r"(?<![a-z]){}(?![a-z])"


def _compile(phrases: list[str]):
    """Word-boundary aware so 'ama' does not match 'amazing' and 'pen' does not
    match 'penalty'. Lower-cased input assumed."""
    return [re.compile(_WORD_EDGE.format(re.escape(phrase))) for phrase in phrases]


COMPILED = {theme: _compile(phrases) for theme, phrases in taxonomy.THEMES.items()}


def themes_for(text: str) -> set:
    lowered = text.lower()
    return {
        theme
        for theme, patterns in COMPILED.items()
        if any(pattern.search(lowered) for pattern in patterns)
    }


def run(appid: int | None = None, top_missed: int = 30):
    appid = appid or config.TARGET_APPID

    theme_counts: Counter = Counter()
    per_week: dict = {}
    negatives = 0
    matched = 0
    missed_terms: Counter = Counter()
    missed_examples: list = []

    for review in hygiene.iter_raw_reviews(appid):
        if review.get("language") not in config.SCORING_LANGUAGES:
            continue
        if review["voted_up"]:
            continue
        text = (review.get("review") or "").strip()
        if not text:
            continue

        negatives += 1
        found = themes_for(text)
        week = hygiene.week_of(review["timestamp_created"])
        bucket = per_week.setdefault(week, Counter())

        if found:
            matched += 1
            theme_counts.update(found)
            bucket.update(found)
        else:
            bucket["unthemed"] += 1
            missed_terms.update(set(mine_themes.tokenise(text)))
            if len(missed_examples) < 8 and 40 < len(text) < 200:
                missed_examples.append(" ".join(text.split()))

    print(f"\nnegative English reviews: {negatives:,}")
    print(f"matched at least one theme: {matched:,} ({matched/max(negatives,1):.1%})")
    print(f"unthemed: {negatives-matched:,} ({(negatives-matched)/max(negatives,1):.1%})")

    print("\n--- theme volumes (a review can carry several) ---")
    for theme, count in theme_counts.most_common():
        print(f"  {theme:<18} {count:>7,}  {count/max(negatives,1):>6.1%} of negatives")

    print(f"\n--- most common words in unthemed reviews (gap check) ---")
    for term, count in missed_terms.most_common(top_missed):
        print(f"  {term:<22} {count:>6,}")

    print("\n--- examples of unthemed complaints ---")
    for example in missed_examples:
        print(f"  {example[:150]!r}")

    return theme_counts, per_week, negatives


if __name__ == "__main__":
    run()
