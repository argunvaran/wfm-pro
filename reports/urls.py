from django.urls import path
from .views import report_dashboard, agent_performance_report, sla_report, adherence_report, customer_journey_report, queue_performance_report, hourly_traffic_report

urlpatterns = [
    path('', report_dashboard, name='report_dashboard'),
    path('agent-performance/', agent_performance_report, name='agent_performance_report'),
    path('sla/', sla_report, name='sla_report'),
    path('adherence/', adherence_report, name='adherence_report'),
    path('customer-journey/', customer_journey_report, name='customer_journey_report'),
    path('queue-performance/', queue_performance_report, name='queue_performance_report'),
    path('hourly-traffic/', hourly_traffic_report, name='hourly_traffic_report'),
]
