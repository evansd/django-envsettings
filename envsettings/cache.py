import re

from .base import URLConfigBase, is_importable


class CacheConfig(URLConfigBase):

    CONFIG = {
        'locmem': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        'file': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'},
        # Memcached backends are auto-selected based on what packages are installed
        'memcached': {'BACKEND': None},
        'memcached-binary': {'BACKEND': None, 'BINARY': True},
        'redis': {'BACKEND': 'redis_cache.cache.RedisCache'},
    }

    def handle_file(self, parsed_url, config):
        if parsed_url.path == '/dev/null':
            config['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
        else:
            config['LOCATION'] = parsed_url.path
        return config

    def handle_locmem(self, parsed_url, config):
        config['LOCATION'] = parsed_url.hostname + parsed_url.path
        return config

    def handle_redis(self, parsed_url, config):
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

    def handle_memcached(self, parsed_url, config):
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
        # Only auto-select backend if one hasn't been explicitly configured
        if not config['BACKEND']:
            self.set_memcached_backend(config)
        return config

    def handle_memcached_binary(self, parsed_url, config):
        return self.handle_memcached(parsed_url, config)

    def set_memcached_backend(self, config):
        """
        Select the most suitable Memcached backend based on the config and
        on what's installed
        """
        # This is the preferred backend as it is the fastest and most fully
        # featured, so we use this by default
        config['BACKEND'] = 'django_pylibmc.memcached.PyLibMCCache'
        if is_importable(config['BACKEND']):
            return
        # Otherwise, binary connections can use this pure Python implementation
        if config.get('BINARY') and is_importable('django_bmemcached'):
            config['BACKEND'] = 'django_bmemcached.memcached.BMemcached'
            return
        # For text-based connections without any authentication we can fall
        # back to Django's core backends if the supporting libraries are
        # installed
        if not any([config.get(key) for key in ('BINARY', 'USERNAME', 'PASSWORD')]):
            if is_importable('pylibmc'):
                config['BACKEND'] = \
                        'django.core.cache.backends.memcached.PyLibMCCache'
            elif is_importable('memcached'):
                config['BACKEND'] = \
                        'django.core.cache.backends.memcached.MemcachedCache'

    def auto_config_memcachier(self, environ, prefix='MEMCACHIER'):
        try:
            servers, username, password = [
                    environ[prefix + key] for key in [
                        '_SERVERS', '_USERNAME', '_PASSWORD']]
        except KeyError:
            return
        return 'memcached-binary://{username}:{password}@{servers}'.format(
            servers=servers, username=username, password=password)

    def auto_config_memcachedcloud(self, environ):
        return self.auto_config_memcachier(environ, prefix='MEMCACHEDCLOUD')

    def auto_config_redistogo(self, environ):
        return environ.get('REDISTOGO_URL')

    def auto_config_rediscloud(self, environ):
        return environ.get('REDISCLOUD_URL')

    def auto_config_openredis(self, environ):
        return environ.get('OPENREDIS_URL')

    def auto_config_redisgreen(self, environ):
        return environ.get('REDISGREEN_URL')
