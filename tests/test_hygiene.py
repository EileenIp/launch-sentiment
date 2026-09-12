"""Tests for duplicate detection. No corpus and no network required."""
from src import hygiene


def test_normalise_collapses_the_variations_pasted_text_picks_up():
    variants = [
        "Sony, give us back our game!",
        "sony give us back our game",
        "SONY!!! GIVE US BACK OUR GAME!!!",
        "Sony,   give  us   back our game.",
    ]

    normalised = {hygiene.normalise(text) for text in variants}

    assert len(normalised) == 1


def test_normalise_keeps_genuinely_different_reviews_apart():
    assert hygiene.normalise("great game, terrible servers") != hygiene.normalise("great game")


def test_normalise_handles_empty_and_whitespace_only_text():
    assert hygiene.normalise("") == ""
    assert hygiene.normalise("   \n\t ") == ""
    assert hygiene.normalise(None) == ""


def test_normalise_folds_unicode_widths():
    """Pasted text from other clients can arrive full-width."""
    assert hygiene.normalise("ＳＯＮＹ") == hygiene.normalise("sony")


def test_week_of_matches_iso_weeks():
    assert hygiene.week_of("2024-05-01T12:00:00+00:00") == "2024-W18"
    assert hygiene.week_of("2024-05-06T00:00:01+00:00") == "2024-W19"
