"""Phase 4: daily series — sentiment, volume, and theme composition.

Sentiment is Steam's thumbs-up flag (Checkpoint 2), not a text scorer.

Two theme series are produced per day, and the difference between them is the whole
ballgame for the lag analysis:

  rate  - negative reviews carrying a theme, per 1,000 reviews that day. Rises when
          complaints rise, but ALSO rises simply because the day got busier.
  share - the same complaints as a fraction of that day's negatives. Composition
          only. This is the one the lag test uses, because volume and the aggregate
          score are both functions of how many people were angry that day, so
          correlating them would recover a relationship that exists by construction
          rather than one in the data.

Writes data/processed/daily_<appid>.json so the lag analysis can iterate without
re-matching 182 regexes over 123k reviews each time.

Run: python -m src.timeseries
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from src import classify_themes, config, hygiene, taxonomy


def daily_path(appid: int):
    return config.PROCESSED_DATA_DIR / f"daily_{appid}.json"


def build(appid: int | None = None) -> dict:
    appid = appid or config.TARGET_APPID

    days: dict = defaultdict(lambda: {
        "reviews_all": 0, "positive_all": 0,      # every language
        "reviews": 0, "positive": 0,              # English only
        "negatives": 0, "themes": Counter(),
    })

    for review in hygiene.iter_raw_reviews(appid):
        date = review["timestamp_created"][:10]
        bucket = days[date]
        up = bool(review["voted_up"])

        bucket["reviews_all"] += 1
        bucket["positive_all"] += int(up)

        if review.get("language") not in config.SCORING_LANGUAGES:
            continue
        bucket["reviews"] += 1
        bucket["positive"] += int(up)

        if up:
            continue
        text = (review.get("review") or "").strip()
        if not text:
            continue
        bucket["negatives"] += 1
        bucket["themes"].update(classify_themes.themes_for(text))

    rows = []
    for date in sorted(days):
        d = days[date]
        row = {
            "date": date,
            "reviews_all": d["reviews_all"],
            "positive_share_all": d["positive_all"] / d["reviews_all"] if d["reviews_all"] else None,
            "reviews": d["reviews"],
            "negatives": d["negatives"],
            "positive_share": d["positive"] / d["reviews"] if d["reviews"] else None,
        }
        for theme in taxonomy.THEMES:
            count = d["themes"].get(theme, 0)
            row[f"n_{theme}"] = count
            # Composition: of the people who complained today, how many about this.
            row[f"share_{theme}"] = count / d["negatives"] if d["negatives"] else None
            # Intensity: complaints of this kind per 1,000 reviews that day.
            row[f"rate_{theme}"] = 1000 * count / d["reviews"] if d["reviews"] else None
        rows.append(row)

    return {"appid": appid, "sentiment_signal": config.SENTIMENT_SIGNAL, "days": rows}


def save(series: dict) -> None:
    path = daily_path(series["appid"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(series), encoding="utf-8")


def load(appid: int | None = None) -> dict:
    return json.loads(daily_path(appid or config.TARGET_APPID).read_text(encoding="utf-8"))


if __name__ == "__main__":
    series = build()
    save(series)
    rows = series["days"]
    print(f"{len(rows)} days, {rows[0]['date']} to {rows[-1]['date']}")

    # Does dropping 27% of the corpus to English change the sentiment picture?
    both = [r for r in rows if r["positive_share"] is not None and r["positive_share_all"] is not None
            and r["reviews_all"] >= 200]
    if both:
        gaps = [abs(r["positive_share"] - r["positive_share_all"]) for r in both]
        print(f"English-only vs all-language positive share, on days with 200+ reviews:")
        print(f"  mean absolute difference {sum(gaps)/len(gaps):.3%}, max {max(gaps):.3%}")

    worst = sorted((r for r in rows if r["reviews"] >= 500), key=lambda r: r["positive_share"])[:8]
    print("\nlowest positive-share days (500+ English reviews):")
    for r in worst:
        print(f"  {r['date']}  {r['reviews']:>7,} reviews  {r['positive_share']:>6.1%} positive")
