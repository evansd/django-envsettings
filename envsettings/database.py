from .base import URLSettingsBase, urlparse


class DatabaseSettings(URLSettingsBase):

    CONFIG = {
        'postgres': {'ENGINE': 'django.db.backends.postgresql_psycopg2'},
        'postgresql': {'ENGINE': 'django.db.backends.postgresql_psycopg2'},
        'postgis': {'ENGINE': 'django.contrib.gis.db.backends.postgis'},
        'mysql': {'ENGINE': 'django.db.backends.mysql'},
        'mysql2': {'ENGINE': 'django.db.backends.mysql'},
        'sqlite': {'ENGINE': 'django.db.backends.sqlite3'},
    }

    def handle_url(self, parsed_url, config):
        config.update({
            'NAME': parsed_url.path[1:],
            'USER': parsed_url.username or '',
            'PASSWORD': parsed_url.password or '',
            'HOST': parsed_url.hostname or '',
            'PORT': parsed_url.port or ''})
        # Allow query params to override values
        for key, value in urlparse.parse_qsl(parsed_url.query):
            if key.upper() in config:
                config[key.upper()] = value
        return config
