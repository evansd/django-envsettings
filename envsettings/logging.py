import copy

from django.utils.log import DEFAULT_LOGGING

from .base import EnvSettings


def modify_django_config(config):
    # Copy the config so we can mutate it
    config = copy.deepcopy(config)
    # Remove filters to allow console handler to work without DEBUG
    config['handlers']['console']['filters'] = []
    # Allow `request` and `security` logs to propagate up to the
    # root handler
    config['loggers']['django.request']['propagate'] = True
    try:
        config['loggers']['django.security']['propagate'] = True
    except KeyError:
        # Older version of Django lack this logger
        pass
    return config


class LoggingSettings(EnvSettings):

    # Our default config is a slightly modified version of the Django
    # default
    CONFIG = modify_django_config(DEFAULT_LOGGING)
    LOG_LEVEL_KEY = ('handlers', 'console', 'level')

    def __init__(self, *args, **kwargs):
        super(LoggingSettings, self).__init__(*args, **kwargs)
        self.CONFIG = copy.deepcopy(self.CONFIG)

    def get(self, key, default='INFO'):
        """
        Return a copy of the logging config with the `LOG_LEVEL_KEY` set to the
        supplied level
        """
        level = self.env.get(key, default)
        config = copy.deepcopy(self.CONFIG)
        self.set_nested_key(config, self.LOG_LEVEL_KEY, level)
        return config

    @staticmethod
    def set_nested_key(dictionary, keys, value):
        for key in keys[:-1]:
            dictionary = dictionary[key]
        dictionary[keys[-1]] = value
