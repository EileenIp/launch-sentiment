"""Tests for the scorer interface. No model download, no network."""
import pytest

from src import scoring


class FakeScorer:
    """Stands in for either real scorer — the point is the shared contract."""

    name = "fake"

    def score_batch(self, texts):
        return [{"label": scoring.POSITIVE, "polarity": 1.0} for _ in texts]


def test_vader_labels_the_three_cases():
    vader = scoring.VaderScorer()

    results = vader.score_batch(
        [
            "This game is absolutely fantastic, best shooter in years",
            "Broken garbage, crashes every five minutes, do not buy",
            "The game exists and has servers.",
        ]
    )

    assert results[0]["label"] == scoring.POSITIVE
    assert results[1]["label"] == scoring.NEGATIVE
    assert {r["label"] for r in results} <= {scoring.POSITIVE, scoring.NEGATIVE, scoring.MIXED}


def test_vader_polarity_is_signed_and_bounded():
    vader = scoring.VaderScorer()

    results = vader.score_batch(["wonderful, i love it", "awful, i hate it"])

    assert results[0]["polarity"] > 0 > results[1]["polarity"]
    assert all(-1.0 <= r["polarity"] <= 1.0 for r in results)


def test_every_scorer_returns_the_same_schema():
    """The spec's requirement: identical schema from both models."""
    vader = scoring.VaderScorer()
    fake = FakeScorer()

    a = vader.score_batch(["great game"])[0]
    b = fake.score_batch(["great game"])[0]

    assert set(a) == set(b) == {"label", "polarity"}
    assert isinstance(a["polarity"], float)


def test_vader_handles_empty_and_symbol_only_text():
    vader = scoring.VaderScorer()

    results = vader.score_batch(["", "!!!!", "????"])

    assert len(results) == 3
    assert all(r["label"] == scoring.MIXED for r in results)


def test_already_scored_reads_ids_and_survives_a_truncated_final_line(tmp_path):
    """An interrupted run leaves a partial line; resuming must not crash on it."""
    path = tmp_path / "scores.jsonl"
    path.write_text(
        '{"recommendationid": "1", "label": "positive", "polarity": 0.5}\n'
        '{"recommendationid": "2", "label": "negative", "polarity": -0.5}\n'
        '{"recommendationid": "3", "label": "posi',
        encoding="utf-8",
    )

    assert scoring.already_scored(path) == {"1", "2"}


def test_already_scored_on_a_missing_file_is_empty(tmp_path):
    assert scoring.already_scored(tmp_path / "nope.jsonl") == set()


def test_scorer_labels_match_the_hand_label_vocabulary():
    """Agreement is only meaningful if both sides use the same three words."""
    assert {scoring.POSITIVE, scoring.NEGATIVE, scoring.MIXED} == {
        "positive",
        "negative",
        "mixed-neutral",
    }
