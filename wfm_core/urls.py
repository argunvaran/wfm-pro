from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from calls.views import dashboard, forecast_view, heatmap_view, integration_view, live_monitor_view, live_monitor_partial
from shifts.views import schedule_view, rta_view
from imports.views import import_data
from agents.views import (
    agent_list, settings_view, create_team, create_skill, create_queue, create_shift_type, edit_shift_type,
    org_chart_view, update_hierarchy, create_department, agent_detail_view, user_management_view
)
from users.views import CustomLoginView, register_view
from calls.api import EventPushViewSet, IntegrationConfigViewSet
from mobile.api import MobileShiftViewSet # Example reuse if needed
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'event/push', EventPushViewSet, basename='event-push')
router.register(r'integrations', IntegrationConfigViewSet, basename='integrations')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('settings/', settings_view, name='settings'),
    path('settings/team/add/', create_team, name='create_team'),
    path('settings/skill/add/', create_skill, name='create_skill'),
    path('settings/queue/add/', create_queue, name='create_queue'),
    path('settings/shift-type/add/', create_shift_type, name='create_shift_type'),
    path('settings/shift-type/<int:pk>/', edit_shift_type, name='edit_shift_type'),
    path('org-chart/', org_chart_view, name='org_chart'),
    path('org-chart/update/', update_hierarchy, name='update_hierarchy'),
    path('org-chart/department/add/', create_department, name='create_department'),
    path('users/', user_management_view, name='user_management'), # Added this line
    path('integrations/', integration_view, name='integrations'),
    path('reports/', include('reports.urls')),
    path('games/', include('gamification.urls')),
    path('rta/', rta_view, name='rta_view'),
    path('forecast/', forecast_view, name='forecast'),
    path('heatmap/', heatmap_view, name='heatmap'),
    path('billing/', include('billing.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'), # New Registration
    
    path('api/v1/', include(router.urls)), # New Standard API
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('live-monitor/', live_monitor_view, name='live_monitor'),
    path('live-monitor/partial/', live_monitor_partial, name='live_monitor_partial'),

    path('schedule/', schedule_view, name='schedule'),
    path('agents/', agent_list, name='agents'),
    path('agents/<int:pk>/', agent_detail_view, name='agent_detail'),
    path('mobile/', include('mobile.urls')),
    path('imports/', include('imports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
