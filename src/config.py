"""All tunable parameters for the project live here — no magic numbers in the pipeline code."""
from pathlib import Path

RANDOM_SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
STEAM_CACHE_DIR = RAW_DATA_DIR / "steam_cache"

# --- Phase 0: the launch under analysis ---
#
# EILEEN DECIDES (Checkpoint 0) — decided 2026-09-13: HELLDIVERS 2.
#
# Chosen over Cyberpunk 2077, which was considered and rejected. Recon numbers
# that drove it (pulled 2026-09-13, real):
#   Cyberpunk 2077  appid 1091500  released 2020-12-09   979,443 reviews  86.9% positive
#   HELLDIVERS 2    appid  553850  released 2024-02-08 1,161,809 reviews  75.5% positive
#
# Why this one: Helldivers 2 launched well and soured later, so there is a genuine
# positive baseline before the sentiment event — which is what makes the spec's
# leading-indicator question answerable at all. Cyberpunk collapsed on day one,
# leaving nothing for complaint themes to lead, and is also the most-analysed
# launch in games data, forfeiting the spec's "chosen for its specific arc"
# defence against the overused-dataset pitfall.
#
# Known deviation from the spec, accepted deliberately: the spec asks for a launch
# 6-24 months old and this one is 31 months (Feb 2024 vs today 2026-09-13). Eileen's
# call. The trade is recency against a far better-shaped sentiment arc. Worth having
# a rehearsed answer for, since "why this launch" is an obvious interview question.
TARGET_APPID: int | None = 553850
TARGET_LAUNCH_DATE: str | None = "2024-02-08"  # store release date, confirmed via appdetails

# Pull window, relative to TARGET_LAUNCH_DATE (spec Phase 0): two weeks before
# launch to catch any early-access run-up, six months after to cover the full
# arc including patch-driven recovery.
PRE_LAUNCH_DAYS = 14
POST_LAUNCH_DAYS = 183

# --- Scope ---
#
# EILEEN DECIDES, 2026-09-13: Steam only for now. Reddit is not pulled.
#
# State this as what it is. The spec allows a Steam-only project when "Reddit
# coverage is too thin" — that is NOT what happened here. Reddit was never
# attempted; this is a scope decision, not a data-availability finding, and the
# write-up must not blur the two.
#
# What it costs: the leading-indicator question loses its most plausible early
# channel. Complaints typically surface in discussion threads before they surface
# as review-score movement, so Reddit was the likeliest place for a lead to be
# visible. Steam-only narrows the claim to "did complaint themes inside reviews
# move before the aggregate score did" — still a real question against 860k
# reviews at daily granularity, but a smaller one than the spec scoped.
#
# Reversible: the corpus, scorers and lag analysis are all source-agnostic.
SOURCES = ("steam",)

# --- Phase 1: corpus hygiene decisions ---
#
# EILEEN DECIDES, 2026-09-13: reviews where steam_purchase is false stay in.
#
# They are 218,449 of 834,605 in the first full pull — 26.2%, far too large a
# slice to drop silently. The context that makes keeping them defensible: the May
# 2024 sentiment event was about an account-linking requirement, so players who
# did not buy through Steam are plausibly part of the story rather than noise
# around it. Excluding them would be quietly excluding a group with a specific
# reason to be angry.
#
# What this obliges the write-up to do: state the 26.2% share openly, and if
# including them materially changes a headline number, show it both ways rather
# than only the version that was kept. Same discipline the spec demands for the
# copypasta call.
KEEP_NON_STEAM_PURCHASES = True

# EILEEN DECIDES, 2026-09-13: review-bomb copypasta is weighted DOWN rather than
# counted as organic sentiment.
#
# There is no neutral option here — mass-coordinated identical reviews are both
# "not one person's opinion expressed N times" and "a real community event that
# genuinely happened." Weighting down says the first reading governs the sentiment
# index. What it does not do is hide the second: per the spec, the README shows the
# key moment BOTH ways, weighted and unweighted, so a reader can see how much of
# W18's collapse is coordination and how much is distinct people.
#
# REVISED after detection ran, 2026-09-13. Eileen delegated the revised call to
# the agent ("your choice"), so this one is the AGENT'S judgement, not hers —
# flagged explicitly because the spec marks this as an interview question whose
# answer is supposed to be hers. Overruling it costs nothing: set both back.
#
# Down-weighting is NOT applied, because the evidence contradicts the premise:
#
#   - W18, the spike week, is the LEAST duplicated week in the window: 20.7%
#     repeated text against a 28-30% baseline in ordinary weeks.
#   - The largest repeated texts are positive community memes ("for democracy",
#     11,851 corpus-wide, 96% positive in W18), not coordinated negativity. The
#     only clearly campaign-related repeats in W18 are "sony" (1,212, 26%
#     positive) and "psn" (837, 11% positive) — together 0.8% of the week.
#   - "we won" / "democracy prevails" / "democracy has prevailed" appear in the
#     thousands at 100% positive inside W18 and are absent from baseline weeks:
#     the reversal is being celebrated in the same week as the bomb.
#
# So down-weighting would strip more positive weight than negative from the very
# week it was meant to correct.
#
# Measured, rather than argued (see hygiene.both_ways): collapsing every repeated
# text to a single vote moves EVERY week down 1.8-4.9pp, and moves W18 down least
# of all (-2.1pp). The W18-vs-baseline gap goes from 26.7pp to 26.0pp. The
# decision changes no conclusion, which is the honest answer to the interview
# question and a stronger one than either weighting scheme.
DOWNWEIGHT_COPYPASTA = False
COPYPASTA_WEIGHT: float | None = None

# EILEEN DECIDES, 2026-09-13: scoring is English-only.
#
# The rule: keep reviews whose Steam `language` field is exactly "english".
# That is 631,806 of 860,018 — 73.5%.
#
# Why: VADER is an English lexicon by construction, so scoring non-English text
# with it produces numbers that look real and mean nothing. A scorer comparison
# run over 27% such text would not settle anything. Hand-labelling would also be
# impossible across Chinese, German and Russian.
#
# The bias this introduces, to be stated in the write-up rather than buried:
# 77,432 Simplified Chinese reviews (9.0%) are the largest excluded group, and a
# non-English playerbase may complain about different things — regional pricing,
# server locations, localisation quality — so the theme mix in Phase 3 describes
# English-speaking players, not all players.
SCORING_LANGUAGES = ("english",)

# Validation sampling: reviews of 4 words or fewer ("egg", "nice", "FREEEEEEDOM")
# are trivially classified by any scorer, so they inflate both scorers' agreement
# equally and hide the difference the validation set exists to measure — while
# consuming a third of the labelling hour. They are excluded from the sample and
# checked separately by scorer-vs-scorer agreement, which needs no hand labels.
#
# The consequence, which the write-up states plainly: the agreement numbers
# describe substantive reviews, not the corpus as a whole.
VALIDATION_MIN_WORDS = 5

# --- Steam API ---
#
# The public appreviews endpoint. No key, no auth, no quota published by Valve.
STEAM_APPREVIEWS_URL = "https://store.steampowered.com/appreviews/{appid}"
STEAM_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"

# 100 is the documented maximum; anything larger is silently clamped by Valve.
NUM_PER_PAGE = 100

# filter=recent returns reviews newest-first by creation date, which is what lets
# a historical window pull terminate early (page until timestamps fall before the
# window start). The alternative, filter=all, sorts by helpfulness and is the one
# that supports day_range — but it also re-orders as votes accrue, so an identical
# re-run would not return an identical corpus. Reproducibility wins here.
REVIEW_FILTER = "recent"
REVIEW_LANGUAGE = "all"
REVIEW_TYPE = "all"
PURCHASE_TYPE = "all"

# Undocumented but verified working (2026-09-13, appid 553850): start_date/end_date
# as unix timestamps with date_range_type="include" makes the endpoint seek directly
# to a historical window. Without it, reaching a 2024 launch window means paging
# backwards through every review since, which for a million-review game is tens of
# thousands of requests to reach data the window starts at.
DATE_RANGE_TYPE = "include"

# Valve publishes no rate limit for this endpoint. Started at 1.5s and dropped to
# 0.5s after ~1,150 sequential requests returned zero 429s — at 8,586 pages for
# this window, 1.5s meant a 3.6-hour pull. The backoff below plus the page cache
# make a wrong guess cheap: a rate-limited run retries, and an abandoned one
# resumes from disk rather than re-fetching.
REQUEST_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2.0

# Steam occasionally returns the same cursor forever instead of an empty page at
# the end of a listing. Without a hard stop that is an infinite loop.
MAX_PAGES_PER_PULL = 2000

# Cursor pagination silently dies on deep listings. Measured 2026-09-13 on appid
# 553850: a request for the full 2024-01-25..2024-08-09 window (858,566 reviews)
# stopped after 656 pages with 65,496 collected — 7.6% coverage, no error, no
# warning, and the truncation looked like clean data. The same endpoint returned
# 48,706 of 48,708 (100.0%) for a single launch week in 489 pages, terminating
# properly on an empty page.
#
# So the window is split into chunks small enough that no single cursor sequence
# gets near that depth. 40,000 leaves clear margin below the observed failure
# point while keeping the number of count-probe requests low.
SAFE_CHUNK_REVIEWS = 40_000

# Guard against pathological recursion if a single day somehow exceeds the chunk
# size — at that point the chunk is taken as-is and the coverage check reports it.
MAX_CHUNK_SPLIT_DEPTH = 12

# Chunks have independent cursor sequences, so they can be fetched concurrently;
# pages *within* a chunk cannot, since each cursor comes from the previous page.
# 4 workers each pausing REQUEST_DELAY_SECONDS between pages puts the aggregate
# rate near 3-4 requests/second. Measured sequentially at ~50 pages/min, which
# made the 8,601-page pull a ~3 hour job.
MAX_CONCURRENT_CHUNKS = 4

# Steam intermittently serves an empty page mid-sequence, which reads as a clean
# end-of-listing. Measured 2026-09-13: with 4 workers, 2 of 24 chunks came back
# 12.7% and 62% short while the single largest chunk (38,262 reviews) completed
# fine — so this is transient, not the pagination depth limit. Because the dud
# response gets cached like any other, a plain re-run replays the truncation;
# retries must bypass the cache.
CHUNK_SHORTFALL_TOLERANCE = 0.002  # deletions between count and fetch run ~0.03%
MAX_CHUNK_RETRIES = 3
