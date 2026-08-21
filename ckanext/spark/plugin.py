import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.spark import cli, helpers


class SparkPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IClick)

    def get_helpers(self):
        return helpers.get_helpers()

    def get_commands(self):
        return cli.get_commands()

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "spark")
