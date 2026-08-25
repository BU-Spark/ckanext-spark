"""Template helpers for the Data@Spark theme."""

from datetime import datetime

from ckan.plugins import toolkit

from ckanext.spark.topics import SPARK_TOPICS


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


def topics():
    """Return the canonical topic taxonomy, each with its live dataset count.

    The live count is temporarily disabled -- see ckanext-spark#7. The
    `package_search` facet query this used to run on every homepage load (with
    no caching) coincided with the CKAN container becoming unhealthy and its
    uWSGI workers thrashing on int within about a minute of deploy, under only
    a single visitor's traffic. Root cause wasn't confirmed before rollback,
    but this is the one thing this PR added to every homepage request, so it's
    the first suspect to remove. Always returns all of SPARK_TOPICS in
    taxonomy order with count 0 until #7 restores this with a fix (caching, a
    cheaper query, or confirmation this wasn't actually the cause).
    """
    return [{"name": name, "title": title, "count": 0} for name, title in SPARK_TOPICS]


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
        "spark_topics": topics,
        "spark_format_date": format_date,
    }
