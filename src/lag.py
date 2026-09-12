"""Phase 4: does any complaint theme move before the aggregate score does?

The claim this project exists to test. It is stated so it can fail: if no theme
leads, that is the finding, and the spec is explicit that a defensible null beats
an overstated lead.

Method, and the reasons for each choice:

  * Both series are differenced (day-over-day change) before correlating. Levels
    are dominated by a single enormous event, so correlating levels would mostly
    measure "both series have a spike in the same week" rather than which moved
    first.
  * Theme COMPOSITION (share of that day's negatives) is used, not volume. Volume
    and the aggregate score are both functions of how many people were angry, so
    their correlation is guaranteed before any data is examined.
  * A positive lead means the theme moved FIRST. Concretely: correlation between
    the theme's change on day d and the score's change on day d+k, for k days.
  * Only days with enough reviews to be stable are used, since a day with nine
    negatives produces a share that swings on one review.

Run: python -m src.lag
"""
from __future__ import annotations

import math

from src import config, taxonomy, timeseries

MIN_REVIEWS_PER_DAY = 200
MAX_LAG_DAYS = 14


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0


def _diff(values: list[float]) -> list[float]:
    return [b - a for a, b in zip(values, values[1:])]


def usable_days(rows: list[dict], min_reviews: int = MIN_REVIEWS_PER_DAY) -> list[dict]:
    """Contiguous run of days big enough for a daily share to be stable."""
    return [r for r in rows if r["reviews"] >= min_reviews and r["negatives"] > 0]


def cross_correlate(theme_series: list[float], score_series: list[float], max_lag: int = MAX_LAG_DAYS):
    """Correlation of theme change at day d with score change at day d+k.

    k > 0 means the theme moved first — the lead the project is looking for.
    """
    dt, ds = _diff(theme_series), _diff(score_series)
    out = []
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            a, b = dt[: len(dt) - k], ds[k:]
        else:
            a, b = dt[-k:], ds[: len(ds) + k]
        if len(a) >= 10:
            out.append({"lag": k, "r": _pearson(a, b), "n": len(a)})
    return out


def null_distribution(theme_series: list[float], score_series: list[float],
                      trials: int = 1000, max_lag: int = MAX_LAG_DAYS, seed: int | None = None):
    """How strong a 'best lag' does chance produce for this pair of series?

    Reporting the most negative correlation across 29 lags means taking the extreme
    of 29 attempts, which finds something even in noise. This builds the null for
    exactly that statistic: rotate the theme series by a random offset — preserving
    its own day-to-day autocorrelation while destroying any real alignment with the
    score — and record the best lag correlation each time.

    A rotation, not a shuffle: shuffling would destroy the autocorrelation too, which
    makes the null far too easy to beat and would dress up noise as a finding.
    """
    import random

    rng = random.Random(config.RANDOM_SEED if seed is None else seed)
    n = len(theme_series)
    best_rs = []
    for _ in range(trials):
        offset = rng.randint(max_lag + 1, n - max_lag - 1)
        rotated = theme_series[offset:] + theme_series[:offset]
        lags = cross_correlate(rotated, score_series, max_lag)
        if lags:
            best_rs.append(min(row["r"] for row in lags))
    return sorted(best_rs)


def analyse(appid: int | None = None, min_reviews: int = MIN_REVIEWS_PER_DAY) -> dict:
    rows = usable_days(timeseries.load(appid)["days"], min_reviews)
    score = [r["positive_share"] for r in rows]

    results = {}
    for theme in taxonomy.THEMES:
        series = [r[f"share_{theme}"] for r in rows]
        lags = cross_correlate(series, score)
        if not lags:
            continue
        # The lead is only interesting if the theme rising goes with the score
        # falling, i.e. a negative correlation. Rank by that, not by magnitude.
        best = min(lags, key=lambda row: row["r"])
        at_zero = next((row["r"] for row in lags if row["lag"] == 0), 0.0)
        results[theme] = {"best": best, "at_zero": at_zero, "lags": lags}

    return {"days": len(rows), "span": (rows[0]["date"], rows[-1]["date"]), "themes": results}


def report(appid: int | None = None) -> None:
    result = analyse(appid)
    print(f"{result['days']} days with {MIN_REVIEWS_PER_DAY}+ reviews, "
          f"{result['span'][0]} to {result['span'][1]}")
    print("\nlag > 0 means the theme moved BEFORE the score. r < 0 means theme up, score down.\n")
    print(f"  {'theme':<18} {'best lag':>9} {'r':>7} {'r at lag 0':>11}")

    ranked = sorted(result["themes"].items(), key=lambda kv: kv[1]["best"]["r"])
    for theme, info in ranked:
        best = info["best"]
        lead = "leads" if best["lag"] > 0 else ("same day" if best["lag"] == 0 else "trails")
        print(f"  {theme:<18} {best['lag']:>+6}d {lead:<6} {best['r']:>+6.2f} {info['at_zero']:>+10.2f}")

    print("\nEILEEN DECIDES whether the leading-indicator claim holds. A correlation")
    print("near zero at every lag, or a best lag of 0, is a null — write it as one.")


if __name__ == "__main__":
    report()
