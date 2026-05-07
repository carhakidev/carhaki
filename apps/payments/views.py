import json
import requests
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from .models import Order
from apps.vehicles.models import VehicleReport, VehicleSearch
from apps.core.models import SiteConfig


class CheckoutView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/checkout.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        order = get_object_or_404(Order, pk=self.kwargs['pk'], user=self.request.user)
        ctx['order'] = order
        ctx['flw_public_key'] = settings.FLUTTERWAVE_PUBLIC_KEY
        ctx['redirect_url'] = self.request.build_absolute_uri(
            reverse('payments:verify_payment', args=[str(order.id)])
        )
        return ctx

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        payment_method = request.POST.get('payment_method', '')
        phone = request.POST.get('phone_number', '')
        order.payment_method = payment_method
        order.phone_number = phone
        order.customer_email = request.user.email
        order.save(update_fields=['payment_method', 'phone_number', 'customer_email'])
        return redirect('payments:checkout', pk=pk)


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


class VerifyPaymentView(LoginRequiredMixin, View):
    def get(self, request, ref):
        order = get_object_or_404(Order, id=ref, user=request.user)
        tx_id = request.GET.get('transaction_id')
        status = request.GET.get('status')

        if status == 'successful' and tx_id:
            verified = self._verify_with_flutterwave(tx_id, order)
            if verified:
                self._complete_order(order, tx_id)
                messages.success(request, 'Payment confirmed! Your report is being generated.')
                return redirect('payments:payment_success', pk=order.pk)

        messages.error(request, 'Payment could not be verified. Please contact support.')
        return redirect('payments:payment_failed', pk=order.pk)

    def _verify_with_flutterwave(self, tx_id: str, order: Order) -> bool:
        url = f'https://api.flutterwave.com/v3/transactions/{tx_id}/verify'
        headers = {'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'}
        try:
            resp = requests.get(url, headers=headers, timeout=15).json()
            data = resp.get('data', {})
            return (
                resp.get('status') == 'success'
                and data.get('status') == 'successful'
                and int(data.get('amount', 0)) >= int(order.amount_ugx)
                and data.get('currency') == 'UGX'
            )
        except Exception:
            return False

    def _complete_order(self, order: Order, tx_id: str):
        from datetime import datetime, timezone
        order.payment_status = Order.COMPLETED
        order.flutterwave_tx_id = tx_id
        order.paid_at = datetime.now(timezone.utc)
        order.save(update_fields=['payment_status', 'flutterwave_tx_id', 'paid_at'])

        if order.report:
            from apps.vehicles.tasks import generate_report
            generate_report.delay(str(order.report.pk))


def create_order_and_report(user, identifier: str, source_country: str, report_type: str) -> Order:
    config = SiteConfig.get_solo()
    amount_map = {
        Order.BASIC: config.basic_report_ugx,
        Order.FULL: config.full_report_ugx,
        Order.DEALER_PACK_10: config.dealer_pack_10_ugx,
    }
    amount_ugx = amount_map.get(report_type, config.full_report_ugx)

    from apps.vehicles.validators import detect_identifier_type
    id_type = detect_identifier_type(identifier)

    search, _ = VehicleSearch.objects.get_or_create(
        identifier=identifier,
        source_country=source_country,
        defaults={'identifier_type': id_type, 'user': user}
    )

    report = VehicleReport.objects.create(
        search=search,
        user=user,
        report_type=report_type,
        status=VehicleReport.PENDING,
    )

    order = Order.objects.create(
        user=user,
        report=report,
        report_type=report_type,
        amount_ugx=amount_ugx,
        amount_usd=config.ugx_to_usd(amount_ugx),
        payment_status=Order.PENDING,
    )
    return order
