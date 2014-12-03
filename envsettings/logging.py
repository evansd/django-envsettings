import copy

from django.utils.log import DEFAULT_LOGGING

from .base import EnvSettings


class LoggingSettings(EnvSettings):

    def get(self, keys=(), default='INFO'):
        return self._get(keys, convert=self.parse_log_level, default=default)

    def parse_log_level(self, level):
        # Copy the default config so we can mutate it
        config = copy.deepcopy(DEFAULT_LOGGING)
        # Remove filters to allow console handler to work without DEBUG
        # Set logging level to supplied value
        config['handlers']['console'].update(filters=[], level=level)
        # Allow `request` and `security` logs to propagate up to the
        # root handler
        config['loggers']['django.request']['propagate'] = True
        try:
            config['loggers']['django.security']['propagate'] = True
        except KeyError:
            # Older version of Django lack this logger
            pass
        return config
