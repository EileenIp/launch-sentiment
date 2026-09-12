# Launch Sentiment: What Went Wrong, and When

> When a launch goes sideways, what exactly turned sentiment — bugs, price, monetisation,
> performance — and how early was it visible before the review score moved?

The claim this project is built to test is a **leading-indicator** one: not "sentiment was
negative," but "complaint theme X spiked N days before the aggregate score dropped." If that
lead doesn't hold in the data, the honest null goes in the write-up instead.

**The launch:** HELLDIVERS 2 (appid 553850, released 2024-02-08). Chosen over
Cyberpunk 2077 because it launched well and soured *later*, which leaves a positive
baseline for the leading-indicator question to be asked against. Reasoning, and the
deliberate deviation from the spec's 6–24 month recency rule, are in `src/config.py`.

**Status:** Phase 0 complete (Steam). Nothing is analysed yet.

| Piece | State |
|---|---|
| Steam review fetcher | Built, tested, live-verified |
| Launch selection | Decided 2026-09-13 |
| Steam corpus | **860,018 reviews, 100.0% of the window** |
| Reddit pull | Not started — needs API credentials |
| Sentiment scoring | Not started |
| Theme taxonomy | Not started |
| Lag analysis | Not started |

## The corpus

Window: 2024-01-25 to 2024-08-09 (14 days pre-launch, 183 post). Steam reports
860,089 reviews in that range; the pull retrieved 860,018 — the 71-review gap is
reviews deleted between the count probe and the fetch. Zero duplicates, zero items
outside the window.

The pre-launch fortnight contains **zero** reviews: Helldivers 2 had no Steam early
access, so the spec's "two weeks before launch" yields nothing for this title.

### Weekly volumes

| Week | Reviews | Positive |
|---|---|---|
| 2024-W06 (launch) | 30,918 | 73.5% |
| 2024-W07 | 61,063 | 76.0% |
| 2024-W08 | 76,597 | 80.9% |
| 2024-W09 | 45,206 | 88.1% |
| 2024-W10 – W17 | 9,529 – 48,924 | 78–86% |
| **2024-W18** | **258,530** | **58.5%** |
| 2024-W19 | 152,153 | 83.8% |
| 2024-W20 – W31 | 1,337 – 9,417 | 71–85% |
| 2024-W32 | 5,179 | 52.8% |

W18 alone is 30% of the entire corpus. Note W19: volume stays enormous while the
positive share snaps back to 83.8% — whatever happened, the reversal is in the data
as clearly as the event. A second, smaller dip appears in W32 on low volume.

These are counts and Steam's own thumbs-up flag, not sentiment analysis. No claim
about *why* anything moved belongs here until Phases 2–4 have run.

## What didn't work

Two failures worth keeping, both caught only by checking totals against an
independent source:

1. **Deep pagination truncates silently.** A single request for the whole window
   returned 65,496 of 858,566 reviews — 7.6% — with no error, missing February
   through April entirely. The same endpoint returned 48,706 of 48,708 for one
   launch week. Fixed by bisecting the window on Steam's own review counts until
   every chunk paginates shallowly.
2. **The integrity check passed the truncated pull.** Duplicates, window bounds,
   empty text and gap distributions were all clean — because every review collected
   *was* genuine. There were simply 92% too few. Coverage against an expected total
   is now the first check, not an afterthought.

A third, subtler one: Steam intermittently serves an empty page mid-sequence, which
reads as a clean end of listing. Because the dud response was cached like any other,
retrying replayed the truncation exactly. Retries now bypass the cache.

## The Steam fetcher

`src/steam_fetch.py` pulls reviews for any appid via Valve's public `appreviews` endpoint.
No API key, no auth.

Compare candidate launches before committing to one:

```bash
python -m src.steam_fetch recon 440
```

```
--- appid 440 ---
name: Team Fortress 2
release date: 10 Oct, 2007
lifetime reviews: 1,250,502
positive: 1,138,419 (91.0%)  negative: 112,083
steam score label: Very Positive
```

Once `TARGET_APPID` and `TARGET_LAUNCH_DATE` are set in `src/config.py`, pull the full
launch window (two weeks pre-launch through six months post):

```bash
python -m src.steam_fetch pull <appid>
```

### Design notes

- **`filter=recent`, not `filter=all`.** `all` sorts by helpfulness and re-orders as votes
  accrue, so an identical re-run would not return an identical corpus. `recent` sorts by
  creation date, which also lets a windowed pull terminate as soon as it pages past the
  window start.
- **Every page is cached to disk** by `(appid, cursor)`. A re-run makes no requests and
  returns byte-identical data — verified live: 483 reviews in 10.5s cold, 0.2s cached.
- **Cursor loops are handled.** Steam sometimes returns the same cursor forever rather than
  an empty page at the end of a listing; the pull stops when a cursor repeats.
- **Reviews are deduplicated** by `recommendationid`, which can repeat across cursor pages.
- Retries with exponential backoff on 429 and 5xx only. A bad appid returns HTTP 200 with an
  HTML body, which is caught and raised rather than parsed as data.

## Setup

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

Reddit credentials (Phase 0, later) go in a gitignored `.env` and are never read into
version-controlled code.

## Working rules

From the spec (`spec-launch-sentiment.md`) and the churn project it inherits from:

- The agent **stops at every `EILEEN DECIDES`** and does not choose.
- **No invented numbers**, anywhere, including as placeholders. A figure not yet computed
  is written `[from run]` until it is.
- `NOTES.md` is Eileen's decision log and is never written by the agent.
- One phase per session; commit per phase.
