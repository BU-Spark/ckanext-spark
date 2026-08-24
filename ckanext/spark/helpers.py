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

    Always returns all of SPARK_TOPICS in taxonomy order, including topics with
    no datasets yet -- the point of a fixed taxonomy is that the shape of it is
    visible before it's full. Counts come from one faceted search rather than a
    query per topic.
    """
    result = toolkit.get_action("package_search")(
        {},
        {
            "rows": 0,
            "facet.field": ["groups"],
            # Defensive, not a bugfix: CKAN feeds facet.limit from
            # `search.facets.limit`, which defaults to 50, so the 11 topics fit
            # today. Pinning -1 means the homepage can't start silently dropping
            # the least-used topics if someone lowers that config, or if the
            # taxonomy grows past it. (The other CKAN setting,
            # `search.facets.default` = 10, is a UI display cap and never
            # reaches this query.)
            "facet.limit": -1,
        },
    )
    # Missing on a brand-new site with an empty index.
    counts = result.get("search_facets", {}).get("groups", {}).get("items", [])
    counts = {item["name"]: item["count"] for item in counts}

    return [
        {"name": name, "title": title, "count": counts.get(name, 0)}
        for name, title in SPARK_TOPICS
    ]


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
