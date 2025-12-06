# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # --- Dashboard & Entries ---
    path('', views.home_dashboard, name='home'),
    path('entries/', views.entries_view, name='entries'),
    
    # --- Reports ---
    path('report/daily/<str:date>/', views.generate_daily_report, name='daily_report'), 
    path('report/daily/', views.generate_daily_report, name='daily_report_today'),

    # --- Workout Tracking ---
    path('workout/', views.workout_list, name='workout_list'),
    path('workout/add/', views.workout_create, name='workout_create'),
    path('workout/<int:pk>/', views.workout_detail, name='workout_detail'),
    path('workout/<int:pk>/edit/', views.workout_update, name='workout_update'),
    path('workout/<int:pk>/delete/', views.workout_delete, name='workout_delete'),
]