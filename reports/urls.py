from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_dashboard, name='report_dashboard'),
    path('agent-performance/', views.agent_performance_report, name='report_agent_performance'),
    path('sla/', views.sla_report, name='report_sla'),
]
