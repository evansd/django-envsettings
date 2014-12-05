import copy
try:
    from importlib.util import find_spec
except ImportError:
    from imp import find_module
    find_spec = False
import os
import re
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text


if find_spec:
    def is_importable(module_name):
        package = module_name.split('.')[0]
        return bool(find_spec(package))
else:
    def is_importable(module_name):
        package = module_name.split('.')[0]
        try:
            f = find_module(package)[0]
            if f:
                f.close()
            return True
        except ImportError:
            return False


class EnvSettings(object):

    def __init__(self, env=os.environ):
        self.env = env

    def get(self, key, default=None):
        return smart_text(self.env.get(key, default))

    def get_bool(self, key, default=None):
        return self.parse_bool(self.env.get(key, default))

    def get_int(self, key, default=None):
        return int(self.env.get(key, default))

    @staticmethod
    def parse_bool(value):
        # Accept bools as well as strings so we can pass them
        # as default values
        if value == 'True' or value == True:
            return True
        elif value == 'False' or value == False:
            return False
        else:
            raise ValueError(
                    "invalid boolean {!r} (must be 'True' or "
                    "'False')".format(value))


class URLSettingsBase(EnvSettings):

    CONFIG = {}

    def __init__(self, *args, **kwargs):
        super(URLSettingsBase, self).__init__(*args, **kwargs)
        # Each instance gets its own copy of the config so it
        # can be safely mutated
        self.CONFIG = copy.deepcopy(self.CONFIG)

    def get(self, key=None, default=None, auto_config=False):
        value = self.env.get(key) if key else None
        if value is None and auto_config:
            value = self.get_auto_config_url()
        if value is None:
            value = default
        return self.parse(value)

    def parse(self, url):
        parsed_url = urlparse.urlparse(url)
        try:
            default_config = self.CONFIG[parsed_url.scheme]
        except KeyError:
            raise ValueError(
                'unrecognised URL scheme for {}: {}'.format(
                    self.__class__.__name__, url))
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
            url = method(self.env)
            if url:
                return url
