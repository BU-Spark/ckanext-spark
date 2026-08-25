"""Template helpers for the Data@Spark theme."""

import logging
import time
from datetime import datetime

from ckan.plugins import toolkit

from ckanext.spark.topics import SPARK_TOPICS

log = logging.getLogger(__name__)

# How long homepage search results may be stale. Everything cached here is a
# "what's here lately" summary, so a tile reading a minute behind costs nothing;
# taking Solr off the per-request path is worth much more.
HOMEPAGE_CACHE_TTL_SECONDS = 60

# Back-compat alias: the topic-count TTL was named separately before the other
# three homepage searches were cached too.
TOPIC_COUNT_TTL_SECONDS = HOMEPAGE_CACHE_TTL_SECONDS

# key -> (fetched_at_monotonic, value). Module-level, so each uWSGI worker keeps
# its own copy: a few queries per TTL instead of one per request. Deliberately
# not Redis -- a shared cache is another moving part that can itself be down, for
# values this cheap to recompute. Assigning a whole tuple is atomic under the
# GIL, so a concurrent refresh costs a duplicate query, never a torn read.
_cache: dict = {}


def _is_anonymous():
    """True only if we're certain no user is logged in.

    This gates every cache read and write, because `package_search` filters on
    permission labels derived from the requesting user (see CKAN's
    logic/action/get.py, "enforce permission filter based on user"): a sysadmin
    gets `labels = None` and sees private datasets. Caching one user's results
    under a shared key would serve their private dataset titles to the next
    visitor.

    Fails CLOSED. Anything unexpected -- no request context (CLI, tests,
    background jobs), a CKAN version that moves `current_user` -- returns False,
    which bypasses the cache and costs a query. The opposite default would leak.
    """
    try:
        user = toolkit.current_user
    except Exception:
        return False
    if user is None:
        return False
    try:
        return bool(user.is_anonymous)
    except Exception:
        return False


def _cached(key, refresh, default):
    """Return `refresh()`'s value, memoised per worker for the TTL.

    Logged-in (or unknown) users always get a live call, so their view is never
    cached and never served from someone else's.

    A failed refresh serves the previous value and still resets the timer, so a
    struggling Solr is retried once per TTL rather than once per request. Solr
    being slow should degrade the homepage's tiles, not 500 the page.
    """
    if not _is_anonymous():
        return refresh()

    entry = _cache.get(key)
    now = time.monotonic()
    if entry is not None and now - entry[0] < HOMEPAGE_CACHE_TTL_SECONDS:
        return entry[1]

    value = entry[1] if entry is not None else default
    try:
        value = refresh()
    except Exception:
        log.warning("Homepage cache refresh failed for %s; serving stale", key,
                    exc_info=True)

    _cache[key] = (now, value)
    return value


def _datasets(**params):
    """Return dataset search results without per-dataset API calls."""
    search_params = {"rows": 6}
    search_params.update(params)
    result = toolkit.get_action("package_search")({}, search_params)
    return result["results"]


def all_datasets():
    return _cached(
        "all_datasets",
        lambda: _datasets(sort="metadata_modified desc"),
        [],
    )


def featured_datasets():
    return _cached(
        "featured_datasets",
        lambda: _datasets(fq="tags:featured", sort="metadata_modified desc"),
        [],
    )


def popular_datasets():
    return _cached(
        "popular_datasets",
        lambda: _datasets(sort="views_recent desc"),
        [],
    )


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
    """Group name -> dataset count, cached like the other homepage searches.

    See ckanext-spark#7: an uncached version of this ran on every homepage load
    and coincided with the int container going unhealthy. Measured at 304
    datasets it is 27.8ms -- indistinguishable from the three `package_search`
    calls the homepage already made -- so this cache is not a proven fix for that
    incident. It removes the query from the hot path so it cannot cause the next
    one, and that is all it claims.
    """
    return _cached("topic_counts", _refresh_topic_counts, {})


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
