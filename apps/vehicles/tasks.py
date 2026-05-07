import logging
from datetime import datetime, timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import VehicleReport
from .grading import calculate_grade, GRADE_COLOURS, GRADE_LABELS
from apps.integrations.nhtsa import NHTSAProvider
from apps.integrations.vinaudit import VinAuditProvider
from apps.integrations.otofacts import OtoFactsProvider
from apps.integrations.carcheck_jp import CarCheckJPProvider
from apps.integrations.normalizer import ReportNormalizer
from apps.integrations.anthropic_ai import generate_ai_summary
from apps.integrations.cache import VehicleDataCache

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_report(self, report_id: str):
    try:
        report = VehicleReport.objects.select_related('search', 'user').get(pk=report_id)
    except VehicleReport.DoesNotExist:
        logger.error(f'Report {report_id} not found')
        return

    report.status = VehicleReport.PROCESSING
    report.save(update_fields=['status'])

    search = report.search
    identifier = search.identifier
    source_country = search.source_country
    cache = VehicleDataCache()

    try:
        cached = cache.get_report(identifier, report.report_type, source_country)
        if cached:
            processed = cached
        else:
            if source_country == 'USA':
                processed = _generate_usa_report(identifier, report.report_type)
            else:
                processed = _generate_japan_report(identifier, report.report_type)
            cache.set_report(identifier, report.report_type, source_country, processed)

        # Compute market value in UGX
        from apps.core.models import SiteConfig
        config = SiteConfig.get_solo()
        mv = processed.get('market_value', {})
        if mv.get('estimate_usd'):
            mv['estimate_ugx'] = int(mv['estimate_usd'] * float(config.usd_to_ugx_rate))
            processed['market_value'] = mv

        # Grade the vehicle
        risk_score, grade = calculate_grade(processed)
        processed['risk_score'] = risk_score
        processed['overall_grade'] = grade
        processed['grade_colour'] = GRADE_COLOURS.get(grade, '#6c757d')
        processed['grade_label'] = GRADE_LABELS.get(grade, 'Unknown')

        # AI summary
        if report.report_type == VehicleReport.FULL:
            ai_summary = generate_ai_summary(processed)
            report.ai_summary = ai_summary
            processed['ai_summary'] = ai_summary

        report.processed_data = processed
        report.overall_grade = grade
        report.risk_score = risk_score
        report.status = VehicleReport.COMPLETED
        report.completed_at = datetime.now(timezone.utc)
        report.is_public = True
        report.save()

        # Generate PDF async
        generate_report_pdf.delay(str(report.pk))

        # Send email notification
        if report.user and report.user.email:
            send_report_email.delay(str(report.pk))

    except Exception as exc:
        logger.exception(f'Error generating report {report_id}: {exc}')
        report.status = VehicleReport.FAILED
        report.save(update_fields=['status'])
        raise self.retry(exc=exc)


def _generate_usa_report(identifier: str, report_type: str) -> dict:
    nhtsa = NHTSAProvider()
    basic_info = nhtsa.get_basic_info(identifier)
    recalls = []
    if basic_info.get('make') and basic_info.get('model') and basic_info.get('year'):
        recalls = nhtsa.get_recalls(basic_info['make'], basic_info['model'], basic_info['year'])

    raw_data = {}
    if report_type == VehicleReport.FULL:
        vinaudit = VinAuditProvider()
        raw_data = vinaudit.get_full_report(identifier)

    normalizer = ReportNormalizer()
    return normalizer.normalize(raw_data or {}, 'vinaudit', basic_info=basic_info, recalls=recalls)


def _generate_japan_report(identifier: str, report_type: str) -> dict:
    otofacts = OtoFactsProvider()
    if otofacts.api_key:
        raw_data = otofacts.get_full_report(identifier)
        if not raw_data.get('error'):
            normalizer = ReportNormalizer()
            return normalizer.normalize(raw_data, 'otofacts')

    carcheck = CarCheckJPProvider()
    raw_data = carcheck.get_full_report(identifier)
    normalizer = ReportNormalizer()
    return normalizer.normalize(raw_data, 'carcheck_jp')


@shared_task
def generate_report_pdf(report_id: str):
    try:
        report = VehicleReport.objects.get(pk=report_id)
        from apps.reports.generators import generate_pdf
        generate_pdf(report)
    except Exception as e:
        logger.exception(f'PDF generation failed for report {report_id}: {e}')


@shared_task
def send_report_email(report_id: str):
    try:
        report = VehicleReport.objects.select_related('search', 'user').get(pk=report_id)
        if not report.user or not report.user.email:
            return

        site_url = getattr(settings, 'SITE_URL', 'https://carhaki.com')
        report_url = f"{site_url}/reports/{report.pk}/"
        vehicle = report.processed_data.get('vehicle', {}) if report.processed_data else {}

        subject = f"Your CarHaki Report — {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}"
        html_body = render_to_string('emails/report_ready.html', {
            'report': report,
            'vehicle': vehicle,
            'report_url': report_url,
            'user': report.user,
        })

        send_mail(
            subject=subject,
            message=f'Your CarHaki report is ready. View it at: {report_url}',
            html_message=html_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[report.user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.exception(f'Email send failed for report {report_id}: {e}')
