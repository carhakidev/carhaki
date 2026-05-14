"""
accounts/views.py

All account-related views for CarHaki.

FIXES APPLIED IN THIS FILE:
  1. Added PasswordChangeView — was missing, caused NoReverseMatch on dashboard.
  2. ProfileView.form_valid() now redirects to dealer_register when user
     switches account_type to DEALER (signal creates the profile shell,
     view handles the redirect).
  3. DashboardView.get_context_data() now supplies clean_count, issues_count,
     total_spent, and has_processing_reports so the dashboard template stats
     row and auto-refresh script work correctly.
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, UpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages

from .models import CustomUser, DealerProfile
from .forms import CustomUserCreationForm, DealerProfileForm, CustomUserUpdateForm


# ---------------------------------------------------------------------------
# Registration & Auth
# ---------------------------------------------------------------------------

class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Welcome to CarHaki! Your account has been created.')
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')


class LogoutView(auth_views.LogoutView):
    next_page = 'core:home'


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        reports = user.reports.select_related('search').order_by('-created_at')[:10]
        orders  = user.orders.order_by('-created_at')[:10]

        ctx['reports'] = reports
        ctx['orders']  = orders

        # *** FIX APPLIED ***
        # Dashboard template references clean_count, issues_count, total_spent,
        # and has_processing_reports — these were missing from the context,
        # causing the stats row to always show 0 and auto-refresh to never fire.
        all_reports = user.reports.all()

        ctx['clean_count']  = all_reports.filter(overall_grade__in=['A', 'B']).count()
        ctx['issues_count'] = all_reports.filter(overall_grade__in=['D', 'E', 'F']).count()

        from apps.payments.models import Order
        completed_orders = user.orders.filter(payment_status=Order.COMPLETED)
        total_ugx = sum(o.amount_ugx for o in completed_orders if o.amount_ugx)
        ctx['total_spent'] = f'{int(total_ugx):,}' if total_ugx else '0'

        ctx['has_processing_reports'] = all_reports.filter(
            status='PROCESSING'
        ).exists()

        return ctx


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully.')

        # *** FIX APPLIED ***
        # When the user switches their account_type to DEALER, the signal
        # (signals.py) creates a blank DealerProfile shell.  Here we redirect
        # them to dealer_register to fill in their business details — unless
        # they already have an approved DealerProfile, in which case go straight
        # to the dealer dashboard.
        user = self.request.user
        if user.account_type == CustomUser.DEALER:
            try:
                profile = user.dealer_profile
                if not profile.business_name:
                    # Shell profile exists but not filled in yet
                    return redirect('accounts:dealer_register')
                return redirect('accounts:dealer_dashboard')
            except DealerProfile.DoesNotExist:
                return redirect('accounts:dealer_register')

        return response


# ---------------------------------------------------------------------------
# Dealer
# ---------------------------------------------------------------------------

class DealerRegisterView(LoginRequiredMixin, CreateView):
    model = DealerProfile
    form_class = DealerProfileForm
    template_name = 'accounts/dealer_register.html'
    success_url = reverse_lazy('accounts:dealer_dashboard')

    def dispatch(self, request, *args, **kwargs):
        # If user already has an approved DealerProfile, skip registration
        if request.user.is_authenticated:
            try:
                profile = request.user.dealer_profile
                if profile.business_name and profile.is_approved:
                    return redirect('accounts:dealer_dashboard')
            except DealerProfile.DoesNotExist:
                pass
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.request.user.account_type = CustomUser.DEALER
        self.request.user.save(update_fields=['account_type'])
        messages.success(
            self.request,
            'Dealer profile submitted for approval. '
            'We will review your application and notify you within 1 business day.'
        )
        return super().form_valid(form)


class DealerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dealer_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx['reports']              = user.reports.select_related('search').order_by('-created_at')[:10]
        ctx['completed_count']      = user.reports.filter(status='COMPLETED').count()
        ctx['total_reports_count']  = user.reports.count()
        ctx['orders_count']         = user.orders.count()

        try:
            ctx['dealer_profile'] = user.dealer_profile
        except DealerProfile.DoesNotExist:
            ctx['dealer_profile'] = None

        return ctx


# ---------------------------------------------------------------------------
# Password Reset (email-based, no login required)
# ---------------------------------------------------------------------------

class PasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'emails/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


# ---------------------------------------------------------------------------
# Password Change (requires login)
# *** FIX APPLIED ***
# This view was referenced in dashboard.html as {% url 'accounts:change_password' %}
# but was never defined in views.py or urls.py. Adding it here and in urls.py
# fixes the NoReverseMatch crash on the dashboard page.
# ---------------------------------------------------------------------------

class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'