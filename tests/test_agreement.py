"""Tests for the agreement calculation. No corpus, no scores file."""
import csv

from src import agreement, scoring


def _write_sample(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["recommendationid", "review", "label"])
        writer.writerows(rows)
    return path


def test_agreement_counts_exact_matches():
    labels = {"1": "positive", "2": "negative", "3": "mixed-neutral"}
    preds = {"1": "positive", "2": "negative", "3": "positive"}

    result = agreement.agreement(labels, preds)

    assert result["n"] == 3
    assert result["agree"] == 2
    assert result["rate"] == 2 / 3


def test_agreement_only_scores_reviews_present_in_both():
    """A scorer that has not reached part of the sample must not be penalised for it."""
    labels = {"1": "positive", "2": "negative"}
    preds = {"1": "positive"}

    result = agreement.agreement(labels, preds)

    assert result["n"] == 1
    assert result["rate"] == 1.0


def test_agreement_reports_per_class_and_confusion():
    labels = {"1": "negative", "2": "negative", "3": "positive"}
    preds = {"1": "negative", "2": "mixed-neutral", "3": "positive"}

    result = agreement.agreement(labels, preds)

    assert result["per_class"]["negative"] == {"n": 2, "agree": 1, "rate": 0.5}
    assert result["confusion"]["negative -> mixed-neutral"] == 1


def test_agreement_handles_no_overlap():
    assert agreement.agreement({"1": "positive"}, {})["n"] == 0


def test_load_labels_skips_blanks_and_junk(tmp_path):
    path = _write_sample(
        tmp_path / "s.csv",
        [["1", "great", "positive"], ["2", "bad", ""], ["3", "meh", "banana"], ["4", "ok", "NEGATIVE"]],
    )

    labels = agreement.load_labels(path)

    assert labels == {"1": "positive", "4": "negative"}, "blank and invalid labels must be skipped"


def test_load_labels_is_case_insensitive(tmp_path):
    path = _write_sample(tmp_path / "s.csv", [["1", "x", "  Mixed-Neutral "]])

    assert agreement.load_labels(path) == {"1": "mixed-neutral"}


def test_contrastive_pattern_finds_hedges_not_substrings():
    assert agreement.CONTRASTIVE.search("great game but the servers die")
    assert agreement.CONTRASTIVE.search("Fun, however it crashes")
    # "but" inside "butter" / "debut" must not count as a hedge.
    assert not agreement.CONTRASTIVE.search("the debut was smooth")
    assert not agreement.CONTRASTIVE.search("butter smooth framerate")


def test_label_vocabulary_matches_the_scorers():
    assert agreement.VALID_LABELS == {scoring.POSITIVE, scoring.NEGATIVE, scoring.MIXED}


def test_import_merges_labels_into_the_csv(tmp_path):
    from src import import_labels

    path = _write_sample(tmp_path / "s.csv", [["1", "great", ""], ["2", "bad", ""]])
    result = import_labels.merge('{"1": "positive", "2": "Negative"}', path)

    assert result == {"applied": 2, "total": 2}
    assert agreement.load_labels(path) == {"1": "positive", "2": "negative"}


def test_import_refuses_unknown_ids(tmp_path):
    import pytest
    from src import import_labels

    path = _write_sample(tmp_path / "s.csv", [["1", "great", ""]])

    with pytest.raises(SystemExit):
        import_labels.merge('{"999": "positive"}', path)


def test_import_refuses_invalid_labels(tmp_path):
    import pytest
    from src import import_labels

    path = _write_sample(tmp_path / "s.csv", [["1", "great", ""]])

    with pytest.raises(SystemExit):
        import_labels.merge('{"1": "banana"}', path)


def test_import_preserves_review_text_including_commas_and_quotes(tmp_path):
    import csv as _csv
    from src import import_labels

    tricky = 'Great game, "really" — but, servers'
    path = _write_sample(tmp_path / "s.csv", [["1", tricky, ""]])
    import_labels.merge('{"1": "mixed-neutral"}', path)

    with open(path, encoding="utf-8") as handle:
        assert list(_csv.DictReader(handle))[0]["review"] == tricky
