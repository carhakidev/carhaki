import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carhaki.settings.production')

app = Celery('carhaki')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Fix for Upstash rediss:// SSL requirement
redis_url = os.getenv('REDIS_URL', '')
if redis_url.startswith('rediss://'):
    app.conf.broker_url = redis_url + '?ssl_cert_reqs=CERT_NONE'
    app.conf.result_backend = redis_url + '?ssl_cert_reqs=CERT_NONE'

app.autodiscover_tasks()
