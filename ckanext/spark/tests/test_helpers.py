"""Tests for Data@Spark template helpers."""

import ckanext.spark.helpers as helpers


def test_spark_hello():
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


def test_groups_accepts_an_optional_limit(monkeypatch):
    calls = []

    def group_list(context, data_dict):
        calls.append((context, data_dict))
        return []

    monkeypatch.setattr(helpers.toolkit, "get_action", lambda action: group_list)

    assert helpers.groups(limit=6) == []
    assert calls == [({}, {"all_fields": True, "limit": 6})]
