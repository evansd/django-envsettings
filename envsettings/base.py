import copy
import importlib
import os
import re
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from django.core.exceptions import ImproperlyConfigured
try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text


def is_importable(module_name):
    package = module_name.split('.')[0]
    try:
        importlib.import_module(package)
        return True
    except ImportError:
        return False


class EnvSettings(object):

    def __init__(self, environ=os.environ):
        self.environ = environ

    def get(self, keys, default=None, convert=smart_text):
        if hasattr(keys, 'strip'):
            keys = [keys]
        for key in keys:
            try:
                value = self.environ[key]
                break
            except KeyError:
                continue
        else:
            value = default if not callable(default) else default()
        if value is None:
            raise ImproperlyConfigured(
                    'No environment variables matching {!r}'.format(keys))
        return convert(value)

    def parse_bool(self, value):
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

    def get_bool(self, keys, default=None):
        return self.get(keys, default, convert=self.parse_bool)

    def get_int(self, keys, default=None):
        return self.get(keys, default, convert=int)


class URLConfigBase(EnvSettings):

    CONFIG = {}

    def get(self, keys=(), default=None, auto_config=False):
        if auto_config:
            orig_default = default
            default = lambda: self.get_auto_config_url() or orig_default
        return super(URLConfigBase, self).get(keys, default,
                convert=self.parse)

    def parse(self, url):
        parsed_url = urlparse.urlparse(url)
        try:
            default_config = self.CONFIG[parsed_url.scheme]
        except KeyError:
            raise ValueError(
                'unrecognised URL scheme for {}: {}'.format(
                    self.__class__.__name__, parsed_url.geturl()))
        handler = self.get_handler_for_scheme(parsed_url.scheme)
        config = copy.deepcopy(default_config)
        return handler(parsed_url, config)

    def get_handler_for_scheme(self, scheme):
        method_name = 'handle_{}'.format(re.sub('\+\.\-', '_', scheme))
        return getattr(self, method_name, self.generic_handler)

    def generic_handler(self, parsed_url, config):
        return config

    def get_auto_config_url(self):
        auto_config_methods = [
                getattr(self, attr) for attr in sorted(dir(self))
                if attr.startswith('auto_config_')]
        for method in auto_config_methods:
            url = method(self.environ)
            if url:
                return url