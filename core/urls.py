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
    path('api/exercises-by-type/', views.get_exercises_by_type, name='get_exercises_by_type'),

    # --- Nutrition ---
    path('nutrition/', views.diet_list, name='diet_list'),
    path('nutrition/log/', views.diet_create, name='diet_create'),
    path('nutrition/foods/', views.food_library, name='food_library'), # To add new foods
    path('nutrition/<int:pk>/', views.diet_detail, name='diet_detail'),
    path('nutrition/<int:pk>/delete/', views.diet_delete, name='diet_delete'),

    # core/urls.py

    # --- Academics & Internship ---
    path('academics/', views.academics_dashboard, name='academics_dashboard'),
    path('academics/study/log/', views.study_session_create, name='study_session_create'),
    path('academics/course/add/', views.course_create, name='course_create'),
    path('academics/project/add/', views.project_create, name='project_create'),
    path('academics/internship/log/', views.internship_log_create, name='internship_log_create'),

    path('academics/study/<int:pk>/edit/', views.study_session_update, name='study_session_update'),
    path('academics/study/<int:pk>/delete/', views.study_session_delete, name='study_session_delete'),
    
    path('academics/course/<int:pk>/edit/', views.course_update, name='course_update'),
    path('academics/course/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    path('academics/project/<int:pk>/edit/', views.project_update, name='project_update'),
    path('academics/project/<int:pk>/delete/', views.project_delete, name='project_delete'),
    
    path('academics/internship/<int:pk>/edit/', views.internship_log_update, name='internship_log_update'),
    path('academics/internship/<int:pk>/delete/', views.internship_log_delete, name='internship_log_delete'),
]
