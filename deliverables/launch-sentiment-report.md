# When a launch goes sideways: what turned sentiment, and how early was it visible?

**HELLDIVERS 2 · 886,850 Steam reviews · 2024-02-08 to 2024-11-04**

## The question

When a live game's review score collapses, a community team needs two things: to know
what it is about, and ideally to have seen it coming. This looked at whether complaint
themes inside Steam reviews rise *before* the aggregate score moves — an early-warning
signal.

## The answer

**Nothing led the score.** Both sentiment collapses in this window were triggered by
dated developer actions, so complaints and the score moved on the same day.

On 2024-05-02 the game sat at 86.7%
positive on 968 reviews. The next day Sony announced a
PlayStation Network account-linking requirement. That day carried
36,055 reviews at 62.8%
positive, and the share of complaints mentioning Sony or PSN went from
21% to 57%.
Volume rose 37-fold in
twenty-four hours. Three days later Sony reversed the decision and the score recovered
to 88.3% — on the single busiest day of the entire
window, 78,185 reviews.

The same shape repeated in August around a balance patch: complaints about balance went
from 0% to 46%
on the day of the patch, with the score falling from
89.1% to 71.2%.

You cannot get early warning of an announcement from reactions to it.

## What the data does support

**Same-day diagnosis.** Within hours of each collapse the theme mix correctly named the
cause, and did so in both directions — Sony/PSN in May while balance complaints *fell*,
balance in August while Sony/PSN stayed flat at
3%. For a community lead opening their laptop to
a review-score alert, "what is this about" is answered immediately and without reading
a single review.

## How solid is the null

Three checks, because the first result was misleading. Raw correlation showed apparent
leads in seven of eight themes, up to twelve days.

1. **A rotation test.** Reporting the best of 29 lags means taking the extreme of 29
   attempts, which finds something in noise. Chance alone produces a median
   best-of-29-lags correlation of about −0.15, which is most of what the raw table showed.
2. **Correcting for testing eight themes.** Only the Sony/PSN theme survives, at lag zero.
3. **Sensitivity to thin days.** The apparent leads move from +3 to +12 to −8 days as the
   minimum day size rises, and their significance evaporates. A real lead persists as
   measurement improves. On a 150-review day there are around 15 complaints, so one
   review shifts a theme's share by seven points.

## What was measured

- **886,850 reviews** across 271 days, 100% of what Steam reports for
  the window. 650,201 are English, which is the subset used for theme analysis.
- **Sentiment is Steam's own thumbs-up flag**, not a text model. Two standard sentiment
  scorers were tested against 200 hand-labelled reviews and both scored worse
  than always guessing "positive" — see Limitations.
- **127,507 negative English reviews** classified into nine complaint themes
  by a transparent keyword taxonomy; 69.6% matched at least one theme.
- **48 official patches** from the developer's own announcements, used to
  annotate the timeline.

| Theme | Reviews | Share of negatives |
|---|---|---|
| psn access | 51,032 | 40.0% |
| bugs stability | 23,126 | 18.1% |
| balance | 14,739 | 11.6% |
| price value | 9,847 | 7.7% |
| content design | 9,334 | 7.3% |
| dev conduct | 8,890 | 7.0% |
| monetisation | 7,251 | 5.7% |
| performance | 5,355 | 4.2% |

## Limitations

**The thumbs-up is binary, and that is the limitation I would raise first.** Steam gives
one bit per review, so "great game, terrible servers" is recorded exactly the same as
"perfect". When I hand-labelled 200 reviews, 19 were genuinely mixed — and
Steam had 17 of those as positive. Roughly one in ten of the sample is flattened into a
category it does not belong in. It is why I treat the daily positive share as a
direction, not a measurement: the shape of the collapses is real, but I would not defend
the exact level of any single day.

**Steam reviewers self-select.** This measures people moved enough to write something,
not players. Both events here were the kind that motivate writing — an account
requirement and a balance change — so the corpus is probably closer to "engaged and
annoyed" than to the playerbase.

**Two standard sentiment tools were tested and rejected.** VADER agreed with the hand
labels 61.5% of the time and a RoBERTa sentiment model 64.0%, against a 72.0%
majority-class baseline — both did worse than always guessing "positive". The failure is
specific to this game: players express enthusiasm through violence and self-deprecation
("I got hit by an explosion, shot into the air, then stomped by a robot 10/10"), which
general-purpose models read as negative. This is a limitation of the tools, not a
finding about the game, and it is why the analysis uses the thumbs-up flag instead.

**Theme matching is keyword-based and covers 69.6% of complaints.** The
remainder is not all missing vocabulary — a real share of it is complaint expressed
without complaint words ("Arrowhead struck gold but are determined to find copper"). No
keyword list reaches those, and topic modelling would be the honest next step.

**Theme analysis is English-only**, which drops roughly a quarter of the corpus. The
largest excluded group is Simplified Chinese, and their complaints may well differ —
regional pricing and access in particular, which matters because one of the two events
was about regional access.

**Reddit was never pulled.** That is a scope decision, not a coverage finding. It also
removes the most plausible place a lead could have been found: complaints usually surface
in discussion threads before they surface as reviews.

## What didn't work

**A silent truncation nearly invalidated everything.** The first full pull returned
65,496 of 858,566 reviews — 7.6% — with no error, missing February through April
entirely. Steam's cursor pagination stops serving at around 650 pages on a large date
range and simply ends. The fix was to bisect the window on Steam's own review counts
until every chunk paginates shallowly.

**The integrity check passed that truncated pull.** It verified duplicate IDs, window
bounds, empty text and timestamp gaps, and all of them were clean — because every review
collected *was* genuine. There were just 92% too few. Comparing the collected count
against an independent total is now the first check, not an afterthought. The lesson
generalises: a validation that only inspects the rows present cannot detect the rows
absent.

**The cache preserved the bug.** Because a bad response was written to disk like any
other, re-running replayed the truncation exactly. Retries had to be made to bypass the
cache before they did anything at all.

**The first lag result was wrong in a way that looked right.** Raw cross-correlation
showed apparent leads in seven of eight themes, up to twelve days — a publishable-looking
table. All of it dissolved under a rotation test, a correction for testing eight themes,
and a sensitivity check on how thin a day was allowed to be. The apparent leads moved
from +3 to +12 to −8 days as measurement improved, which is the signature of noise.
Without those checks this report would have claimed a twelve-day early-warning signal
that does not exist.

**The window had to be extended.** The original six-month window closed three days into
the August event — the one sentiment collapse that could plausibly have built gradually.
A null measured on a truncated event would have been an artefact of the window rather
than a result.

## Recommendation: what to monitor, and at what threshold

**Do not monitor the review score's level.** It moves with the baseline. A "below 72%
positive" rule fires on 35 of 271 days here, 29 of which are nothing — a quarter of the
calendar, which a team would learn to ignore within a fortnight.

**Monitor the day-over-day change instead.** A fall of **12 percentage points or more in
daily positive share** fired exactly three times in nine months:

| Date | What it was |
|---|---|
| 2024-05-03 | Sony announces PSN account linking |
| 2024-08-06 | Balance patch 1.001.002 ships |
| 2024-08-07 | The same event, second day |

Two events, three alerts, **no false alarms**. The same rule at 10 points adds four
alerts that were not events; at 20 points it misses the August event entirely.

**When it trips, read the theme mix, not the reviews.** That is what this pipeline is
actually for. On 3 May the mix moved from 21% to 57% Sony/PSN while balance complaints
*fell*; on 6 August balance went 0% to 46% while Sony/PSN stayed flat at 3%. In both
cases the cause was identifiable within hours, before anyone read a single review.

**Do not expect warning.** Both events were triggered by the studio's own announcements,
on dates it chose. The honest framing for a community team is that this is an
instrumentation tool, not a forecast: it tells you what is happening today, faster and
more accurately than reading the forum. If genuine early warning is the goal, it needs
data that moves before the announcement — crash telemetry, refund rates, or
discussion-thread volume — none of which is in review text.
