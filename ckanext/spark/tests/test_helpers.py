"""Tests for Data@Spark template helpers."""

import re

import pytest

import ckanext.spark.helpers as helpers
import ckanext.spark.topics as topics


def test_format_date_formats_iso_timestamp():
    assert helpers.format_date("2026-07-23T13:14:15.000000") == "July 23, 2026"


def test_all_datasets_uses_single_search_action(monkeypatch):
    calls = []

    def package_search(context, data_dict):
        calls.append((context, data_dict))
        return {"results": [{"name": "example"}]}

    monkeypatch.setattr(
        helpers.toolkit,
        "get_action",
        lambda action: package_search if action == "package_search" else None,
    )

    assert helpers.all_datasets() == [{"name": "example"}]
    assert calls == [({}, {"rows": 6, "sort": "metadata_modified desc"})]


def test_featured_datasets_filters_featured_tag(monkeypatch):
    calls = []

    def package_search(context, data_dict):
        calls.append((context, data_dict))
        return {"results": []}

    monkeypatch.setattr(helpers.toolkit, "get_action", lambda action: package_search)

    assert helpers.featured_datasets() == []
    assert calls == [
        (
            {},
            {
                "rows": 6,
                "fq": "tags:featured",
                "sort": "metadata_modified desc",
            },
        )
    ]


@pytest.fixture(autouse=True)
def _clear_topic_cache():
    """Empty the module-level topic-count cache around every test.

    Without this, whichever topic test ran first would populate the cache and
    every later one would silently assert against its counts instead of its own.
    """
    helpers._topic_counts_cache = (None, {})
    yield
    helpers._topic_counts_cache = (None, {})


def _stub_topic_search(monkeypatch, facet_items, calls=None):
    """Point package_search at a canned `groups` facet response."""

    def package_search(context, data_dict):
        if calls is not None:
            calls.append((context, data_dict))
        return {
            "count": 0,
            "results": [],
            "search_facets": {"groups": {"items": facet_items}},
        }

    monkeypatch.setattr(helpers.toolkit, "get_action", lambda action: package_search)


def test_topics_returns_the_whole_taxonomy_in_order(monkeypatch):
    _stub_topic_search(monkeypatch, [])

    result = helpers.topics()

    assert [topic["name"] for topic in result] == [
        name for name, _title in topics.SPARK_TOPICS
    ]
    # A topic with no datasets still appears -- the taxonomy is the point, not
    # just the datasets currently in it.
    assert all(topic["count"] == 0 for topic in result)


def test_topics_merges_facet_counts_by_group_name(monkeypatch):
    _stub_topic_search(
        monkeypatch,
        [
            {"name": "education-learning", "count": 4},
            {"name": "law-civil-rights", "count": 1},
            # A group that isn't part of the taxonomy must not leak in.
            {"name": "some-other-group", "count": 9},
        ],
    )

    counts = {topic["name"]: topic["count"] for topic in helpers.topics()}

    assert counts["education-learning"] == 4
    assert counts["law-civil-rights"] == 1
    assert counts["housing-urban-development"] == 0
    assert "some-other-group" not in counts


def test_topics_pins_the_facet_limit(monkeypatch):
    """The count query must not inherit a facet cap from site config.

    CKAN takes facet.limit from `search.facets.limit` (default 50), so all 11
    topics come back today. Pinning -1 keeps that true if the config is lowered
    or the taxonomy outgrows it, instead of quietly dropping the rarest topics.
    """
    calls = []
    _stub_topic_search(monkeypatch, [], calls)

    helpers.topics()

    (_context, data_dict), = calls
    assert data_dict["facet.limit"] == -1
    assert data_dict["rows"] == 0


def test_topics_survives_an_empty_search_index(monkeypatch):
    """A fresh site returns no search_facets key at all."""

    monkeypatch.setattr(
        helpers.toolkit,
        "get_action",
        lambda action: lambda context, data_dict: {"count": 0, "results": []},
    )

    assert len(helpers.topics()) == len(topics.SPARK_TOPICS)


def test_topic_counts_are_cached_within_the_ttl(monkeypatch):
    """The whole point of ckanext-spark#7: not one Solr query per homepage load."""
    calls = []
    _stub_topic_search(monkeypatch, [{"name": "education-learning", "count": 4}], calls)

    for _ in range(25):
        helpers.topics()

    assert len(calls) == 1


def test_topic_counts_refresh_after_the_ttl_expires(monkeypatch):
    calls = []
    _stub_topic_search(monkeypatch, [{"name": "education-learning", "count": 4}], calls)

    helpers.topics()
    # Jump past the TTL rather than sleeping through it.
    fetched_at, counts = helpers._topic_counts_cache
    helpers._topic_counts_cache = (
        fetched_at - helpers.TOPIC_COUNT_TTL_SECONDS - 1,
        counts,
    )
    helpers.topics()

    assert len(calls) == 2


def test_topic_counts_serve_stale_values_when_the_refresh_fails(monkeypatch):
    """A struggling Solr must degrade the tiles, not 500 the homepage."""
    _stub_topic_search(monkeypatch, [{"name": "education-learning", "count": 4}])
    helpers.topics()

    def explode(action):
        def _boom(context, data_dict):
            raise RuntimeError("solr is having a moment")

        return _boom

    monkeypatch.setattr(helpers.toolkit, "get_action", explode)
    fetched_at, counts = helpers._topic_counts_cache
    helpers._topic_counts_cache = (
        fetched_at - helpers.TOPIC_COUNT_TTL_SECONDS - 1,
        counts,
    )

    result = {t["name"]: t["count"] for t in helpers.topics()}

    assert result["education-learning"] == 4, "should still serve the last good count"


def test_topic_counts_return_zeros_when_the_first_ever_refresh_fails(monkeypatch):
    """Cold cache plus a broken Solr still has to render a page."""

    def explode(action):
        def _boom(context, data_dict):
            raise RuntimeError("solr is down")

        return _boom

    monkeypatch.setattr(helpers.toolkit, "get_action", explode)

    result = helpers.topics()

    assert len(result) == len(topics.SPARK_TOPICS)
    assert all(topic["count"] == 0 for topic in result)


def test_failed_refresh_backs_off_instead_of_retrying_every_request(monkeypatch):
    """Retrying a broken Solr once per request is how a blip becomes an outage."""
    calls = []

    def explode(action):
        def _boom(context, data_dict):
            calls.append(1)
            raise RuntimeError("solr is down")

        return _boom

    monkeypatch.setattr(helpers.toolkit, "get_action", explode)

    for _ in range(25):
        helpers.topics()

    assert len(calls) == 1


def test_topic_names_are_unique_and_url_safe():
    names = [name for name, _title in topics.SPARK_TOPICS]

    assert len(names) == len(set(names)), "a duplicate name would collide in CKAN"
    for name in names:
        # CKAN group names: lowercase alphanumerics, - and _, at least 2 chars.
        assert re.fullmatch(r"[a-z0-9_-]{2,100}", name), name
