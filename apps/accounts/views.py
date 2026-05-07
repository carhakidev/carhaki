from django.contrib.auth import views as auth_views
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView, UpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser, DealerProfile
from .forms import CustomUserCreationForm, DealerProfileForm, CustomUserUpdateForm


class RegisterView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(self.request, f'Welcome to CarHaki, {user.first_name}!')
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy('accounts:dashboard')


class LogoutView(auth_views.LogoutView):
    next_page = '/'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['reports'] = user.reports.select_related('search').order_by('-created_at')[:10]
        ctx['orders'] = user.orders.order_by('-created_at')[:10]
        return ctx


class ProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


class DealerRegisterView(LoginRequiredMixin, CreateView):
    model = DealerProfile
    form_class = DealerProfileForm
    template_name = 'accounts/dealer_register.html'
    success_url = reverse_lazy('accounts:dealer_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.request.user.account_type = CustomUser.DEALER
        self.request.user.save(update_fields=['account_type'])
        messages.success(self.request, 'Dealer profile submitted for approval.')
        return super().form_valid(form)


class DealerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dealer_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['reports'] = user.reports.select_related('search').order_by('-created_at')[:10]
        ctx['completed_count'] = user.reports.filter(status='COMPLETED').count()
        ctx['total_reports_count'] = user.reports.count()
        ctx['orders_count'] = user.orders.count()
        return ctx


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
