"""Template helpers for the Data@Spark theme."""

import logging
import time
from datetime import datetime

from ckan.plugins import toolkit

from ckanext.spark.topics import SPARK_TOPICS

log = logging.getLogger(__name__)

# How long a topic count may be stale. Topics are created by hand and datasets
# are added in batches, so a homepage tile reading one dataset behind for a
# minute costs nothing; taking Solr off the per-request path is worth much more.
TOPIC_COUNT_TTL_SECONDS = 60

# (fetched_at_monotonic, {group_name: count}). Module-level, so each uWSGI
# worker keeps its own copy -- with a handful of workers that is still at most a
# few queries per TTL instead of one per request. Deliberately not Redis: a
# shared cache would be another moving part and another thing that can be down,
# for a value this cheap to recompute. Assignment of the whole tuple is atomic
# under the GIL, so a concurrent refresh costs a duplicate query, never a torn
# read.
_topic_counts_cache = (None, {})


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


def _refresh_topic_counts():
    """Ask Solr how many datasets sit in each group. One query, no dataset bodies."""
    result = toolkit.get_action("package_search")(
        {},
        {
            "rows": 0,
            "facet.field": ["groups"],
            # Measured at 304 datasets: identical to facet.limit=50 (27.8ms vs
            # 26.6ms median), because the cost is bounded by the number of
            # groups, not the number of datasets. Pinning -1 means the homepage
            # can't silently start dropping the least-used topics if
            # `search.facets.limit` is lowered or the taxonomy outgrows it.
            "facet.limit": -1,
        },
    )
    # Missing on a brand-new site with an empty index.
    items = result.get("search_facets", {}).get("groups", {}).get("items", [])
    return {item["name"]: item["count"] for item in items}


def topic_counts():
    """Group-name -> dataset count, cached for TOPIC_COUNT_TTL_SECONDS.

    See ckanext-spark#7: an uncached version of this query ran on every homepage
    load and coincided with the int container going unhealthy. Root cause was
    never confirmed, and local measurement at 304 datasets puts this query at
    27.8ms median -- indistinguishable from the three `package_search` calls the
    homepage already made (25-27ms each). So this cache is not a proven fix for
    that incident; it removes the query from the hot path so it cannot be the
    cause of the next one, and that is all it claims.

    A failed refresh serves the previous counts rather than raising. Solr being
    slow or down should degrade the homepage's topic tiles to stale-or-zero, not
    500 the whole page -- which is the failure mode #7 actually cared about.
    """
    global _topic_counts_cache
    fetched_at, counts = _topic_counts_cache
    now = time.monotonic()

    if fetched_at is not None and now - fetched_at < TOPIC_COUNT_TTL_SECONDS:
        return counts

    try:
        counts = _refresh_topic_counts()
    except Exception:
        # Keep serving the last good counts (or {} on the very first call) and
        # back off for a full TTL so a struggling Solr isn't retried per request.
        log.warning("Topic count refresh failed; serving stale counts", exc_info=True)

    _topic_counts_cache = (now, counts)
    return counts


def topics():
    """Return the canonical topic taxonomy, each with its dataset count.

    Always returns all of SPARK_TOPICS in taxonomy order, including topics with
    no datasets yet -- the point of a fixed taxonomy is that the shape of it is
    visible before it's full. Counts are cached; see topic_counts().
    """
    counts = topic_counts()
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
