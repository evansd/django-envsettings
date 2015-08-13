from __future__ import absolute_import

from envsettings.base import is_importable
from envsettings import (EnvSettings, CacheSettings, DatabaseSettings,
        EmailSettings)


def get_from(SettingsClass, value):
    settings = SettingsClass({'SOMEVAR': value})
    return settings.get('SOMEVAR')


class TestIsImportable:

    def test_existing_package_importable(self):
        assert is_importable('imaplib')

    def test_nonexistent_package_not_importable(self):
        assert not is_importable('aintnopackageevelkdsjfl')


class TestEnvSettings:

    def test_get_bool(self):
        for var, default, result in [
                ('True', None, True),
                ('False', None, False),
                (None, True, True),
                (None, False, False),
                ]:
            envsettings = EnvSettings({'MYVAR': var} if var is not None else {})
            assert result == envsettings.get_bool('MYVAR', default=default)


class TestCacheSettings:

    def test_redis_url(self):
        url = 'redis://:mypassword@/path/to/socket'
        config = {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'unix://:mypassword@/path/to/socket',
            'OPTIONS': {},
        }
        assert config == get_from(CacheSettings, url)

    def test_memcachier_auto_config(self):
        env = {
            'MEMCACHIER_SERVERS': '127.0.0.1:9000,127.0.0.2:9001',
            'MEMCACHIER_USERNAME': 'me',
            'MEMCACHIER_PASSWORD': 'mypassword'
        }
        config = {
            'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
            'BINARY': True,
            'LOCATION': ['127.0.0.1:9000', '127.0.0.2:9001'],
            'USERNAME': 'me',
            'PASSWORD': 'mypassword',
        }
        assert config == CacheSettings(env).get(auto_config=True)


class TestDatabaseSettings:

    def test_postgres_url(self):
        url = 'postgres://me:mypassword@example.com:999/mydb'
        config = {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'mydb',
            'HOST': 'example.com',
            'PORT': 999,
            'USER': 'me',
            'PASSWORD': 'mypassword',
        }
        assert config == get_from(DatabaseSettings, url)


class TestEmailSettings:

    def test_smtps_url(self):
        url = 'smtps://me:mypassword@example.com:999'
        config = {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': 'example.com',
            'EMAIL_PORT': 999,
            'EMAIL_HOST_USER': 'me',
            'EMAIL_HOST_PASSWORD': 'mypassword',
            'EMAIL_USE_TLS': True
        }
        assert config == get_from(EmailSettings, url)

    def test_sendgrid_auto_config(self):
        env = {
            'SENDGRID_USERNAME': 'me',
            'SENDGRID_PASSWORD': 'mypassword'
        }
        config = {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': 'smtp.sendgrid.net',
            'EMAIL_PORT': 587,
            'EMAIL_HOST_USER': 'me',
            'EMAIL_HOST_PASSWORD': 'mypassword',
            'EMAIL_USE_TLS': True
        }
        assert config == EmailSettings(env).get(auto_config=True)
