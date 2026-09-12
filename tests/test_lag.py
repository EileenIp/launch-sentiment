"""Tests for the lag analysis. Synthetic series with a known answer."""
import pytest

from src import lag


def test_pearson_matches_known_values():
    assert lag._pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert lag._pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)


def test_pearson_is_zero_for_a_flat_series():
    assert lag._pearson([1, 2, 3], [5, 5, 5]) == 0.0


def test_diff_returns_day_over_day_change():
    assert lag._diff([1.0, 3.0, 2.0]) == [2.0, -1.0]


def test_cross_correlate_recovers_a_planted_lead():
    """Theme rises 3 days before the score falls; the analysis must find lag +3."""
    n = 60
    theme = [0.1] * n
    score = [0.8] * n
    for step, day in enumerate(range(10, 20)):
        theme[day] = 0.1 + 0.02 * (step + 1)
        score[day + 3] = 0.8 - 0.02 * (step + 1)

    lags = lag.cross_correlate(theme, score, max_lag=10)
    best = min(lags, key=lambda row: row["r"])

    assert best["lag"] == 3, f"expected a 3-day lead, found {best['lag']}"
    assert best["r"] < -0.5


def test_cross_correlate_reports_lag_zero_for_simultaneous_movement():
    n = 50
    theme = [0.1] * n
    score = [0.8] * n
    for day in range(10, 20):
        theme[day] = 0.3
        score[day] = 0.6

    best = min(lag.cross_correlate(theme, score, max_lag=8), key=lambda row: row["r"])

    assert best["lag"] == 0


def test_cross_correlate_finds_nothing_in_noise():
    """A null must look like a null — flat series must not produce a strong lead."""
    theme = [0.1, 0.11, 0.09, 0.1, 0.11, 0.09] * 8
    score = [0.8] * 48

    best = min(lag.cross_correlate(theme, score, max_lag=6), key=lambda row: row["r"])

    assert abs(best["r"]) < 0.3


def test_usable_days_drops_thin_and_complaint_free_days():
    rows = [
        {"reviews": 500, "negatives": 10},
        {"reviews": 10, "negatives": 5},      # too few reviews
        {"reviews": 900, "negatives": 0},     # no negatives, share undefined
    ]

    assert len(lag.usable_days(rows, min_reviews=200)) == 1


def test_positive_lag_means_theme_first():
    """Guards the sign convention — reversing it would invert every conclusion."""
    n = 40
    theme = [0.1] * n
    score = [0.8] * n
    theme[10] = 0.5
    score[15] = 0.4

    best = min(lag.cross_correlate(theme, score, max_lag=10), key=lambda row: row["r"])

    assert best["lag"] > 0
