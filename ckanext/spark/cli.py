import click
from ckan.plugins import toolkit

from ckanext.spark.topics import SPARK_TOPICS


@click.group(short_help="spark CLI.")
def spark():
    """spark CLI."""
    pass


def _sysadmin_context():
    """An action context allowed to create groups.

    Seeding runs from the command line with no logged-in user, so it borrows the
    site user rather than requiring an operator to pass credentials.
    """
    site_user = toolkit.get_action("get_site_user")({"ignore_auth": True}, {})
    return {"user": site_user["name"], "ignore_auth": True}


@spark.command()
def init_topics():
    """Create (or repair) the Data@Spark topic groups.

    Safe to re-run: existing topics keep any description and image an editor has
    since added, and only a wrong title or a soft-deleted state is corrected.
    """
    context = _sysadmin_context()

    for name, title in SPARK_TOPICS:
        try:
            existing = toolkit.get_action("group_show")(
                dict(context), {"id": name, "include_datasets": False}
            )
        except toolkit.ObjectNotFound:
            toolkit.get_action("group_create")(
                dict(context), {"name": name, "title": title}
            )
            click.echo(f"created  {name}")
            continue

        # Only touch what's actually wrong. A topic soft-deleted through the UI
        # still occupies its name, so reviving it is the only way a re-run can
        # restore the full taxonomy.
        patch = {}
        if existing.get("title") != title:
            patch["title"] = title
        if existing.get("state") != "active":
            patch["state"] = "active"

        if patch:
            toolkit.get_action("group_patch")(dict(context), {"id": name, **patch})
            click.echo(f"repaired {name} ({', '.join(patch)})")
        else:
            click.echo(f"ok       {name}")


def get_commands():
    return [spark]
