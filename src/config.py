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
