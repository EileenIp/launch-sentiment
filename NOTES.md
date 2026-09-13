# NOTES — Launch Sentiment (HELLDIVERS 2)

**Read this before writing in it.** The project spec reserves this file for Eileen
and forbids the agent from writing it, because it is the evidence that the
judgement calls were hers. On 2026-09-13 she instructed the agent to write it
anyway, so:

- **The record below is the agent's** — dates, what was chosen, what was
  rejected, and the evidence each call rested on. All of it is verifiable
  against `src/config.py`, the commit history and the artifacts.
- **Passages marked "Eileen:" are her words, verbatim**, from the session.
- **Slots marked `[IN YOUR WORDS]` are deliberately empty.** That is where the
  reasoning goes, and inventing it would defeat the point of the file. Nothing
  else in the repo is waiting on them.

Every decision here is reversible: the config constant is named in each entry.

---

## Checkpoint 0 — the launch — 2026-09-13

**Chosen: HELLDIVERS 2** (appid 553850, released 2024-02-08).
**Rejected: Cyberpunk 2077** (appid 1091500).

Recon numbers that drove it, pulled live:

| | reviews | positive |
|---|---|---|
| Cyberpunk 2077 | 979,443 | 86.9% |
| HELLDIVERS 2 | 1,161,809 | 75.5% |

Helldivers launched well and soured later, which leaves a genuine positive
baseline for the leading-indicator question to be asked against. Cyberpunk
collapsed on day one, leaving nothing for complaint themes to lead — and it is
the most-analysed launch in games data.

**Accepted deviation:** the spec asks for a launch 6–24 months old; this one was
31 months. Eileen's call, trading recency for a better-shaped sentiment arc.
"Why this launch" is an obvious interview question.

`TARGET_APPID`, `TARGET_LAUNCH_DATE`

**[IN YOUR WORDS]** — why the shape of the arc mattered more to you than recency.

---

## Scope — Steam only — 2026-09-13

Reddit was never pulled. `SOURCES = ("steam",)`

The distinction the write-up must not blur: the spec permits a Steam-only
project when *Reddit coverage is too thin*. That is not what happened. Reddit
was never attempted. This is a scope decision, not a data-availability finding.

**What it costs:** complaints usually surface in discussion threads before they
move a review score, so Reddit was the likeliest place for a lead to be visible.
Steam-only narrows the claim to "did complaint themes inside reviews move before
the aggregate score did." Reversible — the corpus, scorers and lag analysis are
all source-agnostic.

**[IN YOUR WORDS]** — whether you would add Reddit if you returned to this.

---

## Corpus hygiene — 2026-09-13

**Non-Steam purchases stay in.** `KEEP_NON_STEAM_PURCHASES = True`

218,449 of 834,605 reviews — 26.2%, too large to drop silently. The May 2024
event was about an account-linking requirement, so players who did not buy
through Steam are plausibly part of the story rather than noise around it.
Excluding them would have quietly excluded a group with a specific reason to be
angry. The write-up states the 26.2% openly.

**English-only scoring.** `SCORING_LANGUAGES = ("english",)`

631,806 of 860,018 — 73.5%. VADER is an English lexicon by construction, so
scoring non-English text with it produces numbers that look real and mean
nothing. The largest excluded group is 77,432 Simplified Chinese reviews (9.0%),
who may complain about different things — regional pricing among them.

**Copypasta down-weighting: not applied.** `DOWNWEIGHT_COPYPASTA = False`

Eileen's first call was to weight it down. After detection ran she delegated the
revised call to the agent ("your choice"), **so this one is the agent's
judgement, not hers** — flagged because the spec marks it as an interview
question whose answer is supposed to be hers.

The evidence contradicted the premise. W18, the spike week, is the *least*
duplicated week in the window (20.7% repeated text against a 28–30% baseline).
The largest repeated texts are positive community memes — "for democracy",
11,851 corpus-wide, 96% positive in W18 — not coordinated negativity. Collapsing
every repeated text to a single vote moves every week down 1.8–4.9pp and moves
W18 down *least* (−2.1pp); the W18-vs-baseline gap goes from 26.7pp to 26.0pp.
Down-weighting would have stripped more positive weight than negative from the
very week it was meant to correct, and changes no conclusion.

**[IN YOUR WORDS]** — this one is worth reclaiming. Say whether you agree with
the reversal, in your own terms, so it stops being the agent's call.

---

## Checkpoint 2 — the sentiment signal — 2026-09-13

**This reversed the spec's plan.** `SENTIMENT_SIGNAL = "steam_voted_up"`

Measured against Eileen's 200 hand labels:

| signal | agreement |
|---|---|
| VADER | 61.5% |
| RoBERTa (twitter-roberta-base-sentiment-latest) | 64.0% |
| **always predict "positive"** | **72.0%** |
| Steam's own thumbs-up | 95.0% |

Both text scorers lose to guessing "positive". A scorer that loses to the
majority class has no business driving the headline chart.

Why they fail here is specific: Helldivers players express enthusiasm through
violence and self-deprecation — *"I got hit by a explosion shot into the air
then got stomped on by a robot 10/10"* — and general-purpose models read the
words and miss the delight. Both models stay in the repo as the evidence for the
decision.

> **Eileen:** The thumbs-up is binary, and that is the limitation I would raise
> first. It is why I treat the daily positive share as a direction, not a
> measurement.

**[IN YOUR WORDS]** — what labelling 200 reviews by hand actually felt like, and
where you hesitated. That is the strongest interview story in the project and it
exists nowhere in the repo.

---

## Window extension — 2026-09-13

**183 days → 271.** `POST_LAUNCH_DAYS = 271`

Eileen's call, made *after* the first lag analysis had already returned a null.
The six-month window closed on 2024-08-09. The August nerf controversy — the one
event in this corpus that could plausibly have built gradually, and so the only
fair test of the leading-indicator claim — began 2024-08-06 and was still
deepening on the last day in the window. Judging the project's central claim on
three days of a truncated event would have produced a null by accident of the
window rather than a null in the data.

271 days runs to 2024-11-05, covering the nerf patch, the September rebalance and
October's return to baseline. Cost: 26,832 additional reviews.

**Note the order this happened in — it matters.** The null came first, and the
window was widened to give the result its best chance of being overturned. It
survived.

---

## The result — a null — 2026-09-13

No complaint theme leads the review score. Raw correlation suggested leads in
seven of eight themes, up to 12 days; a rotation-based permutation test, a
Bonferroni correction for testing eight themes, and a threshold-sensitivity
sweep each removed them independently. Only `psn_access` survives, at lag 0.

Both collapses were triggered by dated developer actions — the PSN
account-linking announcement and a balance patch — so themes and score moved the
same day. There was no gradual build to detect.

> **Eileen:** This is a good outcome — better than forcing a fake finding.

**What the data does support:** same-day diagnosis. `psn_access` 21%→57% on
3 May while `balance` fell; `balance` 0%→46% on 6 August while `psn` stayed at
3%. Derived alert rule — a 12-point single-day drop in positive share fired 3
times in 9 months with zero false alarms, against 35 fires and 29 false alarms
for the obvious "below 72%" level rule.

> **Eileen**, on the objection that a 12-point threshold is arbitrary:
> A 12-point drop is still a 12-point drop.

---

## Known failures worth telling

Three bugs this build were **silent omissions** — nothing errored, and each was
caught only by counting what should have been there:

1. **Truncated pull.** A wide date range returned 65,496 of 858,566 reviews
   (7.6%) with no error — Steam stops paginating at roughly 650 pages. Fixed
   with count-bisected chunking and a coverage check against Steam's own total.
2. **The integrity check passed the truncated pull**, because it only inspected
   rows that were present. Collected-vs-expected is now the first check.
3. **The disk cache preserved the bad response**, so retries were no-ops until
   `refresh=True` was added.

**[IN YOUR WORDS]** — the general lesson you would take from all three being
silent rather than loud.

---

## Still open

- Half of Limitations, all of "What didn't work", and the mechanics of the
  threshold recommendation are the agent's words. `src/deliverables.py` names
  exactly which passages are yours. Read the rest before defending them live.
- The repo is not pinned on the GitHub profile. Three attempts on 2026-09-13,
  one from a private window, none saved. There is no API for pinning, so it
  cannot be scripted.
