import re
import logging

from django.views.generic import TemplateView, FormView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.conf import settings

from .models import VehicleSearch, VehicleReport
from .forms import VehicleSearchForm
from apps.integrations.nhtsa import NHTSAProvider
from apps.integrations.cache import VehicleDataCache
from apps.core.models import FAQ
from apps.core.forms import ContactForm, DealerApplicationForm

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
        Fields: identifier, source_country, report_type
        """
        from apps.payments.models import Order

        identifier     = request.POST.get('identifier', '').upper().strip()
        source_country = request.POST.get('source_country', 'JAPAN').upper()
        report_type    = request.POST.get('report_type', 'FULL').upper()

        if not identifier:
            messages.error(request, 'No chassis number provided.')
            return redirect('vehicles:home')

        # Require login — send back to preview after login
        if not request.user.is_authenticated:
            preview_url = reverse(
                'vehicles:preview', kwargs={'identifier': identifier}
            )
            return redirect(
                f"{reverse('accounts:login')}"
                f"?next={preview_url}%3Fcountry%3D{source_country}"
            )

        # Normalise report_type
        valid_types = {Order.BASIC, Order.FULL}
        if report_type not in valid_types:
            report_type = Order.FULL

        try:
            # Try the dedicated service first (may not exist yet)
            try:
                from apps.payments.services import create_order_and_report
                order = create_order_and_report(
                    user=request.user,
                    identifier=identifier,
                    source_country=source_country,
                    report_type=report_type,
                )
            except ImportError:
                # Service doesn't exist yet — create Order directly
                search, _ = VehicleSearch.objects.get_or_create(
                    identifier=identifier,
                    source_country=source_country,
                    defaults={'user': request.user},
                )
                order = Order.objects.create(
                    user=request.user,
                    search=search,
                    report_type=report_type,
                    status=Order.PENDING,
                    amount=self._get_price(report_type),
                    currency='UGX',
                )

            return redirect('payments:checkout', pk=order.pk)

        except Exception as exc:
            logger.exception(
                f'Order creation failed for {identifier}: {exc}'
            )
            messages.error(
                request,
                'Something went wrong creating your order. '
                'Please try again or contact support on WhatsApp.',
            )
            preview_url = reverse(
                'vehicles:preview', kwargs={'identifier': identifier}
            )
            return redirect(f'{preview_url}?country={source_country}')

    @staticmethod
    def _get_price(report_type):
        """Return price in UGX based on report type."""
        from apps.payments.models import Order
        prices = {
            Order.BASIC: 25000,
            Order.FULL:  50000,
        }
        return prices.get(report_type, 25000)


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

    def _fetch_japan_preview(self, identifier):
        """
        Calls the OtoFacts /check endpoint (free — no credits deducted).
        Returns dict for template context.
        """
        import requests as req

        api_key = getattr(settings, 'OTOFACTS_API_KEY', '')
        if not api_key:
            return {
                'is_japan':  True,
                'identifier': identifier,
                'available':  False,
                'error':      'OtoFacts API key not configured.',
            }

        try:
            resp = req.get(
                'https://api.otofacts.com/v3/report/check/basic/jp',
                params={'query': identifier},
                headers={
                    'X-API-Key': api_key,
                    'Accept':    'application/json',
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

            logger.warning(
                f'OtoFacts check returned {resp.status_code} for {identifier}'
            )
            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'api_status': resp.status_code,
            }

        except req.exceptions.Timeout:
            logger.warning(f'OtoFacts timeout for {identifier}')
            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'error':      'OtoFacts timed out. Please try again.',
            }
        except Exception as exc:
            logger.exception(f'OtoFacts error for {identifier}: {exc}')
            return {
                'is_japan':   True,
                'identifier': identifier,
                'available':  False,
                'error':      str(exc),
            }

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
        ctx            = super().get_context_data(**kwargs)
        identifier     = self.kwargs['identifier'].upper()
        source_country = self.request.GET.get('country', 'AUTO').upper()

        # Auto-detect: 17-char alphanumeric → USA VIN, anything else → Japan
        if source_country == 'AUTO':
            source_country = 'USA' if self._is_usa_vin(identifier) else 'JAPAN'

        ctx['identifier']       = identifier
        ctx['source_country']   = source_country
        ctx['is_japan_preview'] = (source_country == 'JAPAN')
        ctx['search_form']      = VehicleSearchForm(
            initial={'identifier': identifier}
        )
        # Pricing shown on preview CTA buttons
        ctx['BASIC_PRICE_UGX']  = '25,000'
        ctx['FULL_PRICE_UGX']   = '50,000'

        if source_country == 'JAPAN':
            ctx['vehicle_data'] = self._fetch_japan_preview(identifier)
        else:
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


class DealersView(FormView):
    template_name = 'pages/dealers.html'
    form_class    = DealerApplicationForm
    success_url   = '/dealers/?applied=1'

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
                    f'and will review it within 2 business days.\n\nCarHaki Team'
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
        ctx['applied']        = self.request.GET.get('applied') == '1'
        ctx['dealer_bundles'] = [
            {
                'name':             'Starter Pack',
                'reports':          10,
                'price_ugx':        600000,
                'price_per_report': 60000,
                'saving_ugx':       150000,
                'highlight':        False,
            },
            {
                'name':             'Growth Pack',
                'reports':          25,
                'price_ugx':        1250000,
                'price_per_report': 50000,
                'saving_ugx':       625000,
                'highlight':        True,
            },
            {
                'name':             'Pro Pack',
                'reports':          50,
                'price_ugx':        2000000,
                'price_per_report': 40000,
                'saving_ugx':       1750000,
                'highlight':        False,
            },
            {
                'name':             'Enterprise Pack',
                'reports':          100,
                'price_ugx':        3500000,
                'price_per_report': 35000,
                'saving_ugx':       4000000,
                'highlight':        False,
            },
        ]
        return ctx


class TermsView(TemplateView):
    template_name = 'pages/terms.html'


class PrivacyView(TemplateView):
    template_name = 'pages/privacy.html'