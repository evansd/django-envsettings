import re

from django.core.exceptions import ImproperlyConfigured

from .base import URLConfigBase, is_importable


class cache(URLConfigBase):

    CONFIG = {
        'locmem': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        'file': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'},
        # Memcached backends are auto-selected based on what packages are installed
        'memcached': {'BACKEND': None},
        'memcached-binary': {'BACKEND': None, 'BINARY': True},
        'redis': {'BACKEND': 'redis_cache.cache.RedisCache'},
    }

    @classmethod
    def handle_file(cls, parsed_url, config):
        if parsed_url.path == '/dev/null':
            config['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
        else:
            config['LOCATION'] = parsed_url.path
        return config

    @classmethod
    def handle_locmem(cls, parsed_url, config):
        config['LOCATION'] = parsed_url.hostname + parsed_url.path
        return config

    @classmethod
    def handle_redis(cls, parsed_url, config):
        if parsed_url.hostname:
            db_num = parsed_url.path[1:]
            location = '{}:{}:{}'.format(
                    parsed_url.hostname,
                    parsed_url.port or 637,
                    db_num or '0')
        else:
            location = 'unix:{}' + parsed_url.path
            # Add default db number if none specified
            if not re.search(':[\d]+$', parsed_url.path):
                location += ':0'
        config['LOCATION'] = location
        if parsed_url.password:
            config.setdefault('OPTIONS', {})['PASSWORD'] = parsed_url.password
        return config

    @classmethod
    def handle_memcached(cls, parsed_url, config):
        if parsed_url.hostname:
            netloc = parsed_url.netloc.split('@')[-1]
            if ',' in netloc:
                location = netloc.split(',')
            else:
                location = '{}:{}'.format(
                    parsed_url.hostname,
                    parsed_url.port or 11211)
        else:
            location = 'unix:{}'.format(parsed_url.path)
        config['LOCATION'] = location
        if parsed_url.username:
            config['USERNAME'] = parsed_url.username
        if parsed_url.password:
            config['PASSWORD'] = parsed_url.password
        # Don't auto-select backend if one has been explicitly configured
        if not config['BACKEND']:
            cls.set_memcached_backend(config)
        return config

    @classmethod
    def handle_memcached_binary(cls, parsed_url, config):
        return cls.handle_memcached(parsed_url, config)

    @classmethod
    def set_memcached_backend(cls, config):
        config['BACKEND'] = 'django_pylibmc.memcached.PyLibMCCache'
        if is_importable(config['BACKEND']):
            return
        if config.get('BINARY'):
            config['BACKEND'] = 'django_bmemcached.memcached.BMemcached'
            if is_importable(config['BACKEND']):
                return
        if 'USERNAME' in config or 'PASSWORD' in config:
            raise ImproperlyConfigured('')
        if config.get('BINARY'):
            raise ImproperlyConfigured('')
        if is_importable('pylibmc'):
            config['BACKEND'] = 'django.core.cache.backends.memcached.PyLibMCCache'
            return
        config['BACKEND'] = 'django.core.cache.backends.memcached.MemcachedCache'
