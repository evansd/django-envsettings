import email.utils as email_utils

from .base import get, URLConfigBase


def parse_email_list(email_string):
    return email_utils.getaddresses([email_string])


def get_email_list(varname, default=None):
    return get(varname, default, convert=parse_email_list)


class email(URLConfigBase):

    CONFIG = {
        'smtp': {'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_USE_TLS': False},
        'smtps': {'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_USE_TLS': True},
        'file': {'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend'},
        'http+mailgun': {'EMAIL_BACKEND': 'django_mailgun.MailgunBackend'},
        'http+sendgrid': {'EMAIL_BACKEND': 'sgbackend.SendGridBackend'},
        'http+mandrill': {'EMAIL_BACKEND': 'djrill.mail.backends.djrill.DjrillBackend'},
        'http+ses': {'EMAIL_BACKEND': 'django_ses_backend.SESBackend'},
    }

    @classmethod
    def generic_handler(cls, parsed_url, config):
        config.update({
            'EMAIL_HOST': parsed_url.hostname or 'localhost',
            'EMAIL_PORT': parsed_url.port or 25,
            'EMAIL_HOST_USER': parsed_url.username or '',
            'EMAIL_HOST_PASSWORD': parsed_url.password or ''})
        return config

    @classmethod
    def handle_file(cls, parsed_url, config):
        if parsed_url.path == '/dev/stdout':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
        elif parsed_url.path == '/dev/null':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.dummy.EmailBackend'
        else:
            config['EMAIL_FILE_PATH'] = parsed_url.path
        return config

    def handle_http_mailgun(cls, parsed_url, config):
        config['MAILGUN_ACCESS_KEY'] = parsed_url.password
        config['MAILGUN_SERVER_NAME'] = parsed_url.hostname
        return config

    def handle_http_sendgrid(cls, parsed_url, config):
        config['SENDGRID_USER'] = parsed_url.username
        config['SENDGRID_PASSWORD'] = parsed_url.password
        return config

    def handle_http_mandrill(cls, parsed_url, config):
        config['MANDRILL_API_KEY'] = parsed_url.password
        if parsed_url.username:
            config['MANDRILL_SUBACCOUNT'] = parsed_url.username
        return config

    def handle_http_ses(cls, parsed_url, config):
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
