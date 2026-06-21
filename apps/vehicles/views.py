import re
import logging

from django.views.generic import TemplateView, FormView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse

from .models import VehicleSearch, VehicleReport
from .forms import VehicleSearchForm
from apps.integrations.nhtsa import NHTSAProvider
from apps.integrations.cache import VehicleDataCache
from apps.core.models import FAQ
from apps.core.forms import ContactForm
from apps.core.constants import REPORT_PRICE_NGN

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_form'] = VehicleSearchForm()
        ctx['total_reports'] = VehicleReport.objects.filter(
            status=VehicleReport.COMPLETED
        ).count()
        return ctx

    def post(self, request, *args, **kwargs):
        """
        Handles Buy Report button POSTs from preview.html.
        Fields: identifier (VIN or chassis number)
        """
        from apps.payments.services import create_order_and_report
        from apps.vehicles.validators import detect_identifier_type

        identifier = request.POST.get('identifier', '').upper().strip()

        if not identifier:
            messages.error(request, 'No vehicle identifier provided.')
            return redirect('vehicles:home')

        if not request.user.is_authenticated:
            preview_url = reverse('vehicles:preview', kwargs={'identifier': identifier})
            return redirect(f"{reverse('accounts:login')}?next={preview_url}")

        identifier_type = detect_identifier_type(identifier)

        try:
            order = create_order_and_report(
                user=request.user,
                identifier=identifier,
                identifier_type=identifier_type,
                source_country='USA',
            )
            return redirect('payments:initiate', order_id=order.pk)
        except Exception as exc:
            logger.exception(f'Order creation failed for {identifier}: {exc}')
            messages.error(
                request,
                'Something went wrong creating your order. Please try again or contact support.',
            )
            preview_url = reverse('vehicles:preview', kwargs={'identifier': identifier})
            return redirect(preview_url)


class SearchView(FormView):
    template_name = 'vehicles/search.html'
    form_class = VehicleSearchForm

    def get(self, request, *args, **kwargs):
        # Accept both ?q= (homepage hero) and ?identifier= (form direct)
        identifier = (
            request.GET.get('q', '') or
            request.GET.get('identifier', '')
        ).upper().strip()

        if identifier:
            source_country = request.GET.get('source_country', 'AUTO')
            preview_url = reverse(
                'vehicles:preview', kwargs={'identifier': identifier}
            )
            return redirect(f'{preview_url}?country={source_country}')

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        identifier     = form.cleaned_data['identifier'].upper().strip()
        source_country = form.cleaned_data.get('source_country', 'AUTO')
        preview_url    = reverse(
            'vehicles:preview', kwargs={'identifier': identifier}
        )
        return redirect(f'{preview_url}?country={source_country}')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['source_country'] = self.request.GET.get('source_country', 'AUTO')
        if self.request.user.is_authenticated:
            ctx['recent_searches'] = VehicleSearch.objects.filter(
                user=self.request.user
            ).order_by('-created_at')[:5]
        return ctx


class PreviewView(TemplateView):
    template_name = 'vehicles/preview.html'

    def _is_usa_vin(self, identifier):
        return bool(re.match(r'^[A-HJ-NPR-Z0-9]{17}$', identifier))

    def _fetch_usa_preview(self, identifier):
        """
        Checks Redis cache, then falls back to NHTSA (free, no credits).
        """
        cache = VehicleDataCache()
        cached = cache.get_preview(identifier)
        if cached:
            return cached

        try:
            nhtsa = NHTSAProvider()
            data  = nhtsa.get_basic_info(identifier)
            cache.set_preview(identifier, data)
            return data
        except Exception as exc:
            logger.warning(f'NHTSA error for {identifier}: {exc}')
            return {'error': str(exc)}

    def get_context_data(self, **kwargs):
        ctx        = super().get_context_data(**kwargs)
        identifier = self.kwargs['identifier'].upper()

        ctx['identifier']    = identifier
        ctx['source_country'] = 'USA'
        ctx['search_form']   = VehicleSearchForm(initial={'identifier': identifier})
        ctx['price_ngn']     = REPORT_PRICE_NGN

        vehicle_data = self._fetch_usa_preview(identifier)
        if vehicle_data and 'error' in vehicle_data:
            ctx['error']        = vehicle_data['error']
            ctx['vehicle_data'] = None
        else:
            ctx['vehicle_data'] = vehicle_data

        return ctx


class ReportDetailView(LoginRequiredMixin, DetailView):
    model               = VehicleReport
    template_name       = 'reports/detail.html'
    context_object_name = 'report'

    def get_queryset(self):
        return VehicleReport.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.processed_data:
            ctx['data'] = self.object.processed_data
        return ctx


class SharedReportView(DetailView):
    model               = VehicleReport
    template_name       = 'reports/shared.html'
    context_object_name = 'report'

    def get_object(self):
        token  = self.kwargs['token']
        report = get_object_or_404(
            VehicleReport,
            share_token=token,
            status=VehicleReport.COMPLETED,
        )
        if not report.is_public:
            raise Http404
        return report

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.processed_data:
            ctx['data'] = self.object.processed_data
        return ctx


class ShareReportView(LoginRequiredMixin, View):
    def post(self, request, pk):
        report = get_object_or_404(
            VehicleReport,
            pk=pk,
            user=request.user,
            status=VehicleReport.COMPLETED,
        )
        report.is_public = True
        report.save(update_fields=['is_public'])
        share_url = request.build_absolute_uri(report.share_url)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'share_url': share_url})
        messages.success(request, 'Report sharing link is now active.')
        return redirect('vehicles:report_detail', pk=pk)


class ReportPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        report = get_object_or_404(
            VehicleReport,
            pk=pk,
            user=request.user,
            status=VehicleReport.COMPLETED,
        )
        if not report.pdf_file:
            from apps.reports.generators import generate_pdf
            generate_pdf(report)
            report.refresh_from_db()

        if report.pdf_file:
            response = HttpResponse(
                report.pdf_file.read(),
                content_type='application/pdf',
            )
            response['Content-Disposition'] = (
                f'attachment; filename="carhaki-report-'
                f'{report.search.identifier}.pdf"'
            )
            return response

        messages.error(
            request,
            'PDF could not be generated. Please contact support.',
        )
        return redirect('vehicles:report_detail', pk=pk)


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class PricingView(TemplateView):
    template_name = 'pages/pricing.html'


class FAQView(TemplateView):
    template_name = 'pages/faq.html'

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
        grouped: dict = {}
        for faq in faqs:
            cat = faq.get_category_display()
            grouped.setdefault(cat, []).append(faq)
        ctx['faq_groups'] = grouped
        return ctx


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class    = ContactForm
    success_url   = '/contact/?sent=1'

    def form_valid(self, form):
        msg = form.save()
        self._send_autoreply(msg)
        self._notify_admin(msg)
        messages.success(
            self.request,
            'Thank you for your message. We will respond within 4 business hours.',
        )
        return super().form_valid(form)

    def _send_autoreply(self, msg):
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            body = render_to_string(
                'emails/contact_autoreply.html', {'message': msg}
            )
            send_mail(
                subject='We received your message - CarHaki',
                message=(
                    f'Dear {msg.name},\n\n'
                    'Thank you for contacting CarHaki. '
                    'We will respond within 4 business hours.\n\n'
                    'CarHaki Support Team'
                ),
                from_email=None,
                recipient_list=[msg.email],
                html_message=body,
                fail_silently=True,
            )
        except Exception:
            pass

    def _notify_admin(self, msg):
        try:
            from django.core.mail import mail_admins
            mail_admins(
                subject=f'New contact: {msg.get_subject_display()} from {msg.name}',
                message=(
                    f'Name: {msg.name}\n'
                    f'Email: {msg.email}\n'
                    f'Phone: {msg.phone}\n\n'
                    f'{msg.message}'
                ),
                fail_silently=True,
            )
        except Exception:
            pass

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sent'] = self.request.GET.get('sent') == '1'
        return ctx


class TermsView(TemplateView):
    template_name = 'pages/terms.html'


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'
