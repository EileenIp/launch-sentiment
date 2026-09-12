"""Checkpoint 2: how well each scorer matches Eileen's hand labels.

Reports overall agreement, a per-class breakdown, and two views of the hard cases,
because "which scorer is better" is the wrong question if the two only differ on
reviews that are easy anyway.

Hard cases are defined two ways, neither of which needs a human to nominate them:

  contrastive - the review contains a hedge ("but", "however", "though"). This is
                the "great game but the servers are broken" shape the spec names.
  contested   - the two scorers disagree with each other. Label-free by
                construction, so it cannot be tuned to flatter either one.

Run: python -m src.agreement
"""
from __future__ import annotations

import csv
import json
import re

from src import config, scoring, sample_validation

VALID_LABELS = {scoring.POSITIVE, scoring.NEGATIVE, scoring.MIXED}
CONTRASTIVE = re.compile(r"(?<![a-z])(but|however|though|although|except|aside from)(?![a-z])", re.I)


def load_labels(path=sample_validation.SAMPLE_PATH) -> dict:
    """Eileen's frozen labels. Unlabelled rows are skipped, not guessed."""
    labels = {}
    with open(path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label = (row.get("label") or "").strip().lower()
            if label in VALID_LABELS:
                labels[row["recommendationid"]] = label
    return labels


def load_texts(path=sample_validation.SAMPLE_PATH) -> dict:
    with open(path, encoding="utf-8") as handle:
        return {row["recommendationid"]: row["review"] for row in csv.DictReader(handle)}


def load_scores(appid: int, scorer_name: str, wanted: set) -> dict:
    path = scoring.scores_path(appid, scorer_name)
    found = {}
    if not path.exists():
        return found
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("recommendationid") in wanted:
                found[row["recommendationid"]] = row["label"]
    return found


def agreement(labels: dict, predictions: dict) -> dict:
    shared = [rid for rid in labels if rid in predictions]
    if not shared:
        return {"n": 0, "agree": 0, "rate": 0.0, "per_class": {}, "confusion": {}}

    agree = sum(1 for rid in shared if labels[rid] == predictions[rid])
    per_class, confusion = {}, {}
    for label in sorted(VALID_LABELS):
        of_class = [rid for rid in shared if labels[rid] == label]
        hits = sum(1 for rid in of_class if predictions[rid] == label)
        per_class[label] = {"n": len(of_class), "agree": hits,
                            "rate": hits / len(of_class) if of_class else 0.0}
        for rid in of_class:
            if predictions[rid] != label:
                confusion[f"{label} -> {predictions[rid]}"] = confusion.get(
                    f"{label} -> {predictions[rid]}", 0) + 1

    return {"n": len(shared), "agree": agree, "rate": agree / len(shared),
            "per_class": per_class, "confusion": confusion}


def report(appid: int | None = None) -> None:
    appid = appid or config.TARGET_APPID
    labels = load_labels()
    texts = load_texts()

    if not labels:
        print("No labels found yet — fill the 'label' column in")
        print(f"  {sample_validation.SAMPLE_PATH}")
        return

    total_rows = len(texts)
    print(f"labelled: {len(labels)} of {total_rows}")
    if len(labels) < total_rows:
        print(f"  ({total_rows - len(labels)} still blank — numbers below cover the labelled ones)")

    distribution = {label: sum(1 for v in labels.values() if v == label) for label in sorted(VALID_LABELS)}
    print("your label mix: " + ", ".join(f"{k} {v}" for k, v in distribution.items()))

    wanted = set(labels)
    predictions = {name: load_scores(appid, name, wanted) for name in scoring.SCORERS}

    print("\n=== agreement with your labels ===")
    results = {}
    for name, preds in predictions.items():
        result = agreement(labels, preds)
        results[name] = result
        if not result["n"]:
            print(f"  {name:<12} no scores found")
            continue
        print(f"  {name:<12} {result['agree']}/{result['n']}  {result['rate']:.1%}")
        for label, stats in result["per_class"].items():
            print(f"      {label:<14} {stats['agree']:>3}/{stats['n']:<3} {stats['rate']:>6.1%}")
        if result["confusion"]:
            worst = sorted(result["confusion"].items(), key=lambda kv: -kv[1])[:3]
            print("      most common errors: " + ", ".join(f"{k} ({v})" for k, v in worst))

    contrastive = {rid for rid in labels if CONTRASTIVE.search(texts.get(rid, ""))}
    contested = {
        rid for rid in labels
        if all(rid in p for p in predictions.values())
        and len({p[rid] for p in predictions.values()}) > 1
    }

    for name, subset in (("contrastive (hedged)", contrastive), ("contested (scorers disagree)", contested)):
        if not subset:
            continue
        print(f"\n=== hard cases: {name} — {len(subset)} reviews ===")
        for scorer_name, preds in predictions.items():
            sub = agreement({r: labels[r] for r in subset}, preds)
            if sub["n"]:
                print(f"  {scorer_name:<12} {sub['agree']}/{sub['n']}  {sub['rate']:.1%}")

    if all(r["n"] for r in results.values()):
        best = max(results, key=lambda n: results[n]["rate"])
        gap = abs(results["vader"]["rate"] - results["transformer"]["rate"])
        print(f"\nEILEEN DECIDES which scorer is the headline. On these labels "
              f"{best} leads by {gap:.1%}.")


if __name__ == "__main__":
    report()
