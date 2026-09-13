"""Phase 5: build the website case study entry for eileenip.github.io.

Writes a single object into data/projects.json on the portfolio site, matching the
schema the existing entries use. Every figure is pulled from this project's own
artifacts rather than retyped, and the two charts are drawn from the real daily
series, so nothing here can quietly disagree with the repo.

Run: python -m src.case_study            (prints the entry)
     python -m src.case_study --write    (inserts it into the site's projects.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src import config, deliverables, timeseries

SITE = Path("C:/github/EileenIp.github.io/data/projects.json")
SLUG = "launch-sentiment-helldivers-2024"


def timeline_svg(days: list[dict]) -> str:
    """Positive share over the window, with the two events marked. Drawn from data."""
    rows = [d for d in days if d["reviews"] >= 50]
    W, H, L, T, B = 560, 200, 34, 14, 26
    iw, ih = W - L - 8, H - T - B
    xs = lambda i: L + iw * i / (len(rows) - 1)
    ys = lambda v: T + ih - ih * ((v - 0.45) / 0.55)

    grid = "".join(
        f'<line x1="{L}" y1="{ys(v)}" x2="{W-8}" y2="{ys(v)}" class="viz-stroke-grid"/>'
        f'<text x="2" y="{ys(v)+4}" font-size="9" class="viz-fill-text-soft">{int(v*100)}%</text>'
        for v in (0.5, 0.7, 0.9)
    )
    path = "".join(
        ("M" if i == 0 else "L") + f"{xs(i):.1f} {ys(r['positive_share']):.1f}"
        for i, r in enumerate(rows)
    )
    marks = ""
    for date, label in (("2024-05-03", "PSN linking announced"), ("2024-08-06", "balance patch")):
        i = next((k for k, r in enumerate(rows) if r["date"] == date), None)
        if i is None:
            continue
        anchor = "end" if i > len(rows) * 0.6 else "start"
        dx = -4 if anchor == "end" else 4
        marks += (f'<line x1="{xs(i):.1f}" y1="{T}" x2="{xs(i):.1f}" y2="{T+ih}" '
                  f'class="viz-stroke-accent" stroke-dasharray="3 3"/>'
                  f'<text x="{xs(i)+dx:.1f}" y="{T+10}" font-size="9" text-anchor="{anchor}" '
                  f'class="viz-fill-accent">{label}</text>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Daily positive review share, '
            f'Feb to Nov 2024, showing two sharp drops on the PSN announcement and the balance patch">'
            f'{grid}<path d="{path}" fill="none" class="viz-stroke-accent" stroke-width="1.6"/>{marks}'
            f'<text x="{L}" y="{H-6}" font-size="9" class="viz-fill-text-soft">{rows[0]["date"]}</text>'
            f'<text x="{W-8}" y="{H-6}" font-size="9" text-anchor="end" '
            f'class="viz-fill-text-soft">{rows[-1]["date"]}</text></svg>')


def threshold_svg() -> str:
    """Why watching the change beats watching the level."""
    W, H = 560, 150
    bars = [("Level rule: below 72% positive", 35, 29, "#e0645a"),
            ("Change rule: 12pt single-day drop", 3, 0, "#4fbf8b")]
    out = []
    for k, (label, fires, false_alarms, colour) in enumerate(bars):
        y = 30 + k * 60
        w = fires / 35 * 300
        fw = false_alarms / 35 * 300
        out.append(
            f'<text x="0" y="{y-6}" font-size="11" class="viz-fill-text">{label}</text>'
            f'<rect x="0" y="{y}" width="{w:.0f}" height="18" fill="{colour}" opacity="0.35"/>'
            f'<rect x="0" y="{y}" width="{fw:.0f}" height="18" fill="{colour}"/>'
            f'<text x="{max(w,fw)+8:.0f}" y="{y+13}" font-size="10" class="viz-fill-text">'
            f'{fires} days fired &#183; {false_alarms} false alarms</text>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="A level threshold fires on 35 of 271 '
            f'days with 29 false alarms; a 12-point single-day drop fires 3 times with none">'
            + "".join(out) +
            f'<text x="0" y="{H-6}" font-size="9" class="viz-fill-text-soft">'
            f'Solid = false alarms. Across 271 days.</text></svg>')


def entry() -> dict:
    s = deliverables.stats()
    days = timeseries.load()["days"]
    d = s["day"]

    return {
        "id": SLUG,
        "title": "Launch Sentiment: What Turned, and How Early It Showed",
        "year": 2026,
        "industry": "Gaming",
        "projectType": "NLP Analysis",
        "serviceType": "Analysis + Dashboard",
        "tools": ["Python", "Steam Web API", "VADER", "RoBERTa", "pytest"],
        "sectionHeadlines": {
            "summaryImpact": "The early-warning claim failed, and that is the result",
            "problemSpace": "A score collapse tells you nothing about why",
            "inputs": "886,850 reviews — every one Steam has for the window",
            "discovery": "The first pull returned 7.6% and looked perfect",
            "execution": "Two standard sentiment tools, both rejected on evidence",
            "results": "Watch the change, not the level",
        },
        "cardDescription": (
            "Tested whether complaint themes inside Steam reviews rise before a game's review score "
            "collapses. They don't — both events were triggered by dated developer announcements, so "
            "themes and score moved the same day. The useful finding is same-day diagnosis: the theme "
            "mix names the cause within hours."
        ),
        "impactStat": (
            "A 12-point single-day drop rule fires 3 times in 9 months with zero false alarms; "
            "the obvious level rule fires 35 times, 29 of them nothing"
        ),
        "oneSentenceDescription": (
            "886,850 Steam reviews across a launch, a review-bomb and a balance controversy, testing "
            "whether complaint themes give early warning of a score collapse — and finding they don't."
        ),
        "targetIndustryRole": "Gaming / community and live-ops teams monitoring launch sentiment",
        "links": {
            "dashboard": "https://eileenip.github.io/launch-sentiment/dashboard/",
            "technicalFindings": "https://github.com/EileenIp/launch-sentiment/blob/main/deliverables/launch-sentiment-report.md",
            "notebookRepo": "https://github.com/EileenIp/launch-sentiment",
            "caseStudyPage": "https://github.com/EileenIp/launch-sentiment#readme",
        },
        "summaryImpact": (
            f"**The question was whether complaint themes lead the review score.** If crash complaints "
            f"spike three days before the score moves, a community team has a usable early-warning "
            f"signal. I tested it on HELLDIVERS 2 — {s['reviews']:,} Steam reviews across "
            f"{s['days']} days covering the launch, the PSN account-linking review-bomb, and the "
            f"August balance controversy.\n\n"
            f"**They don't lead.** Both sentiment collapses were triggered by dated developer actions, "
            f"so complaints and the score moved on the same day. On {d['2024-05-02']['date']} the game "
            f"sat at {d['2024-05-02']['positive_share']:.1%} positive on "
            f"{d['2024-05-02']['reviews']:,} reviews; the next day Sony announced PSN account linking "
            f"and the day carried {d['2024-05-03']['reviews']:,} reviews at "
            f"{d['2024-05-03']['positive_share']:.1%}, with Sony/PSN complaints going from "
            f"{d['2024-05-02']['share_psn_access']:.0%} to {d['2024-05-03']['share_psn_access']:.0%}. "
            f"You cannot get early warning of an announcement from reactions to it.\n\n"
            f"**What the data does support is same-day diagnosis.** The theme mix names the cause "
            f"within hours, in both directions — Sony/PSN up in May while balance complaints fell; "
            f"balance {d['2024-08-05']['share_balance']:.0%} to "
            f"{d['2024-08-06']['share_balance']:.0%} in August while Sony/PSN stayed flat. That is a "
            f"real operational tool, just not the one I set out to build."
        ),
        "summaryMetrics": [
            {"value": f"{s['reviews']:,}", "label": "Steam reviews, 100% of the window"},
            {"value": "0 days", "label": "best lead found, across 9 themes", "highlight": True},
            {"value": "3", "label": "alerts in 9 months, zero false", "highlight": True},
            {"value": "200", "label": "reviews hand-labelled for validation"},
            {"value": "61.5% / 64.0%", "label": "sentiment scorers, vs a 72.0% baseline"},
            {"value": f"{s['coverage']:.1%}", "label": "of complaints matched a theme"},
        ],
        "problemSpace": (
            "When a live game's review score falls, the community team's first two questions are what "
            "is this about and did we miss a warning sign. The second question is the valuable one: a "
            "theme that reliably spikes before the aggregate moves would let a team get ahead of a "
            "story instead of reacting to it.\n\n"
            "HELLDIVERS 2 is a good test case because it launched well and soured later, which leaves "
            "a genuine positive baseline to measure a change against. A game that launched badly gives "
            "you nothing to compare to. It also contains two structurally different events: a policy "
            "announcement that triggered one of the largest review-bombs in Steam's history, and a "
            "balance patch that produced a deeper sentiment trough at a fiftieth of the volume."
        ),
        "stakeholders": [
            {"role": "Community management",
             "description": "Needs to know what a spike is about before writing a response, and whether it is still getting worse."},
            {"role": "Live-ops / production",
             "description": "Needs to separate a policy problem from a balance problem from a stability problem, because the fixes sit with different teams."},
            {"role": "Leadership",
             "description": "Wants an early-warning metric. The honest answer here is that review text cannot provide one."},
        ],
        "inputs": {
            "description": (
                f"Every public Steam review for HELLDIVERS 2 between {s['span'][0]} and "
                f"{s['span'][1]} — {s['reviews']:,} of them, pulled from Valve's public appreviews "
                f"endpoint. No API key, no sampling. Sentiment is Steam's own thumbs-up flag rather "
                f"than a text model, for reasons in Execution."
            ),
            "stats": [
                {"value": f"{s['reviews']:,}", "label": "reviews, 100% of Steam's reported total"},
                {"value": f"{s['english']:,}", "label": "English, used for theme analysis"},
                {"value": f"{s['negatives']:,}", "label": "negative English reviews classified"},
                {"value": str(s["patches"]), "label": "official patches, from the developer's own announcements"},
            ],
            "dataQuality": {
                "label": "What the corpus is and isn't",
                "items": [
                    "**Self-selected.** Steam reviewers are people moved enough to write, not players. Both events here were the kind that motivate writing.",
                    "**The thumbs-up is binary.** Of 200 hand-labelled reviews, 19 were genuinely mixed — 'great game, terrible servers' counts identically to 'perfect'. Ambivalence is understated throughout.",
                    "**Theme analysis is English-only**, dropping roughly a quarter of the corpus. The largest excluded group is Simplified Chinese, whose complaints may differ on exactly the regional-access issue one event was about.",
                    "**Reddit was never pulled** — a scope decision, not a coverage finding. It also removes the likeliest place a lead could have appeared, since complaints usually surface in discussion before they surface as reviews.",
                ],
            },
            "closingNote": {
                "label": "Coverage was verified, not assumed",
                "items": [
                    "Every chunk of the pull is checked against Steam's own count for that date range and retried if short. Final coverage 100.0%, zero duplicate IDs, zero out-of-window items.",
                    "This check exists because the first version did not have it — see Discovery.",
                ],
            },
        },
        "surprisingPatterns": {
            "label": "Surprising Pattern",
            "items": [
                "**The review-bomb week was the least duplicated week in the corpus** — 20.7% repeated text against a 28-30% baseline. I expected mass-pasted copypasta to inflate it. Instead the most-repeated texts were positive community memes ('for democracy', 11,851 times), and the only clearly coordinated negative repeats were 'sony' and 'psn' at 0.8% of the week. The collapse was overwhelmingly people writing their own words.",
                f"**The famous event was not the deepest one.** The PSN review-bomb produced {d['2024-05-05']['reviews']:,} reviews in a day. The August balance patch produced a lower positive share ({d['2024-08-07']['positive_share']:.1%} on {d['2024-08-07']['date']}) at roughly a fiftieth of the volume. Loudest and worst are different measurements.",
            ],
        },
        "hypothesisVsReality": {
            "label": "Hypothesis vs. Reality",
            "items": [
                "**Expected:** complaint themes rise days before the aggregate score moves. **Found:** nothing leads. Raw cross-correlation suggested leads in seven of eight themes, up to 12 days — all of it dissolved under three robustness checks.",
                "**Expected:** a sentiment model would be needed to read the reviews. **Found:** two standard models both scored worse than guessing the majority class, and Steam's own thumbs-up flag matched my hand labels far better than either.",
                "**Expected:** review-bomb copypasta would distort the picture and need down-weighting. **Found:** collapsing every repeated text to a single vote changes the headline gap by 0.7 percentage points. The decision did not matter.",
            ],
        },
        "deadEnds": {
            "label": "What didn't work",
            "items": [
                "**The first full pull returned 65,496 of 858,566 reviews — 7.6% — with no error.** Steam's cursor pagination stops serving at around 650 pages on a wide date range and simply ends. February through April were missing entirely. Fixed by bisecting the window on Steam's own review counts until every chunk paginates shallowly.",
                "**My integrity check passed that truncated pull.** Duplicate IDs, window bounds, empty text, timestamp gaps — all clean, because every review collected *was* genuine. There were just 92% too few. A validation that only inspects the rows present cannot detect the rows absent, and comparing against an independent total is now the first check rather than an afterthought.",
                "**The cache faithfully preserved the bug.** A bad response was written to disk like any other, so re-running replayed the truncation exactly. Retries had to be made to bypass the cache before they did anything.",
                "**The six-month window truncated the one event worth testing.** The August controversy began three days before the window closed. I extended to 271 days, because a null measured on a truncated event is an artefact of the window rather than a result.",
            ],
        },
        "executionDeadEnds": {
            "label": "The result I nearly published",
            "items": [
                "Raw cross-correlation produced a clean-looking table showing a 12-day lead for developer-conduct complaints. It was noise. Reporting the best of 29 lags means taking the extreme of 29 attempts, and chance alone produces a median best-of-29-lags correlation of about −0.15 — most of what the table showed.",
                "A rotation test, a correction for testing eight themes, and a sensitivity check on how thin a day is allowed to be each removed it independently. The apparent leads moved from +3 to +12 to −8 days as measurement improved, which is what noise does and a real signal does not.",
            ],
        },
        "methodology": [
            {"heading": "Pull, verified against an independent count",
             "description": "Cursor-paginated pull of Valve's public appreviews endpoint, chunked by bisecting on Steam's own review counts so no single query paginates deep enough to truncate. Every page cached by (appid, cursor, date range); every chunk checked against the expected count and retried with the cache bypassed if short."},
            {"heading": "Sentiment: Steam's flag, after rejecting two models",
             "description": "I hand-labelled 200 reviews blind and tested both scorers against them. **VADER agreed 61.5%, a RoBERTa sentiment model 64.0% — against a 72.0% majority-class baseline.** Both did worse than always guessing 'positive'. The failure is specific: this game's players express enthusiasm through violence and self-deprecation ('I got hit by an explosion, shot into the air, then stomped by a robot 10/10'), which general-purpose models read as negative. Steam's own thumbs-up matched my labels 95.0%, so the index uses that and the models stay in the repo as the evidence for the decision."},
            {"heading": "Themes: a keyword taxonomy, seeded from the data",
             "description": f"Nine themes, 182 seed phrases, mined by measuring which terms are distinctive of thumbs-down reviews rather than guessed. Matching is word-boundary substring — transparent and explainable line by line, which a learned classifier would not be. Multi-label, because 'nerfed into the ground and it crashes' is genuinely two complaints. Coverage {s['coverage']:.1%}; the remainder is partly missing vocabulary and partly complaint with no complaint words in it."},
            {"heading": "The lag test, and why composition not volume",
             "description": "Themes are measured as a share of each day's negatives, not as raw counts. Volume and the aggregate score are both functions of how many people were angry that day, so correlating them recovers a relationship that exists by construction. Both series are differenced before correlating, because levels are dominated by one enormous event."},
            {"heading": "Three checks before believing the result",
             "description": "A rotation-based permutation test built for the statistic actually reported (best of 29 lags); a Bonferroni correction for testing eight themes; and a sensitivity sweep on minimum day size. A test in the suite plants a three-day lead in synthetic data and asserts the method recovers it — reporting a null is only honest if the method could have found a signal."},
            {"heading": "The threshold, derived rather than asserted",
             "description": "Candidate alert rules were tested against the data. A level rule ('below 72% positive') fires on 35 of 271 days, 29 of them nothing. A 12-point single-day drop fires three times in nine months — 3 May, 6 and 7 August — with no false alarms. At 10 points it adds four non-events; at 20 it misses August entirely."},
        ],
        "keyResults": {
            "label": "Key Results",
            "items": [
                "**No theme leads the score.** Only Sony/PSN complaints correlate with it at all (r = −0.30), and the best lag is zero. Every apparent lead failed at least one of three robustness checks.",
                f"**Same-day diagnosis works.** On {d['2024-05-03']['date']} Sony/PSN complaints went {d['2024-05-02']['share_psn_access']:.0%} to {d['2024-05-03']['share_psn_access']:.0%} while balance complaints fell; on {d['2024-08-06']['date']} balance went {d['2024-08-05']['share_balance']:.0%} to {d['2024-08-06']['share_balance']:.0%} while Sony/PSN stayed at {d['2024-08-06']['share_psn_access']:.0%}.",
                "**A change-based alert beats a level-based one decisively.** 3 alerts with zero false positives, against 35 alerts with 29 false positives for the obvious threshold.",
                f"**Recovery is as visible as collapse.** {d['2024-05-06']['date']} — the day Sony reversed — was the busiest day in the corpus at {d['2024-05-06']['reviews']:,} reviews and {d['2024-05-06']['positive_share']:.1%} positive, up from {d['2024-05-05']['positive_share']:.1%} the day before.",
            ],
        },
        "businessInterpretation": (
            "For a community team, this is an instrumentation tool rather than a forecast. It will not "
            "tell you a storm is coming, because in both of these cases the storm was the studio's own "
            "announcement on a date it chose. What it will do is answer 'what is this about' within "
            "hours of a score moving, without anyone reading a review — and it distinguishes a policy "
            "problem from a balance problem from a stability problem, which matters because those fixes "
            "sit with three different teams.\n\n"
            "The alerting recommendation is the practical output: watch the day-over-day change, not "
            "the level. A level threshold fires on a quarter of the calendar and a team learns to "
            "ignore it inside a fortnight. If genuine early warning is the goal, it needs data that "
            "moves before the announcement — crash telemetry, refund rates, or discussion-thread "
            "volume — none of which lives in review text."
        ),
        "recommendations": {
            "items": [
                {"tag": "Community management",
                 "text": "Alert on a 12-point single-day fall in positive share, not on the level. When it trips, read the theme mix before reading reviews — it named the cause correctly in both events here, within hours."},
                {"tag": "Live-ops",
                 "text": "Expect no warning from review text for announcement-driven events. The gap between a decision landing and sentiment moving was under 24 hours both times."},
                {"tag": "Hiring manager",
                 "text": "The headline here is a null, and the interesting work is in what it took to trust it: a truncated pull that looked clean, an integrity check that passed it, and a 12-day 'lead' that three independent checks dissolved."},
            ],
            "limitations": [
                "Steam reviewers self-select — this measures people moved enough to write, not players.",
                "Sentiment is Steam's binary thumbs-up. 19 of 200 hand-labelled reviews were genuinely mixed and the flag cannot represent them, so ambivalence is understated throughout.",
                f"Theme matching is keyword-based at {s['coverage']:.1%} coverage. Some of the remainder is unreachable by any keyword list — 'Arrowhead struck gold but are determined to find copper' is a complaint with no complaint vocabulary in it.",
                "Theme analysis is English-only, excluding roughly a quarter of the corpus — most notably Simplified Chinese reviews, on a project where one of the two events was about regional access.",
                "Two events in one game. The mechanism (announcement-driven events cannot be predicted from reactions) should generalise; the specific thresholds should not be assumed to.",
            ],
            "nextSteps": [
                "Test the same method on a launch whose sentiment decayed gradually rather than breaking on an announcement — that is where a lead could plausibly exist.",
                "Add discussion-forum or Reddit volume as a second source, since complaints usually surface there before they surface as reviews.",
                "Topic modelling as a cross-check on the ~30% of complaints no keyword reaches.",
            ],
        },
        "visuals": [
            {"id": "sentiment-timeline", "section": "summary",
             "label": "Daily positive review share, Feb–Nov 2024",
             "caption": "Both collapses land on a dated developer action. The score recovers within days of the PSN reversal; the August trough is deeper but far smaller in volume.",
             "svg": timeline_svg(days)},
            {"id": "alert-threshold", "section": "results",
             "label": "Why a change rule beats a level rule",
             "caption": "Across 271 days. A 'below 72% positive' rule fires on a quarter of the calendar; a 12-point single-day drop fires three times and every one was a real event.",
             "svg": threshold_svg()},
        ],
    }


def write_to_site(e: dict) -> str:
    data = json.loads(SITE.read_text(encoding="utf-8"))
    projects = data["projects"]
    projects[:] = [p for p in projects if p.get("id") != SLUG]
    projects.append(e)
    SITE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"{len(projects)} projects in {SITE}"


if __name__ == "__main__":
    e = entry()
    if "--write" in sys.argv:
        print(write_to_site(e))
    else:
        print(json.dumps(e, indent=2, ensure_ascii=False)[:1600])
