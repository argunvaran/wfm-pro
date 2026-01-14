
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    MobileShiftViewSet, MobileDashboardViewSet, MobileAdminViewSet,
    MobileShiftChangeRequestViewSet, MobileNotificationViewSet, MobileTeamShiftViewSet
)
from .views import mobile_app_view, manifest_view

router = DefaultRouter()
router.register(r'shifts', MobileShiftViewSet, basename='mobile-shifts')
router.register(r'requests', MobileShiftChangeRequestViewSet, basename='mobile-requests')
router.register(r'notifications', MobileNotificationViewSet, basename='mobile-notifications')
router.register(r'team-shifts', MobileTeamShiftViewSet, basename='mobile-team-shifts')
router.register(r'dashboard', MobileDashboardViewSet, basename='mobile-dashboard')
router.register(r'admin', MobileAdminViewSet, basename='mobile-admin')

urlpatterns = [
    path('', mobile_app_view, name='mobile_app'),
    path('manifest.json', manifest_view, name='mobile_manifest'),
    path('api/', include(router.urls)),
]
