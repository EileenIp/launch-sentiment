# Launch Sentiment: What Went Wrong, and When

> When a launch goes sideways, what exactly turned sentiment — bugs, price, monetisation,
> performance — and how early was it visible before the review score moved?

The claim this project is built to test is a **leading-indicator** one: not "sentiment was
negative," but "complaint theme X spiked N days before the aggregate score dropped." If that
lead doesn't hold in the data, the honest null goes in the write-up instead.

**Status:** Phase 0, not yet started. The launch to analyse is undecided — see below.

## Current state

| Piece | State |
|---|---|
| Steam review fetcher | Built, tested, live-verified |
| Launch selection | **Awaiting Eileen (Checkpoint 0)** |
| Reddit pull | Not started — needs API credentials |
| Sentiment scoring | Not started |
| Theme taxonomy | Not started |
| Lag analysis | Not started |

Nothing here analyses anything yet. There are no findings on this page because no data
has been pulled for a chosen launch.

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
