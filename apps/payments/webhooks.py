import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Order

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def flutterwave_webhook(request):
    secret_hash = settings.FLUTTERWAVE_SECRET_HASH
    signature = request.headers.get('Verif-Hash', '')

    if not signature or signature != secret_hash:
        logger.warning('Flutterwave webhook: invalid signature')
        return HttpResponseForbidden('Invalid signature')

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse('Bad payload', status=400)

    event = payload.get('event', '')
    data = payload.get('data', {})

    if event == 'charge.completed' and data.get('status') == 'successful':
        tx_ref = data.get('tx_ref', '')
        tx_id = str(data.get('id', ''))
        amount = data.get('amount', 0)
        currency = data.get('currency', '')

        try:
            order = Order.objects.get(id=tx_ref)
        except Order.DoesNotExist:
            logger.error(f'Webhook: order {tx_ref} not found')
            return HttpResponse('Order not found', status=404)

        if order.payment_status == Order.COMPLETED:
            return HttpResponse('Already processed', status=200)

        if currency != 'UGX' or int(amount) < int(order.amount_ugx):
            logger.error(f'Webhook: amount mismatch for order {tx_ref}')
            return HttpResponse('Amount mismatch', status=400)

        order.payment_status = Order.COMPLETED
        order.flutterwave_ref = tx_ref
        order.flutterwave_tx_id = tx_id
        order.paid_at = datetime.now(timezone.utc)
        order.save(update_fields=['payment_status', 'flutterwave_ref', 'flutterwave_tx_id', 'paid_at'])

        if order.report:
            from apps.vehicles.tasks import generate_report
            generate_report.delay(str(order.report.pk))
            logger.info(f'Webhook: triggered report generation for order {tx_ref}')

    return HttpResponse('OK', status=200)
