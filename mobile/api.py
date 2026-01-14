
from rest_framework import serializers, viewsets, permissions, status
from shifts.models import Shift, ShiftChangeRequest, Notification
from calls.models import Queue, Call
from agents.models import AgentProfile
from users.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date
from django.db.models import Sum, Count

# Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']

class ShiftSerializer(serializers.ModelSerializer):
    # Shift model has start_time and end_time directly now
    class Meta:
        model = Shift
        fields = ['id', 'date', 'start_time', 'end_time', 'is_published']

class ShiftChangeRequestSerializer(serializers.ModelSerializer):
    shift_detail = ShiftSerializer(source='shift', read_only=True)
    class Meta:
        model = ShiftChangeRequest
        fields = ['id', 'shift', 'shift_detail', 'target_agent', 'request_type', 'status', 'reason', 'created_at']
        read_only_fields = ['status', 'created_at', 'requestor']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'created_at']

class AgentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = AgentProfile
        fields = ['id', 'user', 'employee_id', 'team']

# ViewSets
class MobileShiftViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints for mobile app to fetch schedules
    """
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'agent_profile'):
            return Shift.objects.filter(agent=user.agent_profile, is_published=True).order_by('date')
        return Shift.objects.none()

class MobileShiftChangeRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftChangeRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'agent_profile'):
            return ShiftChangeRequest.objects.filter(requestor=user.agent_profile).order_by('-created_at')
        return ShiftChangeRequest.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'agent_profile'):
            serializer.save(requestor=user.agent_profile)

class MobileNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class MobileTeamShiftViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show shifts of other agents in the same team? 
        # For now, let's just show all published shifts for today/future
        # Ideally filter by Team
        return Shift.objects.filter(is_published=True, date__gte=date.today()).order_by('date')

class MobileDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        today = date.today()
        user = request.user
        
        data = {
            'username': user.username,
            'today': today.strftime("%Y-%m-%d"),
            'next_shift': None,
            'unread_notifications': Notification.objects.filter(user=user, is_read=False).count()
        }
        
        if hasattr(user, 'agent_profile'):
             next_shift = Shift.objects.filter(
                 agent=user.agent_profile, 
                 date__gte=today,
                 is_published=True
             ).order_by('date').first()
             
             if next_shift:
                 data['next_shift'] = {
                     'date': next_shift.date,
                     'start': next_shift.start_time,
                     'end': next_shift.end_time
                 }
                 
        return Response(data)

class MobileAdminViewSet(viewsets.ViewSet):
    """
    For Supervisors/Admins on mobile
    """
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        # Implementation of admin stats
        return Response({})
