"""Phase 2: two sentiment scorers behind one interface.

VADER is a lexicon — transparent, instant, and explainable line by line, which is
exactly why it is the baseline rather than the assumption. The transformer is a
RoBERTa checkpoint fine-tuned on short informal text, which is the closest public
match to what a Steam review actually reads like.

Both return the same schema and the same three labels Eileen hand-labelled with,
so agreement is a direct comparison rather than a mapping argument:

    {"recommendationid": str, "label": "positive"|"negative"|"mixed-neutral",
     "polarity": float}   # polarity in [-1, 1], comparable in sign across scorers

Scores are written to disk once and never recomputed — the transformer pass is the
only expensive step in this project.

Run: python -m src.scoring vader
     python -m src.scoring transformer [limit]
"""
from __future__ import annotations

import json
import sys
import time

from src import config, hygiene, pull_window

POSITIVE = "positive"
NEGATIVE = "negative"
MIXED = "mixed-neutral"

# VADER's own documented thresholds, not tuned here — tuning them against the
# validation set would be fitting the baseline to the test.
VADER_POSITIVE_CUTOFF = 0.05
VADER_NEGATIVE_CUTOFF = -0.05

TRANSFORMER_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
TRANSFORMER_BATCH = 64
TRANSFORMER_MAX_TOKENS = 128


def scores_path(appid: int, scorer_name: str):
    return config.PROCESSED_DATA_DIR / f"scores_{scorer_name}_{appid}.jsonl"


class VaderScorer:
    name = "vader"

    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        self._analyzer = SentimentIntensityAnalyzer()

    def score_batch(self, texts: list[str]) -> list[dict]:
        results = []
        for text in texts:
            compound = self._analyzer.polarity_scores(text)["compound"]
            if compound >= VADER_POSITIVE_CUTOFF:
                label = POSITIVE
            elif compound <= VADER_NEGATIVE_CUTOFF:
                label = NEGATIVE
            else:
                label = MIXED
            results.append({"label": label, "polarity": compound})
        return results


class TransformerScorer:
    name = "transformer"

    def __init__(self):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        torch.set_num_threads(max(1, (__import__("os").cpu_count() or 2) - 2))
        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(TRANSFORMER_MODEL)
        self._model = AutoModelForSequenceClassification.from_pretrained(TRANSFORMER_MODEL)
        self._model.eval()

        # Label order is the model's own, never assumed.
        self._labels = [
            self._model.config.id2label[i].lower() for i in range(self._model.config.num_labels)
        ]

    def _to_label(self, model_label: str) -> str:
        if model_label.startswith("pos"):
            return POSITIVE
        if model_label.startswith("neg"):
            return NEGATIVE
        return MIXED

    def score_batch(self, texts: list[str]) -> list[dict]:
        torch = self._torch
        encoded = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=TRANSFORMER_MAX_TOKENS,
            return_tensors="pt",
        )
        with torch.no_grad():
            logits = self._model(**encoded).logits
        probabilities = torch.softmax(logits, dim=-1)

        results = []
        for row in probabilities:
            index = int(row.argmax())
            label = self._to_label(self._labels[index])
            # One comparable number across scorers: P(positive) - P(negative).
            positive = sum(float(row[i]) for i, l in enumerate(self._labels) if l.startswith("pos"))
            negative = sum(float(row[i]) for i, l in enumerate(self._labels) if l.startswith("neg"))
            results.append({"label": label, "polarity": positive - negative})
        return results


SCORERS = {"vader": VaderScorer, "transformer": TransformerScorer}


def scorable_reviews(appid: int):
    """Every review in a scored language, with text. Length floor applies to the
    validation sample only — the corpus itself is scored whole."""
    for review in hygiene.iter_raw_reviews(appid):
        if review.get("language") not in config.SCORING_LANGUAGES:
            continue
        text = (review.get("review") or "").strip()
        if not text:
            continue
        yield review["recommendationid"], text


def already_scored(path) -> set:
    if not path.exists():
        return set()
    done = set()
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                done.add(json.loads(line)["recommendationid"])
            except (json.JSONDecodeError, KeyError):
                continue  # a partial final line from an interrupted run
    return done


def score_corpus(scorer, appid: int | None = None, limit: int | None = None, batch_size: int = 256):
    appid = appid or config.TARGET_APPID
    path = scores_path(appid, scorer.name)
    path.parent.mkdir(parents=True, exist_ok=True)

    done = already_scored(path)
    if done:
        print(f"resuming: {len(done):,} already scored")

    started = time.time()
    written = 0
    batch_ids: list[str] = []
    batch_texts: list[str] = []

    with open(path, "a", encoding="utf-8") as handle:
        def flush():
            nonlocal written, batch_ids, batch_texts
            if not batch_ids:
                return
            for rid, result in zip(batch_ids, scorer.score_batch(batch_texts)):
                handle.write(json.dumps({"recommendationid": rid, **result}) + "\n")
            written += len(batch_ids)
            handle.flush()
            elapsed = time.time() - started
            print(f"  {written:,} scored  ({written/max(elapsed,1):.0f}/s)", flush=True)
            batch_ids, batch_texts = [], []

        for rid, text in scorable_reviews(appid):
            if rid in done:
                continue
            batch_ids.append(rid)
            batch_texts.append(text)
            if len(batch_ids) >= batch_size:
                flush()
                if limit and written >= limit:
                    break
        flush()

    print(f"{scorer.name}: wrote {written:,} scores to {path}")
    return path


def _main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in SCORERS:
        print(__doc__)
        return 1
    name = argv[1]
    limit = int(argv[2]) if len(argv) > 2 else None
    batch = TRANSFORMER_BATCH if name == "transformer" else 256
    score_corpus(SCORERS[name](), limit=limit, batch_size=batch)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
