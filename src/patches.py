"""Phase 4: the game's own update timeline, for annotating the charts.

Valve's news endpoint carries the developer's patch notes with publish dates, so
the timeline comes from the game rather than from a news article someone wrote
about it. Cached to disk like every other pull.

Run: python -m src.patches
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from src import config, steam_fetch

NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
CACHE = config.RAW_DATA_DIR / "steam_news_{appid}.json"

# Patch notes rather than community round-ups or store promos.
PATCH_TITLE = re.compile(r"\b(patch|hotfix|update|\d+\.\d+)\b", re.I)


def fetch(appid: int | None = None, count: int = 100, pages: int = 12) -> list[dict]:
    """News items, paged backwards with `enddate`.

    A plain request returns only the most recent items — for this app that reaches
    back to Dec 2024, which is after the analysis window ends. Paging backwards is
    the only way to reach a launch window this old.
    """
    appid = appid or config.TARGET_APPID
    path = CACHE.parent / CACHE.name.format(appid=appid)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    seen: dict = {}
    end = None
    for _ in range(pages):
        params = {"appid": appid, "count": count, "maxlength": 1}
        if end is not None:
            params["enddate"] = end
        items = (steam_fetch._http_get(NEWS_URL, params).get("appnews") or {}).get("newsitems") or []
        if not items:
            break
        fresh = [item for item in items if item["gid"] not in seen]
        seen.update({item["gid"]: item for item in items})
        oldest = min(item["date"] for item in items)
        if not fresh or (end is not None and oldest >= end):
            break
        end = oldest - 1

    rows = sorted(seen.values(), key=lambda item: item["date"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return rows


def patches_in_window(appid: int | None = None, since: str | None = None, until: str | None = None):
    """Patch-note entries inside the analysis window, oldest first."""
    appid = appid or config.TARGET_APPID
    if since is None or until is None:
        start, end = steam_fetch.window_for_launch(config.TARGET_LAUNCH_DATE)
        since, until = since or start.date().isoformat(), until or end.date().isoformat()

    rows = []
    for item in fetch(appid):
        date = datetime.fromtimestamp(item["date"], tz=timezone.utc).date().isoformat()
        if not (since <= date <= until):
            continue
        title = (item.get("title") or "").strip()
        if not PATCH_TITLE.search(title):
            continue
        # The feed mixes the developer's own announcements with press coverage.
        # Only the former are patch dates; the latter are reactions to them.
        official = item.get("feedname") == "steam_community_announcements"
        rows.append({"date": date, "title": title, "url": item.get("url", ""),
                     "official": official, "source": item.get("feedlabel", "")})

    rows.sort(key=lambda r: r["date"])
    return rows


if __name__ == "__main__":
    rows = patches_in_window()
    print(f"{len(rows)} patch-note entries inside the analysis window\n")
    for row in rows:
        print(f"  {row['date']}  {row['title'][:80]}")
