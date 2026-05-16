import re
from django.views.generic import TemplateView, FormView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from .models import VehicleSearch, VehicleReport
from .forms import VehicleSearchForm
from apps.integrations.nhtsa import NHTSAProvider
from apps.integrations.cache import VehicleDataCache
from apps.core.models import FAQ, ContactMessage
from apps.core.forms import ContactForm, DealerApplicationForm
import logging

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
        Handles Buy Report form submissions from the preview page.
        Both the Japan and USA preview cards POST here with:
          identifier    — chassis number or VIN
          source_country — JAPAN or USA
          report_type   — BASIC or FULL
        """
        from apps.payments.models import Order
        from apps.payments.services import create_order_and_report

        identifier     = request.POST.get('identifier', '').upper().strip()
        source_country = request.POST.get('source_country', 'JAPAN').upper()
        report_type    = request.POST.get('report_type', 'FULL').upper()

        if not identifier:
            messages.error(request, 'No chassis number or VIN provided.')
            return redirect('vehicles:home')

        # Redirect to login, preserving the preview URL so they come back after
        if not request.user.is_authenticated:
            preview_url = reverse(
                'vehicles:preview', kwargs={'identifier': identifier}
            )
            login_url = reverse('accounts:login')
            return redirect(
                f'{login_url}?next={preview_url}%3Fcountry%3D{source_country}'
            )

        # Normalise report_type to match Order model constants
        if report_type not in (Order.BASIC, Order.FULL):
            report_type = Order.FULL

        try:
            order = create_order_and_report(
                user           = request.user,
                identifier     = identifier,
                source_country = source_country,
                report_type    = report_type,
            )
            return redirect('payments:checkout', pk=order.pk)

        except Exception as exc:
            logger.exception(
                f'create_order_and_report failed for {identifier}: {exc}'
            )
            messages.error(
                request,
                'Something went wrong creating your order. '
                'Please try again or contact support.',
            )
            preview_url = reverse(
                'vehicles:preview', kwargs={'identifier': identifier}
            )
            return redirect(f'{preview_url}?country={source_country}')


class SearchView(FormView):
    template_name = 'vehicles/search.html'
    form_class = VehicleSearchForm

    def get(self, request, *args, **kwargs):
        identifier = (
            request.GET.get('q', '') or
            request.GET.get('identifier', '')
        ).upper().strip()

        if identifier:
            source_country = request.GET.get('source_country', 'AUTO')
            preview_url = reverse(
                'vehicles:preview',
                kwargs={'identifier': identifier}
            )
            return redirect(f'{preview_url}?country={source_country}')

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        identifier = form.cleaned_data['identifier'].upper().strip()
        source_country = form.cleaned_data.get('source_country', 'AUTO')
        preview_url = reverse(
            'vehicles:preview',
            kwargs={'identifier': identifier}
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

    def _fetch_japan_preview(self, identifier):
        import requests as req

        api_key = getattr(settings, 'OTOFACTS_API_KEY', '')
        if not api_key:
            return {
                'is_japan': True,
                'identifier': identifier,
                'available': False,
                'error': 'OtoFacts API key not configured.',
            }

        try:
            resp = req.get(
                'https://api.otofacts.com/v3/report/check/basic/jp',
                params={'query': identifier},
                headers={
                    'X-API-Key': api_key,
                    'Accept': 'application/json',
                },
                timeout=10,
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    'is_japan':   True,
                    'identifier': identifier,
                    'available':  data.get('available', False),
                    'make':       data.get('make', ''),
                    'model':      data.get('model', ''),
                    'year':       data.get('year', ''),
                    'grade':      data.get('grade', ''),
                    'mileage':    data.get('mileage', ''),
                    'color':      data.get('color', ''),
                    'raw':        data,
                }

            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'api_status': resp.status_code,
            }

        except req.exceptions.Timeout:
            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'error':      'OtoFacts timed out. Please try again.',
            }
        except Exception as exc:
            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'error':      str(exc),
            }

    def _fetch_usa_preview(self, identifier):
        cache = VehicleDataCache()
        cached = cache.get_preview(identifier)
        if cached:
            return cached

        try:
            nhtsa = NHTSAProvider()
            data = nhtsa.get_basic_info(identifier)
            cache.set_preview(identifier, data)
            return data
        except Exception as exc:
            return {'error': str(exc)}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        identifier     = self.kwargs['identifier'].upper()
        source_country = self.request.GET.get('country', 'AUTO').upper()

        if source_country == 'AUTO':
            source_country = 'USA' if self._is_usa_vin(identifier) else 'JAPAN'

        ctx['identifier']       = identifier
        ctx['source_country']   = source_country
        ctx['is_japan_preview'] = (source_country == 'JAPAN')
        ctx['search_form']      = VehicleSearchForm(
            initial={'identifier': identifier}
        )

        if source_country == 'JAPAN':
            ctx['vehicle_data'] = self._fetch_japan_preview(identifier)
        else:
            ctx['vehicle_data'] = self._fetch_usa_preview(identifier)
            if ctx['vehicle_data'] and 'error' in ctx['vehicle_data']:
                ctx['error']        = ctx['vehicle_data']['error']
                ctx['vehicle_data'] = None

        return ctx


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = VehicleReport
    template_name = 'reports/detail.html'
    context_object_name = 'report'

    def get_queryset(self):
        return VehicleReport.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.processed_data:
            ctx['data'] = self.object.processed_data
        return ctx


class SharedReportView(DetailView):
    model = VehicleReport
    template_name = 'reports/shared.html'
    context_object_name = 'report'

    def get_object(self):
        token = self.kwargs['token']
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
        ctx = super().get_context_data(**kwargs)
        faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')
        grouped = {}
        for faq in faqs:
            cat = faq.get_category_display()
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(faq)
        ctx['faq_groups'] = grouped
        return ctx


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = '/contact/?sent=1'

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
                'emails/contact_autoreply.html',
                {'message': msg},
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


class DealersView(FormView):
    template_name = 'pages/dealers.html'
    form_class = DealerApplicationForm
    success_url = '/dealers/?applied=1'

    def form_valid(self, form):
        application = form.save()
        self._notify_applicant(application)
        messages.success(
            self.request,
            'Your dealer application has been received. '
            'We will be in touch within 2 business days.',
        )
        return super().form_valid(form)

    def _notify_applicant(self, application):
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            body = render_to_string(
                'emails/dealer_application_email.html',
                {'application': application},
            )
            send_mail(
                subject='Dealer Application Received - CarHaki',
                message=(
                    f'Dear {application.contact_person},\n\n'
                    f'Thank you for applying to become a CarHaki dealer partner. '
                    f'We have received your application for {application.business_name} '
                    f'and will review it within 2 business days.\n\n'
                    'CarHaki Team'
                ),
                from_email=None,
                recipient_list=[application.email],
                html_message=body,
                fail_silently=True,
            )
        except Exception:
            pass

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['applied'] = self.request.GET.get('applied') == '1'
        ctx['dealer_bundles'] = [
            {
                'name': 'Starter Pack',
                'reports': 10,
                'price_ugx': 600000,
                'price_per_report': 60000,
                'saving_ugx': 150000,
                'highlight': False,
            },
            {
                'name': 'Growth Pack',
                'reports': 25,
                'price_ugx': 1250000,
                'price_per_report': 50000,
                'saving_ugx': 625000,
                'highlight': True,
            },
            {
                'name': 'Pro Pack',
                'reports': 50,
                'price_ugx': 2000000,
                'price_per_report': 40000,
                'saving_ugx': 1750000,
                'highlight': False,
            },
            {
                'name': 'Enterprise Pack',
                'reports': 100,
                'price_ugx': 3500000,
                'price_per_report': 35000,
                'saving_ugx': 4000000,
                'highlight': False,
            },
        ]
        return ctx


class TermsView(TemplateView):
    template_name = 'pages/terms.html'


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'