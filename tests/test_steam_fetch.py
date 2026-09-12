"""Tests for the Steam pull. No test here touches the network."""
from datetime import datetime, timezone

import pytest

from src import config, steam_fetch


def _epoch(year, month, day):
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())


def _raw(rid, year, month, day, voted_up=True, review="text"):
    return {
        "recommendationid": str(rid),
        "timestamp_created": _epoch(year, month, day),
        "timestamp_updated": _epoch(year, month, day),
        "review": review,
        "voted_up": voted_up,
        "votes_up": 3,
        "votes_funny": 0,
        "weighted_vote_score": "0.51",
        "comment_count": 1,
        "steam_purchase": True,
        "received_for_free": False,
        "written_during_early_access": False,
        "language": "english",
        "author": {
            "playtime_at_review": 620,
            "playtime_forever": 900,
            "num_reviews": 12,
            "num_games_owned": 140,
        },
    }


def _pager(pages):
    """Fake page_fetcher: serves the given pages in order, keyed by cursor."""
    calls = {"count": 0}

    def fetch(appid, cursor="*", session=None, start_date=None, end_date=None):
        index = calls["count"]
        calls["count"] += 1
        if index >= len(pages):
            return {"reviews": [], "cursor": None}
        return pages[index]

    fetch.calls = calls
    return fetch


def test_parse_review_maps_every_spec_field():
    parsed = steam_fetch.parse_review(_raw(1, 2025, 3, 4, voted_up=False, review="crashes"))

    assert parsed["recommendationid"] == "1"
    assert parsed["review"] == "crashes"
    assert parsed["voted_up"] is False
    assert parsed["steam_purchase"] is True
    assert parsed["received_for_free"] is False
    assert parsed["language"] == "english"
    assert parsed["playtime_at_review_minutes"] == 620
    assert parsed["timestamp_created"] == datetime(2025, 3, 4, tzinfo=timezone.utc)
    # Steam sends weighted_vote_score as a string.
    assert parsed["weighted_vote_score"] == pytest.approx(0.51)


def test_parse_review_survives_a_missing_author_block():
    raw = _raw(2, 2025, 3, 4)
    del raw["author"]

    parsed = steam_fetch.parse_review(raw)

    assert parsed["playtime_at_review_minutes"] is None


def test_fetch_reviews_follows_the_cursor_until_pages_run_out():
    pages = [
        {"reviews": [_raw(1, 2025, 5, 3), _raw(2, 2025, 5, 2)], "cursor": "c2"},
        {"reviews": [_raw(3, 2025, 5, 1)], "cursor": "c3"},
        {"reviews": [], "cursor": None},
    ]

    reviews = steam_fetch.fetch_reviews(123, page_fetcher=_pager(pages))

    assert [r["recommendationid"] for r in reviews] == ["1", "2", "3"]


def test_fetch_reviews_stops_when_the_cursor_repeats():
    """Steam can hand back the same cursor forever instead of an empty page."""
    stuck = {"reviews": [_raw(1, 2025, 5, 3)], "cursor": "same"}

    def fetch(appid, cursor="*", session=None, start_date=None, end_date=None):
        return stuck

    reviews = steam_fetch.fetch_reviews(123, page_fetcher=fetch)

    assert len(reviews) == 1


def test_fetch_reviews_deduplicates_ids_repeated_across_pages():
    pages = [
        {"reviews": [_raw(1, 2025, 5, 3), _raw(2, 2025, 5, 2)], "cursor": "c2"},
        {"reviews": [_raw(2, 2025, 5, 2), _raw(3, 2025, 5, 1)], "cursor": "c3"},
        {"reviews": [], "cursor": None},
    ]

    reviews = steam_fetch.fetch_reviews(123, page_fetcher=_pager(pages))

    assert [r["recommendationid"] for r in reviews] == ["1", "2", "3"]


def test_fetch_reviews_excludes_items_outside_the_window():
    pages = [
        {"reviews": [_raw(1, 2025, 6, 10), _raw(2, 2025, 5, 10), _raw(3, 2025, 4, 1)], "cursor": "c2"},
        {"reviews": [], "cursor": None},
    ]
    since = datetime(2025, 5, 1, tzinfo=timezone.utc)
    until = datetime(2025, 6, 1, tzinfo=timezone.utc)

    reviews = steam_fetch.fetch_reviews(123, since=since, until=until, page_fetcher=_pager(pages))

    assert [r["recommendationid"] for r in reviews] == ["2"]


def test_fetch_reviews_stops_paging_once_a_page_predates_the_window():
    """filter=recent is newest-first, so there is nothing older worth fetching."""
    pages = [
        {"reviews": [_raw(1, 2025, 5, 10)], "cursor": "c2"},
        {"reviews": [_raw(2, 2025, 1, 1)], "cursor": "c3"},
        {"reviews": [_raw(3, 2024, 12, 1)], "cursor": "c4"},
    ]
    pager = _pager(pages)

    reviews = steam_fetch.fetch_reviews(
        123, since=datetime(2025, 5, 1, tzinfo=timezone.utc), page_fetcher=pager
    )

    assert [r["recommendationid"] for r in reviews] == ["1"]
    assert pager.calls["count"] == 2, "should not have paged past the first out-of-window page"


def test_window_for_launch_brackets_the_launch_date():
    since, until = steam_fetch.window_for_launch("2025-03-20")

    assert (datetime(2025, 3, 20, tzinfo=timezone.utc) - since).days == config.PRE_LAUNCH_DAYS
    assert (until - datetime(2025, 3, 20, tzinfo=timezone.utc)).days == config.POST_LAUNCH_DAYS


def test_weekly_volumes_buckets_by_iso_week_with_positive_share():
    reviews = [
        steam_fetch.parse_review(_raw(1, 2025, 5, 5, voted_up=True)),
        steam_fetch.parse_review(_raw(2, 2025, 5, 6, voted_up=False)),
        steam_fetch.parse_review(_raw(3, 2025, 5, 13, voted_up=False)),
    ]

    rows = steam_fetch.weekly_volumes(reviews)

    assert [r["week"] for r in rows] == ["2025-W19", "2025-W20"]
    assert rows[0]["reviews"] == 2
    assert rows[0]["positive_share"] == pytest.approx(0.5)
    assert rows[1]["positive_share"] == pytest.approx(0.0)


def test_fetch_reviews_passes_the_window_to_the_endpoint_as_epochs():
    """Steam seeks to the window itself; without this the pull pages back from today."""
    captured = {}

    def fetch(appid, cursor="*", session=None, start_date=None, end_date=None):
        captured["start_date"] = start_date
        captured["end_date"] = end_date
        return {"reviews": [], "cursor": None}

    since = datetime(2024, 1, 25, tzinfo=timezone.utc)
    until = datetime(2024, 8, 8, tzinfo=timezone.utc)
    steam_fetch.fetch_reviews(553850, since=since, until=until, page_fetcher=fetch)

    assert captured["start_date"] == int(since.timestamp())
    assert captured["end_date"] == int(until.timestamp())


def test_fetch_reviews_sends_no_date_bounds_when_the_window_is_open():
    captured = {}

    def fetch(appid, cursor="*", session=None, start_date=None, end_date=None):
        captured["start_date"] = start_date
        return {"reviews": [], "cursor": None}

    steam_fetch.fetch_reviews(553850, page_fetcher=fetch)

    assert captured["start_date"] is None


def test_plan_chunks_leaves_a_small_window_whole():
    counts = lambda appid, since, until: 1_000

    chunks = steam_fetch.plan_chunks(1, datetime(2024, 1, 1, tzinfo=timezone.utc),
                                     datetime(2024, 6, 1, tzinfo=timezone.utc), counter=counts)

    assert len(chunks) == 1


def test_plan_chunks_bisects_until_every_chunk_is_paginable():
    """Deep cursor pagination silently truncates; no chunk may exceed the safe size."""
    window_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    window_end = datetime(2024, 2, 1, tzinfo=timezone.utc)
    total = 320_000

    def counts(appid, since, until):
        # Uniform density, so a count is proportional to the span.
        span = (until - since) / (window_end - window_start)
        return int(total * span)

    chunks = steam_fetch.plan_chunks(1, window_start, window_end, counter=counts)

    assert len(chunks) > 1
    assert all(expected <= config.SAFE_CHUNK_REVIEWS for _, _, expected in chunks)
    # Chunks must tile the window with no gaps.
    assert chunks[0][0] == window_start
    assert chunks[-1][1] == window_end
    for earlier, later in zip(chunks, chunks[1:]):
        assert earlier[1] == later[0]


def test_plan_chunks_splits_a_dense_period_more_finely_than_a_quiet_one():
    window_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    spike_start = datetime(2024, 1, 16, tzinfo=timezone.utc)
    window_end = datetime(2024, 2, 1, tzinfo=timezone.utc)

    def counts(appid, since, until):
        # Everything is in the back half of the window.
        overlap_start = max(since, spike_start)
        if overlap_start >= until:
            return 100
        return int(200_000 * ((until - overlap_start) / (window_end - spike_start)))

    chunks = steam_fetch.plan_chunks(1, window_start, window_end, counter=counts)
    quiet = [c for c in chunks if c[1] <= spike_start]
    dense = [c for c in chunks if c[0] >= spike_start]

    assert len(dense) > len(quiet)


def test_fetch_window_chunked_deduplicates_across_chunk_boundaries():
    """Adjacent chunks share a boundary instant, so the same review can appear twice."""
    boundary = _raw(99, 2024, 1, 16)

    def counts(appid, since, until):
        return 100_000 if (until - since).days > 20 else 10

    def pager(appid, cursor="*", session=None, start_date=None, end_date=None):
        if cursor == "*":
            return {"reviews": [boundary], "cursor": "c2"}
        return {"reviews": [], "cursor": None}

    reviews, coverage = steam_fetch.fetch_window_chunked(
        1,
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 2, 1, tzinfo=timezone.utc),
        page_fetcher=pager,
        counter=counts,
    )

    assert len(coverage) > 1, "window should have been split"
    assert len(reviews) == 1, "the boundary review must not be counted twice"
    assert sum(row["new"] for row in coverage) == 1


def _many_chunk_setup():
    """A window that bisects into several chunks, each serving one identifiable review."""
    window_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    window_end = datetime(2024, 2, 1, tzinfo=timezone.utc)

    def counts(appid, since, until):
        span = (until - since) / (window_end - window_start)
        return int(320_000 * span)

    def pager(appid, cursor="*", session=None, start_date=None, end_date=None):
        if cursor != "*":
            return {"reviews": [], "cursor": None}
        # One review per chunk, timestamped just inside that chunk so the window
        # filter keeps it, and identified by the chunk it came from.
        review = _raw(start_date, 2024, 1, 15)
        review["timestamp_created"] = start_date + 1
        review["timestamp_updated"] = start_date + 1
        return {"reviews": [review], "cursor": "c2"}

    return window_start, window_end, counts, pager


def test_concurrent_and_sequential_pulls_return_identical_corpora():
    """Merging by chunk order, not completion order, is what makes the pull reproducible."""
    start, end, counts, pager = _many_chunk_setup()

    serial, serial_cov = steam_fetch.fetch_window_chunked(
        1, start, end, page_fetcher=pager, counter=counts, max_workers=1
    )
    parallel, parallel_cov = steam_fetch.fetch_window_chunked(
        1, start, end, page_fetcher=pager, counter=counts, max_workers=8
    )

    assert len(serial) > 1, "window should have split into several chunks"
    assert [r["recommendationid"] for r in serial] == [r["recommendationid"] for r in parallel]
    assert [c["chunk"] for c in parallel_cov] == sorted(c["chunk"] for c in parallel_cov)
    assert [c["fetched"] for c in serial_cov] == [c["fetched"] for c in parallel_cov]


def test_concurrent_pull_reports_every_chunk_exactly_once():
    start, end, counts, pager = _many_chunk_setup()
    seen = []
    guard = __import__("threading").Lock()

    def on_chunk(row):
        with guard:
            seen.append(row["chunk"])

    _, coverage = steam_fetch.fetch_window_chunked(
        1, start, end, page_fetcher=pager, counter=counts, on_chunk=on_chunk, max_workers=8
    )

    assert sorted(seen) == sorted(c["chunk"] for c in coverage)
    assert len(seen) == len(set(seen)), "a chunk was reported twice"


def test_cache_path_separates_identical_cursors_under_different_windows():
    """A cursor means different things under different date bounds — same key would poison the cache."""
    same_cursor = "AoJw+7Xz1PYCf7ay1g4=="

    a = steam_fetch._cache_path(553850, same_cursor, 1704067200, 1717200000)
    b = steam_fetch._cache_path(553850, same_cursor, 1717200000, 1730000000)
    unbounded = steam_fetch._cache_path(553850, same_cursor)

    assert len({a, b, unbounded}) == 3


def test_cache_path_is_filesystem_safe_and_cursor_specific():
    cursor = "AoJw+7Xz1PYCf7ay1g4=="

    path = steam_fetch._cache_path(1091500, cursor)
    other = steam_fetch._cache_path(1091500, "AoJw+different==")

    assert path != other
    assert all(char not in path.name for char in '+=/\\:*?"<>|')


def test_fetch_page_reads_from_cache_without_making_a_request(tmp_path, monkeypatch):
    """The re-run guarantee: a cached pull returns identical data and no network call."""
    monkeypatch.setattr(config, "STEAM_CACHE_DIR", tmp_path)
    payload = {"success": 1, "reviews": [_raw(1, 2025, 5, 3)], "cursor": "next"}
    cached = steam_fetch._cache_path(42, "*")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(__import__("json").dumps(payload), encoding="utf-8")

    def explode(*args, **kwargs):
        raise AssertionError("cache hit should not make a request")

    monkeypatch.setattr(steam_fetch, "_http_get", explode)

    assert steam_fetch.fetch_page(42, "*") == payload
