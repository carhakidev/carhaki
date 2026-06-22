from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from apps.vehicles.models import VehicleReport
from apps.payments.models import Order
from apps.api.serializers.vehicles import ReportListSerializer


class DashboardView(APIView):
    """
    GET /api/dashboard/
    Returns dashboard stats and recent reports.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = VehicleReport.objects.filter(
            user=request.user
        ).select_related('search').order_by('-created_at')

        total_spent = Order.objects.filter(
            user=request.user,
            payment_status=Order.COMPLETED,
        ).aggregate(total=Sum('amount_ngn'))['total'] or 0

        stats = {
            'total_reports': reports.count(),
            'completed': reports.filter(status=VehicleReport.COMPLETED).count(),
            'pending': reports.filter(status__in=[VehicleReport.PENDING, VehicleReport.PROCESSING]).count(),
            'total_spent_ngn': int(total_spent),
        }

        return Response({
            'stats': stats,
            'reports': ReportListSerializer(reports[:10], many=True).data,
            'user': {
                'name': request.user.get_full_name() or request.user.email,
                'email': request.user.email,
                'member_since': request.user.date_joined,
            },
        })
