from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from apps.api.serializers.orders import OrderCreateSerializer, OrderSerializer
from apps.payments.models import Order
from apps.payments.paystack import initialize_transaction, verify_transaction
from apps.payments.services import create_order_and_report
from apps.core.constants import REPORT_PRICE_NGN, BUNDLE_PRICES_NGN


class OrderCreateView(APIView):
    """
    POST /api/orders/create/
    Creates order + Paystack transaction.
    Returns Paystack authorization_url for the Next.js frontend to redirect to.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vin = serializer.validated_data['vin']
        quantity = serializer.validated_data['quantity']

        amount_ngn = BUNDLE_PRICES_NGN[quantity] if quantity != '1' else REPORT_PRICE_NGN

        try:
            with transaction.atomic():
                # create_order_and_report returns a single Order; report is order.report
                order = create_order_and_report(
                    user=request.user,
                    identifier=vin,
                    identifier_type='VIN',
                    source_country='USA',
                )
                order.amount_ngn = amount_ngn
                order.quantity = int(quantity)
                order.save(update_fields=['amount_ngn', 'quantity'])

                callback_url = request.build_absolute_uri('/api/payments/verify/')
                paystack_response = initialize_transaction(
                    email=request.user.email,
                    amount_ngn=amount_ngn,
                    reference=str(order.id),
                    callback_url=callback_url,
                )

                if not paystack_response.get('status'):
                    raise Exception('Paystack initialization failed')

                data = paystack_response['data']
                order.paystack_reference = data['reference']
                order.paystack_access_code = data['access_code']
                order.payment_method = Order.PAYSTACK
                order.save(update_fields=['paystack_reference', 'paystack_access_code', 'payment_method'])

                return Response({
                    'order_id': str(order.id),
                    'authorization_url': data['authorization_url'],
                    'access_code': data['access_code'],
                    'reference': data['reference'],
                    'amount_ngn': amount_ngn,
                }, status=status.HTTP_201_CREATED)

        except Exception:
            return Response(
                {'error': 'Could not create order. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OrderStatusView(APIView):
    """
    GET /api/orders/<pk>/status/
    Returns order and report status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.select_related('report').get(
                id=pk,
                user=request.user,
            )
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class PaymentVerifyView(APIView):
    """
    GET /api/payments/verify/?reference=<ref>
    Paystack redirects here after payment.
    Verifies payment and triggers report generation.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        reference = request.GET.get('reference') or request.GET.get('trxref')
        if not reference:
            return Response({'error': 'No reference provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.select_related('report').get(paystack_reference=reference)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.payment_status == Order.COMPLETED:
            return Response({
                'status': 'already_verified',
                'order_id': str(order.id),
                'report_id': str(order.report.id) if order.report else None,
            })

        try:
            result = verify_transaction(reference)
            if result['data']['status'] == 'success':
                with transaction.atomic():
                    order.payment_status = Order.COMPLETED
                    order.paid_at = timezone.now()
                    order.save(update_fields=['payment_status', 'paid_at'])

                    if order.report:
                        from apps.vehicles.tasks import generate_report
                        generate_report(str(order.report.id))

                return Response({
                    'status': 'success',
                    'order_id': str(order.id),
                    'report_id': str(order.report.id) if order.report else None,
                })
            else:
                order.payment_status = Order.FAILED
                order.save(update_fields=['payment_status'])
                return Response({'status': 'failed'}, status=status.HTTP_402_PAYMENT_REQUIRED)

        except Exception:
            return Response(
                {'error': 'Verification failed.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PaystackWebhookAPIView(APIView):
    """
    POST /api/payments/webhook/
    Paystack server-side webhook (separate from the Django-frontend webhook).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from apps.payments.paystack import verify_webhook_signature
        signature = request.headers.get('X-Paystack-Signature', '')
        if not verify_webhook_signature(request.body, signature):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event = request.data.get('event')
        if event == 'charge.success':
            reference = request.data['data']['reference']
            try:
                order = Order.objects.select_related('report').get(
                    paystack_reference=reference,
                    payment_status=Order.PENDING,
                )
                with transaction.atomic():
                    order.payment_status = Order.COMPLETED
                    order.paid_at = timezone.now()
                    order.save(update_fields=['payment_status', 'paid_at'])
                    if order.report:
                        from apps.vehicles.tasks import generate_report
                        generate_report(str(order.report.id))
            except Order.DoesNotExist:
                pass

        return Response(status=status.HTTP_200_OK)
