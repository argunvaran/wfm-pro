from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from calls.views import dashboard, forecast_view, heatmap_view, integration_view
from shifts.views import schedule_view, rta_view
from imports.views import import_data
from agents.views import agent_list, settings_view, create_team, create_skill, create_queue
from users.views import CustomLoginView, test_signup
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
    path('integrations/', integration_view, name='integrations'),
    path('reports/', include('reports.urls')),
    path('games/', include('gamification.urls')),
    path('rta/', rta_view, name='rta_view'),
    path('forecast/', forecast_view, name='forecast'),
    path('heatmap/', heatmap_view, name='heatmap'),
    path('billing/', include('billing.urls')),
    path('login/', CustomLoginView.as_view(), name='login'),
    
    path('api/v1/', include(router.urls)), # New Standard API
    
    path('logout/', LogoutView.as_view(), name='logout'),
    path('test-signup/', test_signup, name='test_signup'),
    
    path('schedule/', schedule_view, name='schedule'),
    path('agents/', agent_list, name='agents'),
    path('mobile/', include('mobile.urls')),
    path('imports/', include('imports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
