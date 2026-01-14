from django.urls import path
from . import views

urlpatterns = [
    path('', views.gamification_dashboard, name='gamification_dashboard'),
]
