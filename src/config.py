"""All tunable parameters for the project live here — no magic numbers in the pipeline code."""
from pathlib import Path

RANDOM_SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
STEAM_CACHE_DIR = RAW_DATA_DIR / "steam_cache"

# --- Phase 0: the launch under analysis ---
#
# EILEEN DECIDES (Checkpoint 0). Deliberately left unset: the spec requires the
# launch to be one she knows well enough to be questioned about as a player, so
# the agent must not fill this in. Set TARGET_APPID and TARGET_LAUNCH_DATE
# together — every window calculation below derives from the launch date.
TARGET_APPID: int | None = None
TARGET_LAUNCH_DATE: str | None = None  # "YYYY-MM-DD", the store release date

# Pull window, relative to TARGET_LAUNCH_DATE (spec Phase 0): two weeks before
# launch to catch any early-access run-up, six months after to cover the full
# arc including patch-driven recovery.
PRE_LAUNCH_DAYS = 14
POST_LAUNCH_DAYS = 183

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

# Valve publishes no rate limit for this endpoint. 1.5s between pages is well
# inside what the community reports as safe; the backoff below handles the case
# where that assumption turns out to be wrong on a large pull.
REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2.0

# Steam occasionally returns the same cursor forever instead of an empty page at
# the end of a listing. Without a hard stop that is an infinite loop.
MAX_PAGES_PER_PULL = 2000
