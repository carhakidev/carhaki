import json
import logging
from datetime import datetime, timezone

from django.db import transaction
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages

from .models import Order
from . import paystack as paystack_client

logger = logging.getLogger(__name__)


class InitiatePaymentView(LoginRequiredMixin, View):
    """
    GET: initialise a Paystack transaction, save the reference/access_code,
    and redirect the customer to Paystack's hosted payment page.
    """

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id, user=request.user)

        if order.is_paid:
            return redirect('payments:payment_success', pk=order.pk)

        callback_url = request.build_absolute_uri(reverse('payments:verify'))

        try:
            response = paystack_client.initialize_transaction(
                email=order.customer_email or request.user.email,
                amount_ngn=int(order.amount_ngn),
                reference=str(order.id),
                callback_url=callback_url,
            )
        except Exception as exc:
            logger.exception(f'Paystack initialise failed for order {order.id}: {exc}')
            messages.error(request, 'Could not reach the payment gateway. Please try again.')
            return redirect('payments:payment_failed', pk=order.pk)

        data = response.get('data', {})
        order.paystack_reference = data.get('reference', str(order.id))
        order.paystack_access_code = data.get('access_code', '')
        order.payment_method = Order.PAYSTACK
        order.save(update_fields=['paystack_reference', 'paystack_access_code', 'payment_method'])

        authorization_url = data.get('authorization_url', '')
        if not authorization_url:
            logger.error(f'Paystack returned no authorization_url for order {order.id}')
            return redirect('payments:payment_failed', pk=order.pk)

        return redirect(authorization_url)


class VerifyPaymentView(View):
    """
    Paystack redirects here after the customer completes (or abandons) payment.
    No login required — Paystack sends the customer directly.
    """

    def get(self, request):
        reference = request.GET.get('reference', '')
        if not reference:
            return redirect('/')

        try:
            response = paystack_client.verify_transaction(reference)
        except Exception as exc:
            logger.exception(f'Paystack verify failed for reference {reference}: {exc}')
            # Can't look up the order without a valid reference; redirect home
            return redirect('/')

        data = response.get('data', {})

        try:
            order = Order.objects.get(paystack_reference=reference)
        except Order.DoesNotExist:
            logger.error(f'VerifyPaymentView: order with reference {reference} not found')
            return redirect('/')

        if order.is_paid:
            return redirect('payments:payment_success', pk=order.pk)

        amount_matches = int(data.get('amount', 0)) >= int(order.amount_ngn) * 100

        if data.get('status') == 'success' and amount_matches:
            with transaction.atomic():
                order.payment_status = Order.COMPLETED
                order.paid_at = datetime.now(timezone.utc)
                order.save(update_fields=['payment_status', 'paid_at'])

                if order.report:
                    from apps.vehicles.tasks import generate_report
                    generate_report.delay(str(order.report.pk))
                    logger.info(f'VerifyPaymentView: queued report for order {order.id}')

            messages.success(request, 'Payment confirmed! Your report is being generated.')
            return redirect('payments:payment_success', pk=order.pk)

        order.payment_status = Order.FAILED
        order.save(update_fields=['payment_status'])
        messages.error(request, 'Payment could not be verified. Please contact support.')
        return redirect('payments:payment_failed', pk=order.pk)


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(View):
    """
    Server-side Paystack webhook — validates HMAC-SHA512 signature,
    handles charge.success events.
    Always returns 200 to prevent Paystack retry storms.
    """

    def post(self, request):
        signature = request.headers.get('x-paystack-signature', '')
        if not paystack_client.verify_webhook_signature(request.body, signature):
            logger.warning('PaystackWebhookView: invalid signature')
            return HttpResponse(status=200)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            logger.warning('PaystackWebhookView: malformed JSON body')
            return HttpResponse(status=200)

        event = payload.get('event', '')
        data = payload.get('data', {})

        if event != 'charge.success':
            return HttpResponse(status=200)

        reference = data.get('reference', '')
        amount = data.get('amount', 0)  # kobo

        try:
            order = Order.objects.get(paystack_reference=reference)
        except Order.DoesNotExist:
            logger.error(f'PaystackWebhookView: order with reference {reference} not found')
            return HttpResponse(status=200)

        if order.is_paid:
            return HttpResponse(status=200)

        if int(amount) < int(order.amount_ngn) * 100:
            logger.error(f'PaystackWebhookView: amount mismatch for order {order.id}')
            return HttpResponse(status=200)

        with transaction.atomic():
            order.payment_status = Order.COMPLETED
            order.paid_at = datetime.now(timezone.utc)
            order.save(update_fields=['payment_status', 'paid_at'])

            if order.report:
                from apps.vehicles.tasks import generate_report
                generate_report.delay(str(order.report.pk))
                logger.info(f'PaystackWebhookView: queued report for order {order.id}')

        return HttpResponse(status=200)


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = get_object_or_404(Order, pk=self.kwargs['pk'], user=self.request.user)
        ctx['order'] = order
        if order.report:
            ctx['report'] = order.report
        return ctx


class PaymentFailedView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/failed.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['order'] = get_object_or_404(Order, pk=self.kwargs['pk'], user=self.request.user)
        return ctx
