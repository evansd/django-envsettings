import email.utils as email_utils

from .base import get, URLConfigBase, is_importable


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
        'mailgun': {'EMAIL_BACKEND': 'django_mailgun.MailgunBackend'},
        'sendgrid': {'EMAIL_BACKEND': 'sgbackend.SendGridBackend'},
        'mandrill': {'EMAIL_BACKEND': 'djrill.mail.backends.djrill.DjrillBackend'},
        'ses': {'EMAIL_BACKEND': 'django_ses_backend.SESBackend'},
        'postmark': {'EMAIL_BACKEND': 'postmark.django_backend.EmailBackend'},
    }

    @classmethod
    def handle_smtp(cls, parsed_url, config):
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

    @classmethod
    def handle_smtps(cls, parsed_url, config):
        return cls.handle_smtp(parsed_url, config)

    @classmethod
    def handle_file(cls, parsed_url, config):
        if parsed_url.path == '/dev/stdout':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
        elif parsed_url.path == '/dev/null':
            config['EMAIL_BACKEND'] = 'django.core.mail.backends.dummy.EmailBackend'
        else:
            config['EMAIL_FILE_PATH'] = parsed_url.path
        return config

    def handle_mailgun(cls, parsed_url, config):
        config['MAILGUN_ACCESS_KEY'] = parsed_url.password
        config['MAILGUN_SERVER_NAME'] = parsed_url.hostname
        return config

    def auto_config_mailgun(cls, environ):
        try:
            api_key, login, password, server, port = [
                    environ['MAILGUN_' + key] for key in (
                        'API_KEY', 'SMTP_LOGIN', 'SMTP_PASSWORD',
                        'SMTP_SERVER', 'SMTP_PORT')]
        except KeyError:
            return
        if is_importable(cls.CONFIG['mailgun']['EMAIL_BACKEND']):
            domain = login.split('@')[-1]
            return 'mailgun://api:{api_key}@{domain}'.format(
                    api_key=api_key, domain=domain)
        else:
            return 'smtps://{login}:{password}@{server}:{port}'.format(
                    login=login, password=password, server=server, port=port)

    def handle_sendgrid(cls, parsed_url, config):
        config['SENDGRID_USER'] = parsed_url.username
        config['SENDGRID_PASSWORD'] = parsed_url.password
        return config

    def auto_config_sendgrid(cls, environ):
        try:
            user, password = environ['SENDGRID_USERNAME'], environ['SENDGRID_PASSWORD']
        except KeyError:
            return
        if is_importable(cls.CONFIG['sendgrid']['EMAIL_BACKEND']):
            return 'sendgrid://{user}:{password}@sendgrid.com'.format(
                    user=user, password=password)
        else:
            return 'smtps://{user}:{password}@smtp.sendgrid.net:587'.format(
                    user=user, password=password)

    def handle_mandrill(cls, parsed_url, config):
        config['MANDRILL_API_KEY'] = parsed_url.password
        if parsed_url.username:
            config['MANDRILL_SUBACCOUNT'] = parsed_url.username
        return config

    def auto_config_mandrill(cls, environ):
        try:
            user, api_key = environ['MANDRIL_USERNAME'], environ['MANDRILL_APIKEY']
        except KeyError:
            return
        if is_importable(cls.CONFIG['mandrill']['EMAIL_BACKEND']):
            return 'mandrill://:{api_key}@mandrillapp.com'.format(
                    api_key=api_key)
        else:
            return 'smtps://{user}:{api_key}@smtp.mandrillapp.com:587'.format(
                    user=user, api_key=api_key)

    def handle_ses(cls, parsed_url, config):
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

    def handle_postmark(cls, parsed_url, config):
        config['POSTMARK_API_KEY'] = parsed_url.password
        return config

    def auto_config_postmark(cls, environ):
        try:
            api_key, server = (environ['POSTMARK_API_KEY'],
                    environ['POSTMARK_SMTP_SERVER'])
        except KeyError:
            return
        if is_importable(cls.CONFIG['postmark']['EMAIL_BACKEND']):
            return 'postmark://user:{api_key}@postmarkapp.com'.format(
                    api_key=api_key)
        else:
            return 'smtps://{api_key}:{api_key}@{server}:25'.format(
                    api_key=api_key, server=server)
