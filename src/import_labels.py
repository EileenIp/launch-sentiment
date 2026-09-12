"""Merge hand labels into the frozen validation CSV.

Exists because the browser download route does not always reach this repo — the
labelling can happen on another device, or the download can be blocked. This takes
the labels as JSON ({"recommendationid": "label", ...}) from a file or stdin and
writes them into the CSV in place, leaving the review text untouched.

Refuses unknown ids and unknown labels rather than silently dropping them, since a
quietly half-imported validation set would corrupt every agreement number downstream.

Run: python -m src.import_labels labels.json
     python -m src.import_labels -   (read from stdin)
"""
from __future__ import annotations

import csv
import json
import sys

from src import agreement, sample_validation


def merge(raw: str, path=sample_validation.SAMPLE_PATH) -> dict:
    labels = json.loads(raw)
    if not isinstance(labels, dict):
        raise SystemExit("expected a JSON object of {recommendationid: label}")

    with open(path, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    known_ids = {row["recommendationid"] for row in rows}
    unknown_ids = [rid for rid in labels if rid not in known_ids]
    bad_labels = {
        rid: value for rid, value in labels.items()
        if str(value).strip().lower() not in agreement.VALID_LABELS
    }
    if unknown_ids:
        raise SystemExit(f"{len(unknown_ids)} id(s) not in the sample, e.g. {unknown_ids[:3]}")
    if bad_labels:
        raise SystemExit(f"invalid label(s): {list(bad_labels.items())[:3]}")

    applied = 0
    for row in rows:
        value = labels.get(row["recommendationid"])
        if value:
            row["label"] = str(value).strip().lower()
            applied += 1

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["recommendationid", "review", "label"])
        writer.writeheader()
        writer.writerows(rows)

    return {"applied": applied, "total": len(rows)}


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    raw = sys.stdin.read() if argv[1] == "-" else open(argv[1], encoding="utf-8").read()
    result = merge(raw)
    print(f"applied {result['applied']} labels to {result['total']} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
