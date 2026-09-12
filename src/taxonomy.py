"""Phase 3: the complaint theme taxonomy. EILEEN'S FILE — edit freely.

Eight themes: the spec's six, plus `balance` and `dev_conduct`, which Eileen added
on 2026-09-13 after mining showed the two largest complaint clusters in this corpus
had nowhere to go.

Every seed phrase below was drawn from `src/mine_themes.py` output against the real
corpus — terms that actually occur in Helldivers 2 negative reviews, not a generic
guess at what a complaint looks like. That said, these are a STARTING POINT. The
spec puts the taxonomy in Eileen's hands because she knows which of these are
load-bearing and which are noise, and because an interviewer will ask why a
particular phrase counts as monetisation rather than value.

Matching is substring-on-normalised-text: transparent, tunable, and explainable
line by line. A review can carry several themes; that is deliberate, since
"nerfed into the ground and it crashes" is genuinely two complaints.
"""

THEMES = {
    "bugs_stability": [
        "crash", "crashes", "crashing", "freeze", "freezes", "freezing",
        "broken game", "game broken", "still broken", "bugged", "buggy",
        "buggy mess", "new bugs", "breaking bugs", "through walls",
        "through terrain", "clipping", "invisible", "doesn't work",
        "does not work", "even work", "unusable", "bricking", "unplayable",
        "literally unplayable", "glitch", "softlock", "disconnect",
        # Added 2026-09-13. "server" was simply missing, on a game whose launch
        # was defined by server capacity failures — the single largest gap in the
        # first taxonomy. "kicked" is the loosest of these: it can mean kicked by
        # a host rather than dropped by the server.
        "server", "servers", "server issues", "matchmaking", "cannot connect",
        "can't connect", "kicked", "desync", "lost progress",
    ],
    "performance": [
        "unoptimized", "unoptimised", "optimization", "optimisation",
        "stutter", "stutters", "stuttering", "fps", "frame rate", "framerate",
        "lag", "laggy", "low end", "performance",
    ],
    "price_value": [
        "refund", "want refund", "requested refund", "money back", "want money",
        "waste money", "waste time", "save money", "wasted", "give money",
        "don't waste", "not worth", "overpriced",
    ],
    "monetisation": [
        "warbond", "warbonds", "new warbond", "behind warbonds", "paywall",
        "behind paywall", "super credits", "microtransaction", "scam",
        "pay game", "locked behind",
    ],
    "content_design": [
        "slop", "mediocre", "underwhelming", "less fun", "not fun",
        "fun anymore", "unfun", "used fun", "chore", "slog", "repetitive",
        "game dead", "dumpster", "game trash", "game sucks", "disappointment",
        "boring", "stale", "content drought",
        # Added 2026-09-13. REVISIT "grind"/"grindy": in this game grinding is
        # usually for Super Credits, which makes it arguably a monetisation
        # complaint. Multi-label softens the problem — a review mentioning both
        # grind and warbonds picks up both themes rather than the wrong one —
        # but if monetisation volume looks thin, this is the first place to look.
        "aiming", "vaulting", "clunky", "grind", "grindy", "tedious",
    ],
    # Added by Eileen 2026-09-13 — the largest cluster the spec's six had no home for.
    "balance": [
        "nerf", "nerfs", "nerfed", "nerfing", "constant nerfs", "keep nerfing",
        "nerf weapons", "nerfing weapons", "nerfing everything", "nerfing fun",
        "buffs enemies", "buff enemies", "buffing enemies", "instead buffing",
        "balance team", "balancing team", "balance decisions",
        "balancing decisions", "game balance", "game balancing", "unbalanced",
        "durable damage", "monkey paw", "grunt fantasy", "into the ground",
        "bullet sponge", "spawn rates", "enemy spawns", "ragdolling",
        "penetration", "weaker", "gets worse", "getting worse", "game worse",
        "every patch", "every update",
    ],
    # Added by Eileen 2026-09-13 — developer and community conduct.
    "dev_conduct": [
        "doxxed", "doxxing", "death threats", "content creators", "ama",
        "glazedivers", "arrogant", "antagonistic", "devs hate", "devs play",
        "devs don't", "devs dont", "developers don't", "unprofessional",
        "tone deaf", "moderator", "moderators", "moderation", "banned",
        "blocked", "toxic community", "insulting", "sweet summer",
        "summer child", "incompetent", "incompetence", "excuses", "lied",
        "ignoring", "ignored", "tricked",
    ],
    # Added by Eileen 2026-09-13. Platform access, kept separate from dev_conduct
    # because it is about Sony and account requirements rather than developer
    # behaviour — and because it is the proximate cause of the W18 spike, so
    # burying it inside another theme would hide the one most likely to answer
    # the leading-indicator question.
    #
    # Two seeds here are broader than the rest and worth a second look when
    # editing: "region" can match unrelated uses, and "outsourced" was surfaced by
    # mining at high lift but its link to the account-linking story is unverified
    # — it may be about outsourced development or support instead.
    "psn_access": [
        "sony lied", "psn", "playstation account", "playstation network",
        "account linking", "link account", "delisted", "still delisted",
        "delisted countries", "still unavailable", "region locked",
        "region lock", "not available in", "outsourced", "sony",
    ],
}
