from .base import *  # noqa
import environ

env = environ.Env()

DEBUG = False

# Render (and most PaaS) terminates SSL at the edge; the app sees plain HTTP.
# Use the forwarded-proto header instead of redirecting internally.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Allow the Render subdomain automatically; add custom domains via ALLOWED_HOSTS env var
_extra = [h.strip() for h in env('ALLOWED_HOSTS', default='') .split(',') if h.strip()]
ALLOWED_HOSTS = _extra + ['.onrender.com', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in _extra if h not in ('localhost', '127.0.0.1')] + [
    'https://*.onrender.com',
    'https://carhaki-web.vercel.app',
]

# Use S3 for media files only when bucket is configured
if env('AWS_STORAGE_BUCKET_NAME', default=''):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f"{env('AWS_STORAGE_BUCKET_NAME')}.s3.amazonaws.com"

# Email: use SendGrid when configured, otherwise log to console
if env('SENDGRID_API_KEY', default=''):
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {
        'SENDGRID_API_KEY': env('SENDGRID_API_KEY'),
    }
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CORS_ALLOWED_ORIGINS = [
    "https://carhaki.com",
    "https://www.carhaki.com",
    "https://carhaki-web.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
