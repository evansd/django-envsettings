Django EnvSettings
==================

.. image:: https://img.shields.io/travis/evansd/django-envsettings.svg
   :target:  https://travis-ci.org/evansd/django-envsettings
   :alt: Build Status

.. image:: https://img.shields.io/pypi/v/django-envsettings.svg
    :target: https://pypi.python.org/pypi/django-envsettings
    :alt: Latest PyPI version

**One-stop shop for configuring 12-factor Django apps**

 * Simple API for getting settings from environment variables.
 * Supports wide variety of email, cache and database backends.
 * Easily customisable and extensible.
 * One line auto-config for many Heroku add-ons.


Basic Settings
--------------

In your Django project's ``settings.py``:

.. code-block:: python

    import envsettings

    SECRET_KEY = envsettings.get('DJANGO_SECRET_KEY', 'development_key_not_a_secret')

    # Accepts the strings "True" and "False"
    DEBUG = envsettings.get_bool('DJANGO_DEBUG', default=True)

    FILE_UPLOAD_MAX_MEMORY_SIZE = envsettings.get_int('MAX_UPLOAD_SIZE', default=2621440)


Email Settings
--------------

Because of the way Django's email settings work, this requires a bit of a hack with
``locals()``:

.. code-block:: python

    import envsettings

    locals().update(
        envsettings.email.get('MAIL_URL', default='file:///dev/stdout'))


This sets ``EMAIL_BACKEND`` and whatever other values are needed to
configure the selected backend.

Example URLs
++++++++++++

Standard SMTP backend:

.. code-block:: bash

    # SMTP without TLS
    smtp://username:password@host.example.com:25
    # SMTP with TLS
    smtps://username:password@host.example.com:587


Special Django backends for use in development:

.. code-block:: bash

    # Console backend
    file:///dev/stdout

    # Dummy packend
    file:///dev/null

    # File-based backend
    file:///path/to/output/dir


Proprietary backends (each requires the appropriate package installed):

.. code-block:: bash

   # Requires `django-mailgun`
   mailgun://api:api_key@my-sending-domain.com

   # Requires `sendgrid-django`
   sendgrid://username:password@sendgrid.com

   # Requires `djrill`
   mandrill://:api_key@mandrillapp.com
   mandrill://subaccount_name:api_key@mandrillapp.com

   # Requires `django-ses-backend`
   ses://access_key_id:access_key@us-east-1
   ses://access_key_id:access_key@email.eu-west-1.amazonaws.com

   # Requires `django-postmark`
   postmark://api:api_key@postmarkapp.com


Heroku Auto-Config
++++++++++++++++++

Pass ``auto_config=True`` like so:

.. code-block:: python

    locals().update(
        envsettings.email.get(default='file:///dev/stdout', auto_config=True))

This will automatically detect and configure any of the following Heroku email add-ons:
*Mailgun*, *Sendgrid*, *Mandrill*, *Postmark*.

So, for instance, you can configure your app to send email via Mailgun simply by running:

.. code-block:: bash

   heroku addons:add mailgun:starter

By default it will use each provider's SMTP endpoint, however if it detects that
the appropriate backend is installed (see list above) it will configure Django to
use the HTTP endpoint which will be faster.


Cache Settings
--------------

.. code-block:: python

    import envsettings

    CACHES = {'default': envsettings.cache.get('CACHE_URL', 'locmem://')}


Example URLs
++++++++++++

Django backends for use in development:

.. code-block:: bash

   # Local memory
   locmem://
   # Local memory with prefix
   locmem://some-prefix

   # File based
   file:///path/to/cache/directory

   # Dummy cache
   file:///dev/null


Redis (requires ``django-redis`` package):

.. code-block:: bash

  # Basic Redis configuration
  redis://example.com:6379
  # With password
  redis://:secret@example.com:6379
  # Specifying database number
  redis://example.com:6379/3
  # Using UNIX socket
  redis:///path/to/socket
  # Using UNIX socket with password and database number
  redis://:secret@/path/to/socket:3


To use Memcached you need one of the following packages installed:
``django_pylibmc``, ``django_bmemcached``, ``pylibmc``, ``mecached``

Only ``django_pylibmc`` and ``django_bmemcachd`` support authentication and the memcached
binary protocol, so if you want to use either of these featues you'll need one of those
packages.

.. code-block:: bash

   # Basic Memcached configuration
   memcached://example.com:11211
   # Multiple servers
   memcached://example.com:11211,another.com:11211,onemore.com:11211
   # With authentication
   memcached://username:password@example.com
   # Using the binary protocol
   memcached-binary://example.com:11211


Heroku Auto-Config
++++++++++++++++++

Pass ``auto_config=True`` like so:

.. code-block:: python

   CACHES = {'default': envsettings.cache.get(default='locmen://', auto_config=True)}

This will automatically detect and configure any of the following Heroku cache add-ons:
*Memcachier*, *MemcachedCloud*, *RedisToGo*, *RedisCloud*, *OpenRedis*, *RedisGreen*.


Customising & Extending
-----------------------

Django EnvSettings is designed to be easily extensible by subclassing one of the existing
settings providers: ``CacheSettings``, ``EmailSettings``, or ``DatabaseSettings``.


Changing default configuration
++++++++++++++++++++++++++++++

Obviously you can modify the configuration dictionary after it's returned from ``envsettings``.
However you can also set default values for each backend, while letting the environment determine
which backend to use. For example:

.. code-block:: python

   envsettings.database.CONFIG['postgres']['OPTIONS'] = {
       'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE}


Supporting new backends
+++++++++++++++++++++++

To add a new backend, subclass the appropriate settings class.
You will then need to add a key to the ``CONFIG`` dictionary which maps
the URL scheme you want to use for your backend to the default config
for that backend. You will also need to add a method named
``handle_<URL_SCHEME>_url`` which will be passed the output from ``urlparse`` and the
default config. The method should use the values from the parsed URL to update the
config appropriately.

For example:


.. code-block:: python

   import envsettings

   class CacheSettings(envsettings.CacheSettings):

       CONFIG = dict(envsettings.CacheSettings.CONFIG, **{
           'my-proto': {'BACKEND': 'my_cache_backend.MyCacheBackend'}
       })

       def handle_my_proto_url(self, parsed_url, config):
           config['HOST'] = parsed_url.hostname or 'localhost'
           config['PORT'] = parsed_url.port or 9000
           config['USERNAME'] = parsed_url.username
           config['PASSWORD'] = parsed_url.password
           return config

   cachesettings = CacheSettings()

   CACHES = {'default': cachesettings.get('CACHE_URL')}


Supporting new auto configuration options
+++++++++++++++++++++++++++++++++++++++++

To add a new auto-configuration provider, subclass the appropriate settings class and add a method
named ``auto_config_<PROVIDER_NAME>``. This will be passed a dictionary of environment
variables and should return either an appropriate configuration URL, or None.

The auto config methods are tried in lexical order, so if you want to force a method
to be tried first you could call it ``auto_config_00_my_provider``, or something like
that.

Here's an example:

.. code-block:: python

   import envsettings

   class CacheSettings(envsettings.CacheSettings):

       def auto_config_my_redis(self, env):
           try:
               host = env['MY_REDIS_HOST']
               password = env['MY_REDIS_PASSWORD']
           except KeyError:
               return None
           else:
               return 'redis://:{password}@{host}'.format(
                   host=host, password=password)

   cachesettings = CacheSettings()

   CACHES = {'default': cachesettings.get('CACHE_URL', auto_config=True)}


Compatibility
-------------

Tested on Python **2.7**, **3.3**, **3.4** and **PyPy**,
with Django versions **1.4** --- **1.7**


Issues & Contributing
---------------------

Raise an issue on the `GitHub project <https://github.com/evansd/django-envsettings>`_ or
feel free to nudge `@_EvansD <https://twitter.com/_evansd>`_ on Twitter.


License
-------

MIT Licensed
