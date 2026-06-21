from apps.vehicles.models import VehicleReport, VehicleSearch
from apps.core.constants import REPORT_PRICE_NGN, REPORT_TYPE
from .models import Order


def create_order_and_report(
    user,
    identifier: str,
    identifier_type: str,
    source_country: str = 'USA',
) -> Order:
    """
    Create a VehicleSearch, VehicleReport, and Order for the given user.
    Always creates a US_VEHICLE report at the fixed NGN price from constants.
    """
    search, _ = VehicleSearch.objects.get_or_create(
        identifier=identifier,
        source_country=source_country,
        defaults={'identifier_type': identifier_type, 'user': user},
    )

    report = VehicleReport.objects.create(
        search=search,
        user=user,
        report_type=REPORT_TYPE,
        status=VehicleReport.PENDING,
    )

    order = Order.objects.create(
        user=user,
        report=report,
        report_type=REPORT_TYPE,
        amount_ngn=REPORT_PRICE_NGN,
        payment_status=Order.PENDING,
        customer_email=user.email,
    )
    return order
