# Project spec — Launch Sentiment: What Went Wrong, and When

**For:** Eileen Ip · portfolio project
**Theme:** Social media & marketing
**Agent:** one builder, Sonnet, in Claude Code. Same working rules as the churn spec: stop at every **EILEEN DECIDES**, never invent a number, never write `NOTES.md`, read spec + `NOTES.md` + last commit at session start, commit per phase.

---

## The business question

> When a launch goes sideways, what exactly turned sentiment — bugs, price, monetisation, performance — and how early was it visible before the review score moved?

The differentiator is the **leading-indicator claim**: not "sentiment was negative" but "complaint theme X spiked N days before the aggregate score dropped." That's what a community or marketing team can act on.

**Who cares:** community management, marketing, and product teams in the launch window; the same monitoring pattern applies to any media release.

---

## Phase 0 — Pick the launch and verify the data

**EILEEN DECIDES first:** which launch. Criteria: shipped 6–24 months ago (complete arc, still discussed), had a visible sentiment event (score drop, review-bomb, patch-driven recovery), and generates enough volume (thousands of Steam reviews minimum). A game with a rocky launch and a documented recovery gives the best narrative arc. Pick something you genuinely know — you'll be asked about it as a person, not just an analyst.

**AGENT, then:**

- **Steam reviews** via the official `appreviews` endpoint — paginated with `cursor`, `filter=recent`, `num_per_page=100`, respecting rate limits with backoff and disk caching. Pull the full launch window: 2 weeks pre-launch (if early access) through 6 months post. Fields: review text, timestamp, voted_up, playtime at review, steam_purchase, received_for_free, language.
- **Reddit** via PRAW (Eileen creates the API credentials — agent never handles them in code, they live in `.env`, gitignored): the game's subreddit plus r/Games threads, submissions and top-level comments across the same window. Note PRAW's listing limits (~1000 items per listing) — pull via multiple sort orders and time filters, dedupe by ID, and report honestly what coverage that achieves. If coverage is too thin, the project stands on Steam reviews alone — say so rather than pretending.
- Report volumes per week, per source. **Checkpoint 0.**

## Phase 1 — Corpus hygiene

**AGENT:** dedupe (copypasta and repost storms are real during review-bombs — quantify them, they're a finding, not just noise); language filter with a stated rule; bot/spam heuristics reported before applied.

**EILEEN DECIDES:** whether review-bomb copypasta counts as sentiment or gets weighted down. There's no neutral answer — mass-coordinated one-word reviews are both "not organic sentiment" and "a real community event." Whatever you choose, the README shows the analysis both ways at the key moment. This is a genuinely interesting judgement call; treat it as a feature of the project.

**Checkpoint 1.**

## Phase 2 — Sentiment scoring, with validation you own

**AGENT:** implement two scorers behind one interface: VADER (fast, transparent, lexicon-based) and a transformer sentiment model (e.g. a RoBERTa sentiment checkpoint via `transformers`). Score the full corpus with both.

**EILEEN DOES — the validation set:** hand-label 200 randomly sampled reviews (positive/negative/mixed-neutral). Roughly an hour. The agent then reports both scorers' agreement with your labels, overall and on the hard cases (sarcasm, "great game but…" reviews).

**EILEEN DECIDES:** which scorer is the headline, using your own validation numbers — not a blog post's benchmark. "I hand-labelled 200 reviews and chose X because it agreed with me 87% vs 74%, and gamer sarcasm broke the lexicon approach" is a complete interview answer with your fingerprints on it. Gaming language famously breaks generic sentiment tools ("sick", "broken", "OP", "grind") — your validation set is where that shows up.

**Tests (pytest):** scorer interface returns identical schema for both models; timestamps of all scored items fall inside the window; the validation-set agreement numbers are computed from the frozen label file, not regenerated.

**Checkpoint 2.**

## Phase 3 — Theme classification (the absorbed support-ticket layer)

**AGENT:** classify each negative item into themes: **bugs/stability, performance, price/value, monetisation, content/design, other** — via a keyword/rule taxonomy first (transparent, tunable), optionally topic modelling (BERTopic/LDA) as a cross-check that the taxonomy isn't missing a theme. Report theme volumes over time.

**EILEEN DECIDES:** the taxonomy itself — the seed keywords per theme, reviewed and edited by hand. An agent's guess at what "monetisation complaint" looks like for *this* game will be generic; yours won't be.

## Phase 4 — The time-series claim

**AGENT:**

- Daily sentiment index per source; theme-share over time; overlay the aggregate Steam review score.
- The core analysis: for the identified sentiment event(s), which theme moved first, and by how many days did theme-level negativity lead the aggregate score? Cross-correlation at lags, plus a plain plot a non-technical reader can see the lead in.
- Patch-date annotation: pull the game's update timeline and mark it. Did sentiment recover after specific patches?

**EILEEN DECIDES:** whether the leading-indicator claim actually holds in this data. If the lead is a day or the correlation is mush, the honest finding is "aggregate score and themes moved together — early warning here needed different data (crash telemetry, refund rates)." Write that if it's true. A defensible null beats an overstated lead.

**Checkpoint 4.**

## Phase 5 — Deliverables

The four-output pattern from the churn spec: self-contained HTML dashboard on GitHub Pages (hero: the timeline — sentiment, themes, patches, score on one chart with a date scrubber), stakeholder deck, 3–4 page report, website case study. Plain language: "complaints about crashes doubled in the three days before the score fell," not "negative class share increased."

**EILEEN WRITES:** "what didn't work," limitations (Steam reviewers self-select; Reddit coverage bounds; sentiment tools vs sarcasm — cite your own validation numbers), and the recommendation: what a community team should monitor and at what threshold.

---

## Readiness gate notes

- **Visualisation-only?** No — two-scorer validation, theme classification, and the lag analysis are the depth layers.
- **Overused data?** Steam review sentiment projects exist; the hand-labelled validation, theme taxonomy, and leading-indicator test are the differentiators. A launch chosen for its specific arc also makes it non-generic by construction.
- **Business context?** Cleared — launch-window monitoring is a staffed function at every publisher.
- **Tutorial clone?** Medium risk if it collapses to "VADER on reviews, plot the line." The validation set and the lag claim are what keep it out of that bucket — they are not optional.

## Screening audit

Churn spec Appendix C before shipping. At-risk rows: **Depth of analysis** (if the lag analysis is skipped) and **Defendability** (the scorer choice must rest on your validation numbers, nothing else).

## Cost discipline

Estimate A$15–25. The pulls are cheap; the transformer scoring pass is the compute-heavy step — run it once, cache scores to disk, never re-score. Stop and reassess past A$35.

## Definition of done

- [ ] Full-window Steam corpus cached; Reddit coverage achieved and honestly stated
- [ ] 200-item hand-labelled validation set, frozen, with agreement numbers for both scorers
- [ ] Theme taxonomy edited by Eileen, volumes over time
- [ ] Lag analysis with a stated, honest conclusion — including a null if that's the truth
- [ ] `pytest` green
- [ ] Four deliverables; case study with real numbers only
- [ ] Rehearsed answers: why this scorer, how you validated it, why these themes, what the lead time was and how sure you are
