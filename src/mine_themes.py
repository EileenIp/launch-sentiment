"""Phase 3 prep: surface the words complaints actually use, for Eileen to sort into themes.

The spec puts the taxonomy in Eileen's hands because an agent's guess at what a
"monetisation complaint" looks like for this game would be generic. This does not
guess — it measures which terms are distinctive of negative reviews in THIS corpus,
so the seed keywords get edited from evidence rather than invented.

Negative/positive is split on Steam's own thumbs-down, deliberately NOT on a
sentiment scorer: the scorer choice is still open at Checkpoint 2, and seeding a
taxonomy from a scorer that might be rejected would bake that choice in early.

Run: python -m src.mine_themes
"""
from __future__ import annotations

import re
from collections import Counter

from src import config, hygiene

TOKEN = re.compile(r"[a-z][a-z'\-]+")
MIN_OCCURRENCES = 150
PRUNE_EVERY = 100_000

# Deliberately short: only words that carry no complaint signal in any theme. Words
# like "crash", "price", "server" must survive, and so must hedges like "but".
STOPWORDS = {
    "the", "a", "an", "and", "or", "if", "of", "to", "in", "is", "it", "its", "this", "that",
    "was", "were", "be", "been", "are", "am", "i", "im", "ive", "you", "your", "they", "them",
    "their", "we", "our", "us", "he", "she", "his", "her", "for", "on", "at", "as", "with",
    "so", "just", "not", "no", "do", "does", "did", "have", "has", "had", "my", "me", "all",
    "can", "will", "would", "there", "what", "when", "who", "how", "from", "by", "out", "up",
    "get", "got", "one", "like", "about", "than", "then", "now", "also", "any", "more", "most",
}


def tokenise(text: str) -> list[str]:
    return [word for word in TOKEN.findall(text.lower()) if word not in STOPWORDS and len(word) > 2]


def _prune(counter: Counter, floor: int = 2) -> None:
    for key, count in list(counter.items()):
        if count < floor:
            del counter[key]


def mine(appid: int | None = None, top_n: int = 45):
    appid = appid or config.TARGET_APPID

    negative: Counter = Counter()
    positive: Counter = Counter()
    neg_docs = pos_docs = 0
    examples: dict = {}

    for index, review in enumerate(hygiene.iter_raw_reviews(appid), start=1):
        if review.get("language") not in config.SCORING_LANGUAGES:
            continue
        text = (review.get("review") or "").strip()
        if not text:
            continue

        words = tokenise(text)
        if not words:
            continue
        terms = set(words) | {f"{a} {b}" for a, b in zip(words, words[1:])}

        if review["voted_up"]:
            pos_docs += 1
            positive.update(terms)
        else:
            neg_docs += 1
            negative.update(terms)
            for term in terms:
                if term not in examples and len(text) < 300:
                    examples[term] = text

        if index % PRUNE_EVERY == 0:
            _prune(negative)
            _prune(positive)

    rows = []
    for term, neg_count in negative.items():
        if neg_count < MIN_OCCURRENCES:
            continue
        pos_count = positive.get(term, 0)
        neg_rate = neg_count / max(neg_docs, 1)
        pos_rate = (pos_count + 1) / max(pos_docs, 1)
        rows.append(
            {
                "term": term,
                "negative": neg_count,
                "positive": pos_count,
                "lift": neg_rate / pos_rate,
                "example": examples.get(term, ""),
            }
        )

    rows.sort(key=lambda row: -row["lift"])
    return rows[:top_n], neg_docs, pos_docs


def print_candidates(rows, neg_docs, pos_docs) -> None:
    print(f"\nnegative reviews: {neg_docs:,}   positive: {pos_docs:,}")
    print("\nterms most distinctive of complaints (lift = how much likelier in a negative review)\n")
    print(f"  {'term':<28} {'neg':>7} {'pos':>7} {'lift':>7}")
    for row in rows:
        print(f"  {row['term']:<28} {row['negative']:>7,} {row['positive']:>7,} {row['lift']:>7.1f}x")


if __name__ == "__main__":
    rows, neg_docs, pos_docs = mine()
    print_candidates(rows, neg_docs, pos_docs)
