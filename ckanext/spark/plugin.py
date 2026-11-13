import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.spark import cli, helpers


def topics_first(facets_dict):
    """Call CKAN's `groups` facet "Topics" and list it first.

    Topics are modelled as CKAN groups (see topics.py), so the stock facet
    reads "Groups" and sits second, behind Organizations. The topic is the main
    way into the catalog, as the discipline is in Atlas, so it leads the sidebar.
    """
    if "groups" not in facets_dict:
        return facets_dict
    reordered = {"groups": toolkit._("Topics")}
    reordered.update((k, v) for k, v in facets_dict.items() if k != "groups")
    return reordered


class SparkPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IFacets, inherit=True)

    def get_helpers(self):
        return helpers.get_helpers()

    def get_commands(self):
        return cli.get_commands()

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")

    def dataset_facets(self, facets_dict, package_type):
        return topics_first(facets_dict)

    def group_facets(self, facets_dict, group_type, package_type):
        return topics_first(facets_dict)

    def organization_facets(self, facets_dict, organization_type, package_type):
        return topics_first(facets_dict)
