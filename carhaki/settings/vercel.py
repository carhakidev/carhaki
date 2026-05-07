import os
from .production import *  # noqa

# Vercel terminates SSL at the edge — no redirect needed inside the app
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Accept all *.vercel.app subdomains + any custom domains added via ALLOWED_HOSTS env var
_extra = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
ALLOWED_HOSTS = _extra + ['.vercel.app', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app'] + [
    f'https://{h}' for h in _extra if h not in ('localhost', '127.0.0.1')
]

# Use in-process memory cache when Redis is not configured
if not os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Fall back to console email when SendGrid is not configured
if not os.environ.get('SENDGRID_API_KEY'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# django-axes needs a persistent store for distributed deployments;
# disable it on Vercel (stateless serverless) to avoid startup errors
AXES_ENABLED = False

# WhiteNoise: serve static files directly from source dirs without collectstatic.
# CompressedManifestStaticFilesStorage requires a pre-built manifest which doesn't
# exist on Vercel (no collectstatic build step), so fall back to plain storage.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
