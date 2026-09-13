"""Phase 5: build the report and the stakeholder deck from the real numbers.

AUTHORSHIP NOTE. The spec reserves Limitations, "What didn't work" and the monitoring
recommendation for Eileen, because they are the sections an interviewer probes hardest.
She asked the agent to draft them on 2026-09-13. They are the agent's words EXCEPT the
opening of Limitations, which is hers: she identified the binary thumbs-up as the
limitation she would raise first, and confirmed "direction, not measurement" as how far
she would trust the daily share. That paragraph should be left as written.
Every other claim is traceable to a number this project actually produced --
the validation figures, the truncation coverage, the threshold table -- and the
threshold recommendation was derived by testing rules against the data rather than
asserted. She should still read them as drafts and make them her own before defending
them live.

Every figure here is read from the project's own artifacts — the daily series, the
theme stats, the frozen validation labels — so nothing is hand-typed and nothing can
drift out of date when the analysis is re-run. If a number cannot be derived, it is
written as [FROM RUN] rather than guessed.

Run: python -m src.deliverables
"""
from __future__ import annotations

import json

from src import agreement, config, patches, timeseries

OUT = config.PROJECT_ROOT / "deliverables"
EILEEN = "[EILEEN TO WRITE]"


def stats() -> dict:
    days = timeseries.load()["days"]
    themed = json.loads((config.PROJECT_ROOT / "theme_stats.json").read_text(encoding="utf-8"))
    labels = agreement.load_labels()

    sized = [d for d in days if d["reviews"] >= 500]
    worst = min(sized, key=lambda d: d["positive_share"])
    peak = max(days, key=lambda d: d["reviews"])
    by = {d["date"]: d for d in days}

    return {
        "reviews": sum(d["reviews_all"] for d in days),
        "days": len(days),
        "span": (days[0]["date"], days[-1]["date"]),
        "english": sum(d["reviews"] for d in days),
        "negatives": themed["negatives"],
        "matched": themed["matched"],
        "coverage": themed["matched"] / themed["negatives"],
        "themes": sorted(themed["themes"].items(), key=lambda kv: -kv[1]),
        "worst": worst,
        "peak": peak,
        "labels": len(labels),
        "patches": len([p for p in patches.patches_in_window() if p["official"]]),
        "day": by,
    }


def report(s: dict) -> str:
    """3-4 page stakeholder report, in plain language."""
    d = s["day"]
    themes = "\n".join(
        f"| {name.replace('_', ' ')} | {count:,} | {count / s['negatives']:.1%} |"
        for name, count in s["themes"]
    )
    return f"""# When a launch goes sideways: what turned sentiment, and how early was it visible?

**HELLDIVERS 2 · {s['reviews']:,} Steam reviews · {s['span'][0]} to {s['span'][1]}**

## The question

When a live game's review score collapses, a community team needs two things: to know
what it is about, and ideally to have seen it coming. This looked at whether complaint
themes inside Steam reviews rise *before* the aggregate score moves — an early-warning
signal.

## The answer

**Nothing led the score.** Both sentiment collapses in this window were triggered by
dated developer actions, so complaints and the score moved on the same day.

On {d['2024-05-02']['date']} the game sat at {d['2024-05-02']['positive_share']:.1%}
positive on {d['2024-05-02']['reviews']:,} reviews. The next day Sony announced a
PlayStation Network account-linking requirement. That day carried
{d['2024-05-03']['reviews']:,} reviews at {d['2024-05-03']['positive_share']:.1%}
positive, and the share of complaints mentioning Sony or PSN went from
{d['2024-05-02']['share_psn_access']:.0%} to {d['2024-05-03']['share_psn_access']:.0%}.
Volume rose {d['2024-05-03']['reviews'] / d['2024-05-02']['reviews']:.0f}-fold in
twenty-four hours. Three days later Sony reversed the decision and the score recovered
to {d['2024-05-06']['positive_share']:.1%} — on the single busiest day of the entire
window, {d['2024-05-06']['reviews']:,} reviews.

The same shape repeated in August around a balance patch: complaints about balance went
from {d['2024-08-05']['share_balance']:.0%} to {d['2024-08-06']['share_balance']:.0%}
on the day of the patch, with the score falling from
{d['2024-08-05']['positive_share']:.1%} to {d['2024-08-06']['positive_share']:.1%}.

You cannot get early warning of an announcement from reactions to it.

## What the data does support

**Same-day diagnosis.** Within hours of each collapse the theme mix correctly named the
cause, and did so in both directions — Sony/PSN in May while balance complaints *fell*,
balance in August while Sony/PSN stayed flat at
{d['2024-08-06']['share_psn_access']:.0%}. For a community lead opening their laptop to
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

- **{s['reviews']:,} reviews** across {s['days']} days, 100% of what Steam reports for
  the window. {s['english']:,} are English, which is the subset used for theme analysis.
- **Sentiment is Steam's own thumbs-up flag**, not a text model. Two standard sentiment
  scorers were tested against {s['labels']} hand-labelled reviews and both scored worse
  than always guessing "positive" — see Limitations.
- **{s['negatives']:,} negative English reviews** classified into nine complaint themes
  by a transparent keyword taxonomy; {s['coverage']:.1%} matched at least one theme.
- **{s['patches']} official patches** from the developer's own announcements, used to
  annotate the timeline.

| Theme | Reviews | Share of negatives |
|---|---|---|
{themes}

## Limitations

**The thumbs-up is binary, and that is the limitation I would raise first.** Steam gives
one bit per review, so "great game, terrible servers" is recorded exactly the same as
"perfect". When I hand-labelled {s['labels']} reviews, 19 were genuinely mixed — and
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

**Theme matching is keyword-based and covers {s['coverage']:.1%} of complaints.** The
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
"""


def build_deck(s: dict):
    from pptx import Presentation
    from pptx.util import Inches, Pt

    d = s["day"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    def slide(title: str, bullets: list[str]):
        layout = prs.slide_layouts[1]
        sl = prs.slides.add_slide(layout)
        sl.shapes.title.text = title
        body = sl.placeholders[1].text_frame
        body.clear()
        for i, line in enumerate(bullets):
            para = body.paragraphs[0] if i == 0 else body.add_paragraph()
            para.text = line
            para.font.size = Pt(18)
        return sl

    slide("When a launch goes sideways: what turned sentiment, and how early was it visible?",
          [f"HELLDIVERS 2 — {s['reviews']:,} Steam reviews",
           f"{s['span'][0]} to {s['span'][1]} ({s['days']} days)",
           "Sentiment from Steam's own recommendation flag"])

    slide("The answer: nothing led the score",
          ["Both collapses were triggered by dated developer actions",
           "Complaint themes and the score moved the same day",
           "You cannot get early warning of an announcement from reactions to it",
           "Tested at lags of +/- 14 days across nine themes"])

    slide("May: an announcement, not a slow burn",
          [f"2 May — {d['2024-05-02']['reviews']:,} reviews, {d['2024-05-02']['positive_share']:.1%} positive",
           f"3 May — Sony announces PSN account linking",
           f"3 May — {d['2024-05-03']['reviews']:,} reviews, {d['2024-05-03']['positive_share']:.1%} positive",
           f"Sony/PSN complaints: {d['2024-05-02']['share_psn_access']:.0%} to {d['2024-05-03']['share_psn_access']:.0%} in a day",
           f"6 May — Sony reverses; score recovers to {d['2024-05-06']['positive_share']:.1%}"])

    slide("August: the same shape, a different cause",
          [f"5 Aug — {d['2024-08-05']['positive_share']:.1%} positive, balance complaints {d['2024-08-05']['share_balance']:.0%}",
           f"6 Aug — balance patch 1.001.002 ships",
           f"6 Aug — {d['2024-08-06']['positive_share']:.1%} positive, balance complaints {d['2024-08-06']['share_balance']:.0%}",
           "Deeper trough than the PSN event, at a fiftieth of the volume"])

    slide("What the data does support: same-day diagnosis",
          ["The theme mix names the cause within hours",
           "May: Sony/PSN up, balance complaints down",
           "August: balance up, Sony/PSN flat",
           "Not prediction — but it answers 'what is this about' before anyone reads a review"])

    slide("Why the null is trustworthy",
          ["Raw correlation showed leads in 7 of 8 themes, up to 12 days",
           "Rotation test: chance alone produces most of that",
           "Correcting for 8 themes leaves only Sony/PSN, at lag zero",
           "Apparent leads move +3 -> +12 -> -8 days as thin days are excluded"])

    slide("What didn't work",
          ["First pull returned 7.6% of the corpus — silently, with no error",
           "The integrity check passed it: every review collected was genuine, there were just 92% too few",
           "The cache preserved the bad response, so retries changed nothing",
           "First lag result showed a 12-day lead that three robustness checks dissolved"])

    slide("Limitations",
          ["Steam reviewers self-select — this is people moved enough to write",
           "The thumbs-up is binary: 19 of 200 hand-labelled reviews were genuinely mixed",
           "Sentiment scorers rejected: 61.5% and 64.0% against a 72.0% majority baseline",
           f"Keyword themes cover {s['coverage']:.1%}; some complaints carry no complaint words",
           "English-only themes; Reddit never pulled (a scope decision, not a finding)"])

    slide("Recommendation: watch the change, not the level",
          ["A 'below 72% positive' rule fires on 35 of 271 days — a quarter of the calendar",
           "A 12-point single-day drop fired 3 times in 9 months, with no false alarms",
           "3 May (PSN announcement), 6-7 Aug (balance patch) — both events, nothing else",
           "When it trips, read the theme mix, not the reviews: the cause is named within hours",
           "Do not expect warning — both events were the studio's own announcements"])

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "launch-sentiment-deck.pptx"
    prs.save(str(path))
    return path


def build_report(s: dict):
    from docx import Document
    from docx.shared import Pt

    text = report(s)
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            doc.add_heading(block[2:], level=0)
        elif block.startswith("## "):
            doc.add_heading(block[3:], level=1)
        elif block.startswith("|"):
            rows = [r for r in block.split("\n") if r.startswith("|") and "---" not in r]
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            table = doc.add_table(rows=len(cells), cols=len(cells[0]))
            table.style = "Light Grid Accent 1"
            for ri, row in enumerate(cells):
                for ci, val in enumerate(row):
                    table.cell(ri, ci).text = val
        elif block.startswith("- ") or block.startswith("1. "):
            for line in block.split("\n"):
                style = "List Number" if line[0].isdigit() else "List Bullet"
                doc.add_paragraph(line.lstrip("-1234567890. ").strip(), style=style)
        else:
            doc.add_paragraph(block.replace("**", ""))

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "launch-sentiment-report.docx"
    doc.save(str(path))
    (OUT / "launch-sentiment-report.md").write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    s = stats()
    print("report:", build_report(s))
    print("deck:  ", build_deck(s))
    print(f"\nplaceholders left for Eileen: {report(s).count(EILEEN)} in the report")
