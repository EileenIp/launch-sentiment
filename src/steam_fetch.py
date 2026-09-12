"""Pull Steam reviews for one app, with disk caching and backoff.

Two entry points:

  recon(appid)   - cheap. One call to the store API for name/release date, one to
                   appreviews for the lifetime positive/negative split. Use this to
                   compare candidate launches before committing to one (spec Phase 0,
                   Checkpoint 0).

  fetch_reviews(appid, since, until)
                 - the real pull. Cursor-paginated, every page cached to disk, so a
                   re-run costs nothing and returns byte-identical data.

Run: python -m src.steam_fetch recon <appid>
     python -m src.steam_fetch pull <appid>
"""
from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from src import config


class SteamAPIError(RuntimeError):
    pass


def _utc(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def _cache_path(appid: int, cursor: str, start_date: int | None = None, end_date: int | None = None) -> Path:
    # Cursors contain characters that are not filesystem-safe, and can be long. The
    # date range is part of the key because the same cursor means different things
    # under different range bounds.
    key = f"{cursor}|{start_date}|{end_date}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return config.STEAM_CACHE_DIR / f"{appid}" / f"{digest}.json"


def _http_get(url: str, params: dict, session: requests.Session | None = None) -> dict:
    """GET with retry on the failures that are worth retrying (429, 5xx, timeouts)."""
    caller = session or requests
    last_error: Exception | None = None

    for attempt in range(config.MAX_RETRIES):
        try:
            response = caller.get(url, params=params, timeout=config.REQUEST_TIMEOUT_SECONDS)
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc
        else:
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    # Steam serves an HTML error page with a 200 when an appid is bad.
                    raise SteamAPIError(f"{url}: 200 but body was not JSON") from exc
            if response.status_code not in (429, 500, 502, 503, 504):
                raise SteamAPIError(f"{url}: HTTP {response.status_code}")
            last_error = SteamAPIError(f"HTTP {response.status_code}")

        if attempt < config.MAX_RETRIES - 1:
            time.sleep(config.BACKOFF_BASE_SECONDS * (2**attempt))

    raise SteamAPIError(f"{url}: gave up after {config.MAX_RETRIES} attempts") from last_error


def fetch_page(
    appid: int,
    cursor: str = "*",
    session: requests.Session | None = None,
    start_date: int | None = None,
    end_date: int | None = None,
) -> dict:
    """One page of reviews. Cached on disk by (appid, cursor, date range); a hit makes no request."""
    path = _cache_path(appid, cursor, start_date, end_date)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    params = {
        "json": 1,
        "filter": config.REVIEW_FILTER,
        "language": config.REVIEW_LANGUAGE,
        "review_type": config.REVIEW_TYPE,
        "purchase_type": config.PURCHASE_TYPE,
        "num_per_page": config.NUM_PER_PAGE,
        "cursor": cursor,
    }
    if start_date is not None and end_date is not None:
        params.update(
            {"start_date": start_date, "end_date": end_date, "date_range_type": config.DATE_RANGE_TYPE}
        )

    payload = _http_get(config.STEAM_APPREVIEWS_URL.format(appid=appid), params, session=session)
    if payload.get("success") != 1:
        raise SteamAPIError(f"appid {appid}: appreviews returned success={payload.get('success')}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    time.sleep(config.REQUEST_DELAY_SECONDS)
    return payload


def parse_review(raw: dict) -> dict:
    """Flatten one raw review into the fields the spec asks for, plus the dedup key."""
    author = raw.get("author") or {}
    return {
        "recommendationid": raw.get("recommendationid"),
        "timestamp_created": _utc(raw["timestamp_created"]),
        "timestamp_updated": _utc(raw["timestamp_updated"]) if raw.get("timestamp_updated") else None,
        "review": raw.get("review", ""),
        "voted_up": bool(raw.get("voted_up")),
        "votes_up": raw.get("votes_up", 0),
        "votes_funny": raw.get("votes_funny", 0),
        "weighted_vote_score": float(raw.get("weighted_vote_score") or 0.0),
        "comment_count": raw.get("comment_count", 0),
        "steam_purchase": bool(raw.get("steam_purchase")),
        "received_for_free": bool(raw.get("received_for_free")),
        "written_during_early_access": bool(raw.get("written_during_early_access")),
        "language": raw.get("language"),
        "playtime_at_review_minutes": author.get("playtime_at_review"),
        "playtime_forever_minutes": author.get("playtime_forever"),
        "author_num_reviews": author.get("num_reviews"),
        "author_num_games_owned": author.get("num_games_owned"),
    }


def fetch_reviews(
    appid: int,
    since: datetime | None = None,
    until: datetime | None = None,
    session: requests.Session | None = None,
    page_fetcher=fetch_page,
    on_page=None,
) -> list[dict]:
    """All reviews for appid, newest first, optionally bounded to [since, until].

    Because filter=recent is ordered newest-first, the pull stops as soon as a page's
    oldest review predates `since` — there is nothing older worth paging to.
    """
    collected: list[dict] = []
    seen_ids: set[str] = set()
    cursor = "*"
    seen_cursors: set[str] = set()

    # Ask Steam to seek to the window rather than paging back to it from today.
    start_epoch = int(since.timestamp()) if since is not None else None
    end_epoch = int(until.timestamp()) if until is not None else None

    for _ in range(config.MAX_PAGES_PER_PULL):
        if cursor in seen_cursors:
            break
        seen_cursors.add(cursor)

        payload = page_fetcher(
            appid, cursor, session=session, start_date=start_epoch, end_date=end_epoch
        )
        if on_page is not None:
            on_page(payload)

        raw_reviews = payload.get("reviews") or []
        if not raw_reviews:
            break

        page_oldest: datetime | None = None
        for raw in raw_reviews:
            parsed = parse_review(raw)
            created = parsed["timestamp_created"]
            if page_oldest is None or created < page_oldest:
                page_oldest = created

            if since is not None and created < since:
                continue
            if until is not None and created > until:
                continue
            # Steam can repeat a review across cursor boundaries.
            if parsed["recommendationid"] in seen_ids:
                continue
            seen_ids.add(parsed["recommendationid"])
            collected.append(parsed)

        if since is not None and page_oldest is not None and page_oldest < since:
            break

        next_cursor = payload.get("cursor")
        if not next_cursor:
            break
        cursor = next_cursor

    return collected


@dataclass
class ReconResult:
    appid: int
    name: str | None = None
    release_date: str | None = None
    total_reviews: int = 0
    total_positive: int = 0
    total_negative: int = 0
    review_score_desc: str | None = None
    notes: dict = field(default_factory=dict)

    @property
    def positive_share(self) -> float | None:
        if not self.total_reviews:
            return None
        return self.total_positive / self.total_reviews

    def print_report(self) -> None:
        print(f"\n--- appid {self.appid} ---")
        print(f"name: {self.name or '(store lookup failed)'}")
        print(f"release date: {self.release_date or '(unknown)'}")
        print(f"lifetime reviews: {self.total_reviews:,}")
        share = self.positive_share
        if share is not None:
            print(f"positive: {self.total_positive:,} ({share:.1%})  negative: {self.total_negative:,}")
        print(f"steam score label: {self.review_score_desc or '(none)'}")
        for label, value in self.notes.items():
            print(f"{label}: {value}")


def recon(appid: int, session: requests.Session | None = None) -> ReconResult:
    """Cheap candidate check: name, release date, lifetime review volume and split."""
    result = ReconResult(appid=appid)

    details = _http_get(
        config.STEAM_APPDETAILS_URL,
        # "basic" alone omits release_date, which is the field the whole pull window
        # is derived from; the pair returns both it and the name.
        {"appids": appid, "filters": "basic,release_date"},
        session=session,
    )
    entry = (details or {}).get(str(appid)) or {}
    if entry.get("success") and entry.get("data"):
        data = entry["data"]
        result.name = data.get("name")
        result.release_date = (data.get("release_date") or {}).get("date")

    summary = _http_get(
        config.STEAM_APPREVIEWS_URL.format(appid=appid),
        {
            "json": 1,
            "filter": config.REVIEW_FILTER,
            "language": config.REVIEW_LANGUAGE,
            "review_type": config.REVIEW_TYPE,
            "purchase_type": config.PURCHASE_TYPE,
            "num_per_page": 0,
            "cursor": "*",
        },
        session=session,
    ).get("query_summary") or {}

    result.total_reviews = summary.get("total_reviews", 0)
    result.total_positive = summary.get("total_positive", 0)
    result.total_negative = summary.get("total_negative", 0)
    result.review_score_desc = summary.get("review_score_desc")
    return result


def count_reviews(
    appid: int,
    since: datetime,
    until: datetime,
    session: requests.Session | None = None,
) -> int:
    """How many reviews Steam says exist in a window. One request, no pagination."""
    summary = _http_get(
        config.STEAM_APPREVIEWS_URL.format(appid=appid),
        {
            "json": 1,
            "filter": config.REVIEW_FILTER,
            "language": config.REVIEW_LANGUAGE,
            "review_type": config.REVIEW_TYPE,
            "purchase_type": config.PURCHASE_TYPE,
            "num_per_page": 0,
            "cursor": "*",
            "start_date": int(since.timestamp()),
            "end_date": int(until.timestamp()),
            "date_range_type": config.DATE_RANGE_TYPE,
        },
        session=session,
    ).get("query_summary") or {}
    return summary.get("total_reviews", 0)


def plan_chunks(
    appid: int,
    since: datetime,
    until: datetime,
    counter=count_reviews,
    _depth: int = 0,
) -> list[tuple[datetime, datetime, int]]:
    """Split a window into ranges small enough to paginate fully.

    Bisects on Steam's own review count rather than on a fixed calendar interval,
    because review density varies by orders of magnitude across a launch window —
    a fixed weekly split would be wasteful in quiet months and still too deep
    during a review-bomb.
    """
    total = counter(appid, since, until)

    if total <= config.SAFE_CHUNK_REVIEWS or _depth >= config.MAX_CHUNK_SPLIT_DEPTH:
        return [(since, until, total)]

    midpoint = since + (until - since) / 2
    # Sub-second ranges cannot be split further.
    if midpoint <= since or midpoint >= until:
        return [(since, until, total)]

    return plan_chunks(appid, since, midpoint, counter, _depth + 1) + plan_chunks(
        appid, midpoint, until, counter, _depth + 1
    )


def fetch_window_chunked(
    appid: int,
    since: datetime,
    until: datetime,
    session: requests.Session | None = None,
    page_fetcher=fetch_page,
    counter=count_reviews,
    on_page=None,
    on_chunk=None,
    max_workers: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Pull a whole window via chunks, fetched concurrently. Returns (reviews, coverage rows).

    Chunks run in parallel because each owns an independent cursor sequence. Pages
    within a chunk stay sequential — a page's cursor only exists once the previous
    page has been read.

    Results are merged in chunk order rather than completion order, so the corpus is
    byte-identical whatever the workers happen to do. `max_workers=1` runs inline,
    which keeps tests deterministic.
    """
    chunks = plan_chunks(appid, since, until, counter=counter)
    workers = max_workers if max_workers is not None else config.MAX_CONCURRENT_CHUNKS

    thread_state = threading.local()

    def pull_one(indexed_chunk):
        index, (chunk_since, chunk_until, expected) = indexed_chunk
        # requests.Session is not documented as thread-safe; give each worker its own.
        if session is not None:
            worker_session = session
        else:
            if not hasattr(thread_state, "session"):
                thread_state.session = requests.Session()
            worker_session = thread_state.session

        chunk_reviews = fetch_reviews(
            appid,
            since=chunk_since,
            until=chunk_until,
            session=worker_session,
            page_fetcher=page_fetcher,
            on_page=on_page,
        )
        return index, chunk_since, chunk_until, expected, chunk_reviews

    indexed = list(enumerate(chunks, start=1))
    if workers <= 1:
        results = [pull_one(item) for item in indexed]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(pull_one, item) for item in indexed]
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                if on_chunk is not None:
                    on_chunk(
                        {
                            "chunk": result[0],
                            "since": result[1],
                            "until": result[2],
                            "expected": result[3],
                            "fetched": len(result[4]),
                            "new": None,  # not yet merged; filled in below
                        }
                    )

    collected: list[dict] = []
    seen_ids: set[str] = set()
    coverage: list[dict] = []

    for index, chunk_since, chunk_until, expected, chunk_reviews in sorted(results, key=lambda r: r[0]):
        new = 0
        for review in chunk_reviews:
            if review["recommendationid"] in seen_ids:
                continue
            seen_ids.add(review["recommendationid"])
            collected.append(review)
            new += 1

        row = {
            "chunk": index,
            "since": chunk_since,
            "until": chunk_until,
            "expected": expected,
            "fetched": len(chunk_reviews),
            "new": new,
        }
        coverage.append(row)
        if workers <= 1 and on_chunk is not None:
            on_chunk(row)

    return collected, coverage


def window_for_launch(launch_date: str) -> tuple[datetime, datetime]:
    """The spec's pull window: PRE_LAUNCH_DAYS before launch to POST_LAUNCH_DAYS after."""
    launch = datetime.fromisoformat(launch_date).replace(tzinfo=timezone.utc)
    return (
        launch - timedelta(days=config.PRE_LAUNCH_DAYS),
        launch + timedelta(days=config.POST_LAUNCH_DAYS),
    )


def weekly_volumes(reviews: list[dict]) -> list[dict]:
    """Per-ISO-week review counts and positive share — the Checkpoint 0 volume report."""
    buckets: dict[str, dict] = {}
    for review in reviews:
        created = review["timestamp_created"]
        year, week, _ = created.isocalendar()
        key = f"{year}-W{week:02d}"
        bucket = buckets.setdefault(key, {"week": key, "reviews": 0, "positive": 0})
        bucket["reviews"] += 1
        bucket["positive"] += int(review["voted_up"])

    rows = []
    for key in sorted(buckets):
        bucket = buckets[key]
        bucket["positive_share"] = bucket["positive"] / bucket["reviews"]
        rows.append(bucket)
    return rows


def _main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 1
    command, appid = argv[1], int(argv[2])

    if command == "recon":
        recon(appid).print_report()
        return 0

    if command == "pull":
        if not config.TARGET_LAUNCH_DATE:
            print("config.TARGET_LAUNCH_DATE is unset — Checkpoint 0 has not been decided yet.")
            return 1
        since, until = window_for_launch(config.TARGET_LAUNCH_DATE)
        reviews = fetch_reviews(appid, since=since, until=until)
        print(f"pulled {len(reviews):,} reviews in [{since.date()}, {until.date()}]")
        for row in weekly_volumes(reviews):
            print(f"  {row['week']}  {row['reviews']:>6,}  {row['positive_share']:.1%} positive")
        return 0

    print(f"unknown command: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
