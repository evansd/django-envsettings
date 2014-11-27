import copy
import os
import re
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.core.exceptions import ImproperlyConfigured
from django.utils.log import DEFAULT_LOGGING
try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text


def get(varname, default=None, convert=smart_text):
    """
    Gets a key from os.environ, converting it to supplied type (unicode string by
    default)
    """
    value = os.getenv(varname, default)
    if value is None:
        raise ImproperlyConfigured(
                "Environment variable '{}' not defined".format(varname))
    try:
        return convert(value)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            "Error in environment variable '{}': {}" .format(varname, exc))


def parse_bool(value):
    """
    Converts 'True' and 'False' strings to booleans
    """
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized == 'true':
        return True
    elif normalized == 'false':
        return False
    else:
        raise ValueError(
                "invalid boolean '{}' (must be 'True' or 'False')".format(value))

def get_bool(varname, default=None):
    return get(varname, default, convert=parse_bool)


def get_int(varname, default=None):
    return get(varname, default, convert=int)


class URLConfigBase(object):

    CONFIG = {}

    @classmethod
    def get(cls, varname, default=None):
        return get(varname, default, convert=cls.parse)

    @classmethod
    def parse(cls, url):
        parsed_url = urlparse.urlparse(url)
        try:
            default_config = cls.CONFIG[parsed_url.scheme]
        except KeyError:
            raise ValueError(
                'unrecognised URL scheme for {}: {}'.format(
                    cls.__name__, parsed_url.scheme))
        handler = cls.get_handler_for_scheme(parsed_url.scheme)
        config = copy.deepcopy(default_config)
        return handler(parsed_url, config)

    @classmethod
    def get_handler_for_scheme(cls, scheme):
        method_name = 'handle_{}'.format(re.sub('\+\.\-', '_', scheme))
        return getattr(cls, method_name, cls.generic_handler)

    @classmethod
    def generic_handler(self, parsed_url, config):
        return config


def get_logging_config(level='INFO'):
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
