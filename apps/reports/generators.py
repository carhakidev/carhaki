import logging
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def generate_pdf(report) -> bool:
    try:
        from weasyprint import HTML, CSS
        from django.conf import settings

        processed = report.processed_data or {}
        vehicle = processed.get('vehicle', {})

        html_string = render_to_string('reports/pdf_template.html', {
            'report': report,
            'data': processed,
            'vehicle': vehicle,
            'brands': processed.get('brands', []),
            'accidents': processed.get('accidents', []),
            'recalls': processed.get('recalls', []),
            'odometer_records': processed.get('odometer_records', []),
            'title_history': processed.get('title_history', []),
            'uganda': processed.get('uganda_eligibility', {}),
            'ai_summary': report.ai_summary,
        })

        pdf_bytes = HTML(string=html_string).write_pdf()
        filename = f'carhaki-report-{report.search.identifier}-{report.pk}.pdf'
        report.pdf_file.save(filename, ContentFile(pdf_bytes), save=True)
        logger.info(f'PDF generated: {filename}')
        return True

    except ImportError:
        logger.warning('WeasyPrint not available — skipping PDF generation')
        return False
    except Exception as e:
        logger.exception(f'PDF generation failed for report {report.pk}: {e}')
        return False
