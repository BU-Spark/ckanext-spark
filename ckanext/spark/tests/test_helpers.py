"""Tests for Data@Spark template helpers."""

import re

import pytest

import ckanext.spark.helpers as helpers
import ckanext.spark.topics as topics

# Captured before the autouse fixture stubs it out, so the tests below can
# exercise the real gate rather than the stub.
_REAL_IS_ANONYMOUS = helpers._is_anonymous


@pytest.fixture(autouse=True)
def _anonymous_with_empty_cache(monkeypatch):
    """Every test starts anonymous with an empty cache.

    Two separate hazards, both of which produce tests that pass for the wrong
    reason: a populated cache means later tests assert against an earlier
    test's values, and outside a request context `_is_anonymous()` fails closed,
    so the cache would never engage and the caching tests would be vacuous.
    """
    helpers._cache.clear()
    monkeypatch.setattr(helpers, "_is_anonymous", lambda: True)
    yield
    helpers._cache.clear()

def _age_out(key):
    """Push a cache entry past its TTL instead of sleeping through it."""
    fetched_at, value = helpers._cache[key]
    helpers._cache[key] = (fetched_at - helpers.HOMEPAGE_CACHE_TTL_SECONDS - 1, value)


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

    # Second call inside the TTL is served from cache, not Solr.
    assert helpers.all_datasets() == [{"name": "example"}]
    assert len(calls) == 1


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
    _age_out("topic_counts")
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
    _age_out("topic_counts")

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


def test_every_homepage_search_is_cached(monkeypatch):
    """All four homepage searches, not just the topic counts (see #7 discussion).

    A warm homepage should make zero Solr calls. Previously it made four.
    """
    calls = []

    def package_search(context, data_dict):
        calls.append(data_dict)
        return {
            "results": [],
            "search_facets": {"groups": {"items": []}},
        }

    monkeypatch.setattr(helpers.toolkit, "get_action", lambda action: package_search)

    def render_homepage():
        helpers.all_datasets()
        helpers.popular_datasets()
        helpers.featured_datasets()
        helpers.topics()

    render_homepage()
    assert len(calls) == 4, "cold cache should do exactly one query per helper"

    calls.clear()
    for _ in range(10):
        render_homepage()
    assert calls == [], "a warm homepage must not touch Solr at all"


def test_logged_in_users_never_read_or_write_the_cache(monkeypatch):
    """The privacy gate.

    `package_search` filters on permission labels derived from the user, and a
    sysadmin gets no filter at all -- so caching their results under a shared key
    would serve private dataset titles to the next anonymous visitor. Logged-in
    users must always go live, and must never populate the shared cache.
    """
    monkeypatch.setattr(helpers, "_is_anonymous", lambda: False)
    calls = []

    def package_search(context, data_dict):
        calls.append(data_dict)
        return {"results": [{"name": "a-private-dataset"}]}

    monkeypatch.setattr(helpers.toolkit, "get_action", lambda action: package_search)

    for _ in range(5):
        helpers.all_datasets()

    assert len(calls) == 5, "a logged-in user must always get a live query"
    assert helpers._cache == {}, "a logged-in user must not populate the cache"


def test_is_anonymous_fails_closed_without_a_request_context(monkeypatch):
    """Outside a request there is no user to check, so caching must not engage.

    Fail-closed is the whole point: the wrong default here leaks one user's
    results to another.
    """

    monkeypatch.delattr(helpers.toolkit, "current_user", raising=False)

    assert _REAL_IS_ANONYMOUS() is False


def test_is_anonymous_is_false_for_a_logged_in_user(monkeypatch):
    monkeypatch.setattr(
        helpers.toolkit, "current_user", type("U", (), {"is_anonymous": False})()
    )
    assert _REAL_IS_ANONYMOUS() is False


def test_is_anonymous_is_true_for_an_anonymous_visitor(monkeypatch):
    monkeypatch.setattr(
        helpers.toolkit, "current_user", type("U", (), {"is_anonymous": True})()
    )
    assert _REAL_IS_ANONYMOUS() is True
