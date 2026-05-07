from .base import *  # noqa

DEBUG = True

try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1']
except ImportError:
    pass

# Use local file storage in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relax rate limiting in dev
AXES_ENABLED = False

# Fall back to local-memory cache if Redis is not available in dev
import environ as _environ_dev
_env_dev = _environ_dev.Env()
_redis_url = _env_dev('REDIS_URL', default='redis://localhost:6379/0')

try:
    import redis as _redis_lib
    _r = _redis_lib.Redis.from_url(_redis_url)
    _r.ping()
    # Redis available — keep django-redis config from base
except Exception:
    # Redis not available — fall back to local memory cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
