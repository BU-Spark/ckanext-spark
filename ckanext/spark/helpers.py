"""Template helpers for the Data@Spark theme."""

from datetime import datetime

from ckan.plugins import toolkit


def _datasets(**params):
    """Return dataset search results without per-dataset API calls."""
    search_params = {"rows": 6}
    search_params.update(params)
    result = toolkit.get_action("package_search")({}, search_params)
    return result["results"]


def all_datasets():
    return _datasets(sort="metadata_modified desc")


def featured_datasets():
    return _datasets(fq="tags:featured", sort="metadata_modified desc")


def popular_datasets():
    return _datasets(sort="views_recent desc")


def groups():
    return toolkit.get_action("group_list")({}, {"all_fields": True})


def format_date(value):
    """Format CKAN's ISO timestamp for compact display."""
    if not value:
        return ""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return f"{parsed:%B} {parsed.day}, {parsed.year}"


def get_helpers():
    return {
        "spark_all_datasets": all_datasets,
        "spark_featured_datasets": featured_datasets,
        "spark_popular_datasets": popular_datasets,
        "spark_groups": groups,
        "spark_format_date": format_date,
    }
