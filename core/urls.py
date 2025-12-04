# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_dashboard, name='home'),
    path('report/daily/<str:date>/', views.generate_daily_report, name='daily_report'), 
    path('report/daily/', views.generate_daily_report, name='daily_report_today'),     
    path('entries/', views.entries_view, name='entries'),
]
