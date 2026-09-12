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

## The copypasta question, answered both ways

A review-bomb is supposed to be inflated by mass-pasted identical reviews. In this
corpus it isn't.

**W18, the spike week, is the least duplicated week in the window** — 20.7% repeated
text against a 28–30% baseline. The most-repeated texts are positive community memes,
not coordinated anger:

| Text (W18) | Count | Positive |
|---|---|---|
| `for democracy` | 1,321 | 96% |
| `we won` | 692 | 100% |
| `democracy has prevailed` | 485 | 100% |
| `sony` | 1,212 | 26% |
| `psn` | 837 | 11% |

`sony` and `psn` are the only clearly campaign-related repeats — 0.8% of the week.
Meanwhile `we won` and `democracy has prevailed` are absent from every baseline week:
the reversal is being celebrated inside the same week as the bomb.

So rather than argue about weighting, here is the effect measured. "Collapsed" counts
each distinct text once per week — the strongest possible down-weighting, which
brackets the effect instead of estimating it:

| Week | Reviews | Every review | Collapsed | Delta |
|---|---|---|---|---|
| W15 | 17,494 | 85.5% | 82.6% | −3.0pp |
| W16 | 13,046 | 84.7% | 81.7% | −2.9pp |
| W17 | 9,529 | 85.3% | 82.8% | −2.5pp |
| **W18** | **258,530** | **58.5%** | **56.4%** | **−2.1pp** |
| W19 | 152,153 | 83.8% | 81.7% | −2.1pp |

Every week moves down, because repeated text is disproportionately positive. W18 moves
*least*. The W18-versus-baseline gap goes from 26.7pp to 26.0pp — a **0.7pp** change to
the thing the project actually claims.

The copypasta decision does not change any conclusion here, and that is a more useful
answer than picking a side would have been.

Two limits on that claim: detection is exact match after normalisation, so templated
variation ("Sony ruined this" / "sony killed it") is invisible to it — identical-text
copypasta wasn't the mechanism, which is not the same as saying nothing was coordinated.
And 27.5% of all reviews are three words or fewer, so much of the ~28% baseline is short
generic text ("good", "fun") colliding by chance rather than anyone pasting anything.

## The scorer validation, and why it changed the project

200 reviews were hand-labelled blind — no scorer output, no Steam thumbs-up visible —
then compared against both scorers.

| | Agreement with the hand labels |
|---|---|
| VADER | 61.5% |
| Transformer | 64.0% |
| **"Always say positive"** | **72.0%** |
| **Steam's own thumbs-up** | **95.0%** (on the 181 labelled clearly positive or negative) |

**Both scorers lose to a classifier that does not read the text.** The label mix is
144 positive / 37 negative / 19 mixed-neutral, so always guessing "positive" scores
72%. Quoting "the transformer wins, 64.0% vs 61.5%" without that baseline would be
a misleading result, not a finding.

They also fail differently. The transformer is far better on negatives (70.3% vs
45.9%); VADER edges positives (71.5% vs 69.4%). Both collapse on mixed-neutral
(15.8% and 10.5%) — the class a nuanced daily index would most need.

**Why they fail is specific to this game.** Where both scorers said negative and the
hand label said positive:

> "I got hit by a explosion shot into the air then got stomped on by a robot 10/10
> would get hit by my teammate drop pod again"
> "This game has ruined my chances of getting a girlfriend. 10/10"
> "Tyranny is a cancer and modern democracy is the cure"

Helldivers players express enthusiasm through violence, self-deprecation and
in-fiction propaganda. General-purpose sentiment models read the words and miss the
delight. That is not a tuning problem; it is a register mismatch.

**So the sentiment index is built on Steam's thumbs-up flag instead** — human
judgement, attached to 100% of the corpus, and closer to the hand labels than either
model managed. The text scorers stay in the repo as the evidence for this decision,
not as part of the pipeline.

This is the opposite of what the spec planned, and it is a better outcome than
following the plan would have been: a measured reason to reject two standard tools
beats an unexamined reason to adopt one.

## Complaint themes

Nine themes, 182 seed phrases, applied to the 123,316 negative English reviews.
Multi-label: "nerfed into the ground and it crashes" is genuinely two complaints.

| Theme | Reviews | Share of negatives |
|---|---|---|
| `psn_access` | 50,719 | 41.1% |
| `bugs_stability` | 22,309 | 18.1% |
| `balance` | 13,277 | 10.8% |
| `price_value` | 9,595 | 7.8% |
| `content_design` | 8,691 | 7.0% |
| `dev_conduct` | 8,563 | 6.9% |
| `monetisation` | 6,866 | 5.6% |
| `performance` | 5,079 | 4.1% |
| **matched ≥1 theme** | **86,129** | **69.8%** |

How the taxonomy got there, since the intermediate numbers are the interesting part:

| Configuration | Coverage |
|---|---|
| The spec's six themes, plus balance and dev_conduct | 36.0% |
| + `psn_access` | 66.1% |
| + bugs and content gap fills (**current**) | **69.8%** |
| + developer-mention fills (**rejected**) | 74.3% |

One theme — account access — took coverage from a third to two-thirds. It was added
only because mining showed a large cluster with nowhere to go, and it is now the
largest theme in the corpus by a wide margin.

**The rejected 4.5pp.** Adding `devs`, `arrowhead` and `developer` to `dev_conduct`
would have bought 74.3% coverage. Seed attribution showed `devs` (11.8% of sampled
negatives) and `arrowhead` (8.0%) doing nearly all of that work — matching any
*mention* of the developer, including balance complaints like "devs keep nerfing
everything". Since Phase 4's entire leading-indicator claim rests on theme share
over time, a theme that silently absorbs other themes' complaints would corrupt the
one chart the project turns on. The coverage was not worth it.

**Stated limits.** `psn_access` is carried by bare `sony` (12.1%) and `psn` (7.6%);
the precise phrases — `account linking` (0.6%), `delisted` (0.3%) — contribute
almost nothing. In negative reviews that is still a strong signal, but the theme
measures *mentions of Sony or PSN*, not account-linking complaints specifically.
`grind`/`grindy` sit in `content_design` though grinding here is usually for Super
Credits, which arguably makes them monetisation.

**The 30.2% that matches nothing is not all fixable.** Some is missing vocabulary.
Much of it is complaint without complaint words:

> "Arrowhead struck gold but are determined to find copper."
> "Just when you thought the hole couldn't get any deeper, they got a drill."

No keyword list reaches those. That is the ceiling of a transparent keyword
taxonomy, and the reason the spec suggests topic modelling as a cross-check rather
than a replacement.

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
