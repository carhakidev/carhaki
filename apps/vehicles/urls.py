from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('reports/sample/', RedirectView.as_view(pattern_name='vehicles:search', permanent=False), name='sample_report'),
    path('preview/<str:identifier>/', views.PreviewView.as_view(), name='preview'),
    path('reports/<uuid:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<uuid:pk>/share/', views.ShareReportView.as_view(), name='report_share'),
    path('reports/shared/<uuid:token>/', views.SharedReportView.as_view(), name='report_shared'),
    path('reports/<uuid:pk>/pdf/', views.ReportPDFView.as_view(), name='report_pdf'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('faq/', views.FAQView.as_view(), name='faq'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('dealers/', views.DealersView.as_view(), name='dealers'),
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
]
