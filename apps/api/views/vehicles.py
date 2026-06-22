from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from apps.vehicles.models import VehicleReport
from apps.api.serializers.vehicles import (
    VehicleReportSerializer, ReportListSerializer
)
from apps.vehicles.preview_service import get_preview_data


class VehiclePreviewView(APIView):
    """
    GET /api/vehicles/preview/<vin>/
    Public endpoint — returns free NHTSA preview data.
    """
    permission_classes = [AllowAny]

    def get(self, request, vin):
        vin = vin.upper().strip()
        try:
            preview = get_preview_data(vin)
            return Response(preview)
        except Exception:
            return Response(
                {'error': 'Could not retrieve vehicle data. Check the VIN and try again.'},
                status=status.HTTP_404_NOT_FOUND,
            )


class ReportListView(APIView):
    """
    GET /api/reports/
    Returns all reports for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = VehicleReport.objects.filter(
            user=request.user
        ).select_related('search').order_by('-created_at')
        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)


class ReportDetailView(APIView):
    """
    GET /api/reports/<pk>/
    Returns full report data for the authenticated owner.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report = VehicleReport.objects.select_related('search').get(
                id=pk,
                user=request.user,
            )
        except VehicleReport.DoesNotExist:
            return Response({'error': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(VehicleReportSerializer(report).data)


class SharedReportView(APIView):
    """
    GET /api/reports/shared/<token>/
    Public — returns shared report by share token.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            report = VehicleReport.objects.select_related('search').get(
                share_token=token,
                is_public=True,
            )
        except VehicleReport.DoesNotExist:
            return Response(
                {'error': 'Report not found or not public.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(VehicleReportSerializer(report).data)
