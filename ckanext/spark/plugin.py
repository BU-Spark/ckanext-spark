import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
from ckan.model import Package

# import ckanext.spark.cli as cli
# import ckanext.spark.helpers as helpers
# import ckanext.spark.views as views
# from ckanext.spark.logic import (
#     action, auth, validators
# )

def all_packages():
    packages = toolkit.get_action('package_list')({},{})
    return packages

def featured_datasets():
    search_params = {
       'q': 'tags:featured',  # Filter by the "featured" tag
       'start': 0,
    }
    result = toolkit.get_action('package_search')(search_params)
    return result

def popular_datasets():
    '''Return a list of the most popular datasets by recent view count.'''
    search_params = {
        'sort': 'views_recent desc',  # Sort by recent view count in descending order
        'start': 0,
    }
    result = toolkit.get_action('package_search')({}, search_params)

    return result

class SparkPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # plugins.implements(plugins.IAuthFunctions)
    # plugins.implements(plugins.IActions)
    # plugins.implements(plugins.IBlueprint)
    # plugins.implements(plugins.IClick)
    # plugins.implements(plugins.ITemplateHelpers)
    # plugins.implements(plugins.IValidators)

    # IConfigurer
    def get_helpers(self):
        return {
            'spark_all_packages': all_packages,
            'spark_featured_datasets': featured_datasets,
            'spark_popular_datasets': popular_datasets 
        }

    def update_config(self, config_):
        toolkit.add_template_directory(config_, "templates")
        toolkit.add_public_directory(config_, "public")
        toolkit.add_resource("assets", "spark")


    # IAuthFunctions

    # def get_auth_functions(self):
    #     return auth.get_auth_functions()

    # IActions

    # def get_actions(self):
    #     return action.get_actions()

    # IBlueprint

    # def get_blueprint(self):
    #     return views.get_blueprints()

    # IClick

    # def get_commands(self):
    #     return cli.get_commands()

    # ITemplateHelpers

    # def get_helpers(self):
    #     return helpers.get_helpers()

    # IValidators

    # def get_validators(self):
    #     return validators.get_validators()
    

