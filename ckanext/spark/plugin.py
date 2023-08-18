import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
from ckan.model import Package
import dateutil.parser  # Import the necessary library
from datetime import datetime

# import ckanext.spark.cli as cli
# import ckanext.spark.helpers as helpers
# import ckanext.spark.views as views
# from ckanext.spark.logic import (
#     action, auth, validators
# )

def all_packages():
    packages = toolkit.get_action('package_list')({}, {})
    packages = packages[:6]
    dataset_objects = []
    
    for package_name in packages:
        dataset = toolkit.get_action('package_show')({}, {'id': package_name})
        metadata_modified = dateutil.parser.parse(dataset['metadata_modified'])
        formatted_date = metadata_modified.strftime("%d, %B, %Y")
        dataset['formatted_date'] = formatted_date

        dataset_objects.append(dataset)
    
    return dataset_objects
 
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
        'sort': 'views_recent desc',  #TODO: enable views in ckan app
    }
    result = toolkit.get_action('package_search')({}, search_params)
    return result

def all_groups():
    '''Return a sorted list of the all groups'''
    groups = toolkit.get_action('group_list')(
        {}, {})
    return groups

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
            'spark_popular_datasets': popular_datasets,
            'spark_groups': all_groups
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
    

