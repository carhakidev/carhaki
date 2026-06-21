from django.contrib.auth import views as auth_views
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, UpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserUpdateForm


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
    next_page = '/'


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

        from apps.payments.models import Order
        all_reports = user.reports.all()

        ctx['clean_count']  = all_reports.filter(overall_grade__in=['A', 'B']).count()
        ctx['issues_count'] = all_reports.filter(overall_grade__in=['D', 'E', 'F']).count()

        total_spent = Order.objects.filter(
            user=user,
            payment_status=Order.COMPLETED,
        ).aggregate(total=Sum('amount_ngn'))['total'] or 0
        ctx['total_spent'] = f'{int(total_spent):,}'

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
        return response


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
# ---------------------------------------------------------------------------

class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'
