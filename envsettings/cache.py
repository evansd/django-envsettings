import re

from .base import URLSettingsBase, is_importable


class CacheSettings(URLSettingsBase):

    CONFIG = {
        'locmem': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
        'file': {'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache'},
        # Memcached backends are auto-selected based on what packages are installed
        'memcached': {'BACKEND': None},
        'memcached-binary': {'BACKEND': None, 'BINARY': True},
        'redis': {'BACKEND': 'redis_cache.cache.RedisCache'},
    }

    def handle_file_url(self, parsed_url, config):
        if parsed_url.path == '/dev/null':
            config['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
        else:
            config['LOCATION'] = parsed_url.path
        return config

    def handle_locmem_url(self, parsed_url, config):
        config['LOCATION'] = parsed_url.hostname + parsed_url.path
        return config

    def handle_redis_url(self, parsed_url, config):
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

    def handle_memcached_url(self, parsed_url, config):
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

    def handle_memcached_binary_url(self, parsed_url, config):
        return self.handle_memcached_url(parsed_url, config)

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

    def auto_config_memcachier(self, env, prefix='MEMCACHIER'):
        try:
            servers, username, password = [
                    env[prefix + key] for key in [
                        '_SERVERS', '_USERNAME', '_PASSWORD']]
        except KeyError:
            return
        return 'memcached-binary://{username}:{password}@{servers}/'.format(
            servers=servers, username=username, password=password)

    def auto_config_memcachedcloud(self, env):
        return self.auto_config_memcachier(env, prefix='MEMCACHEDCLOUD')

    def auto_config_redistogo(self, env):
        return env.get('REDISTOGO_URL')

    def auto_config_rediscloud(self, env):
        return env.get('REDISCLOUD_URL')

    def auto_config_openredis(self, env):
        return env.get('OPENREDIS_URL')

    def auto_config_redisgreen(self, env):
        return env.get('REDISGREEN_URL')
