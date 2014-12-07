from __future__ import absolute_import

import email.utils

from .base import URLSettingsBase, is_importable


class EmailSettings(URLSettingsBase):

    CONFIG = {
        'smtp': {'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_USE_TLS': False},
        'smtps': {'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_USE_TLS': True},
        'file': {'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend'},
        'mailgun': {'EMAIL_BACKEND': 'django_mailgun.MailgunBackend'},
        'sendgrid': {'EMAIL_BACKEND': 'sgbackend.SendGridBackend'},
        'mandrill': {'EMAIL_BACKEND': 'djrill.mail.backends.djrill.DjrillBackend'},
        'ses': {'EMAIL_BACKEND': 'django_ses_backend.SESBackend'},
        'postmark': {'EMAIL_BACKEND': 'postmark.django_backend.EmailBackend'},
    }

    @staticmethod
    def parse_address_list(address_string):
        """
        Takes an email address list string and returns a list of (name, address) pairs
        """
        return email.utils.getaddresses([address_string])

    def get_address_list(self, key, default=None):
        return self.parse_address_list(self.env.get(key, default))

    def handle_smtp_url(self, parsed_url, config):
        if config.get('EMAIL_USE_TLS'):
            default_port = 587
        elif config.get('EMAIL_USE_SSL'):
            default_port = 465
        else:
            default_port = 25
        config.update({
            'EMAIL_HOST': parsed_url.hostname or 'localhost',
            'EMAIL_PORT': parsed_url.port or default_port,
            'EMAIL_HOST_USER': parsed_url.username or '',
            'EMAIL_HOST_PASSWORD': parsed_url.password or ''})
        return config

    def handle_smtps_url(self, parsed_url, config):
        return self.handle_smtp_url(parsed_url, config)

    def handle_file_url(self, parsed_url, config):
        if parsed_url.path == '/dev/stdout':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
        elif parsed_url.path == '/dev/null':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.dummy.EmailBackend'
        else:
            config['EMAIL_FILE_PATH'] = parsed_url.path
        return config

    def handle_mailgun_url(self, parsed_url, config):
        config['MAILGUN_ACCESS_KEY'] = parsed_url.password
        config['MAILGUN_SERVER_NAME'] = parsed_url.hostname
        return config

    def auto_config_mailgun(self, environ):
        try:
            api_key, login, password, server, port = [
                    environ['MAILGUN_' + key] for key in (
                        'API_KEY', 'SMTP_LOGIN', 'SMTP_PASSWORD',
                        'SMTP_SERVER', 'SMTP_PORT')]
        except KeyError:
            return
        if is_importable(self.CONFIG['mailgun']['EMAIL_BACKEND']):
            domain = login.split('@')[-1]
            return 'mailgun://api:{api_key}@{domain}'.format(
                    api_key=api_key, domain=domain)
        else:
            return 'smtps://{login}:{password}@{server}:{port}'.format(
                    login=login, password=password, server=server, port=port)

    def handle_sendgrid_url(self, parsed_url, config):
        config['SENDGRID_USER'] = parsed_url.username
        config['SENDGRID_PASSWORD'] = parsed_url.password
        return config

    def auto_config_sendgrid(self, environ):
        try:
            user, password = environ['SENDGRID_USERNAME'], environ['SENDGRID_PASSWORD']
        except KeyError:
            return
        if is_importable(self.CONFIG['sendgrid']['EMAIL_BACKEND']):
            return 'sendgrid://{user}:{password}@sendgrid.com'.format(
                    user=user, password=password)
        else:
            return 'smtps://{user}:{password}@smtp.sendgrid.net:587'.format(
                    user=user, password=password)

    def handle_mandrill_url(self, parsed_url, config):
        config['MANDRILL_API_KEY'] = parsed_url.password
        if parsed_url.username:
            config['MANDRILL_SUBACCOUNT'] = parsed_url.username
        return config

    def auto_config_mandrill(self, environ):
        try:
            user, api_key = environ['MANDRILL_USERNAME'], environ['MANDRILL_APIKEY']
        except KeyError:
            return
        if is_importable(self.CONFIG['mandrill']['EMAIL_BACKEND']):
            return 'mandrill://:{api_key}@mandrillapp.com'.format(
                    api_key=api_key)
        else:
            return 'smtps://{user}:{api_key}@smtp.mandrillapp.com:587'.format(
                    user=user, api_key=api_key)

    def handle_ses_url(self, parsed_url, config):
        if parsed_url.username:
            config['AWS_SES_ACCESS_KEY_ID'] = parsed_url.username
        if parsed_url.password:
            config['AWS_SES_SECRET_ACCESS_KEY'] = parsed_url.password
        if parsed_url.hostname:
            if '.' in parsed_url.hostname:
                config['AWS_SES_REGION_ENDPOINT'] = parsed_url.hostname
            else:
                config['AWS_SES_REGION_NAME'] = parsed_url.hostname
        return config

    def handle_postmark_url(self, parsed_url, config):
        config['POSTMARK_API_KEY'] = parsed_url.password
        return config

    def auto_config_postmark(self, environ):
        try:
            api_key, server = (environ['POSTMARK_API_KEY'],
                    environ['POSTMARK_SMTP_SERVER'])
        except KeyError:
            return
        if is_importable(self.CONFIG['postmark']['EMAIL_BACKEND']):
            return 'postmark://user:{api_key}@postmarkapp.com'.format(
                    api_key=api_key)
        else:
            return 'smtps://{api_key}:{api_key}@{server}:25'.format(
                    api_key=api_key, server=server)
