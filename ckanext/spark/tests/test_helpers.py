"""Tests for Data@Spark template helpers."""

import re

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


def test_topics_returns_the_whole_taxonomy_in_order():
    result = helpers.topics()

    assert [topic["name"] for topic in result] == [
        name for name, _title in topics.SPARK_TOPICS
    ]
    # A topic with no datasets still appears -- the taxonomy is the point, not
    # just the datasets currently in it.
    assert all(topic["title"] for topic in result)


def test_topics_live_count_is_temporarily_disabled(monkeypatch):
    """See ckanext-spark#7.

    The `package_search` facet query this used to run on every homepage load
    coincided with int becoming unhealthy shortly after this shipped. Root
    cause wasn't confirmed, but this was the one thing added to every
    homepage request, so it's disabled pending investigation. This test pins
    that: topics() must not touch package_search at all right now, and every
    count must read 0. Update/remove this once #7 restores a fix.
    """

    def fail(*_args, **_kwargs):
        raise AssertionError("topics() must not call get_action while disabled")

    monkeypatch.setattr(helpers.toolkit, "get_action", fail)

    result = helpers.topics()

    assert all(topic["count"] == 0 for topic in result)


def test_topic_names_are_unique_and_url_safe():
    names = [name for name, _title in topics.SPARK_TOPICS]

    assert len(names) == len(set(names)), "a duplicate name would collide in CKAN"
    for name in names:
        # CKAN group names: lowercase alphanumerics, - and _, at least 2 chars.
        assert re.fullmatch(r"[a-z0-9_-]{2,100}", name), name
