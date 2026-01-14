from rest_framework.views import APIView
from rest_framework import serializers, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django_tenants.utils import schema_context
from tenants.models import Client
from .models import Call, Queue, CallVolume, RealTimeEvent, IntegrationConfig
from datetime import datetime
from django.shortcuts import get_object_or_404
from .integrations.connectors import handle_incoming_event

class WebhookReceiverView(APIView):
    # Deprecated - kept for backward compat if needed, but we will redirect logic
    authentication_classes = [] 
    permission_classes = [permissions.AllowAny] 

    def post(self, request, format=None):
        return Response({"error": "Use /api/v1/event/push/ with X-API-Key"}, status=status.HTTP_410_GONE)

class IntegrationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConfig
        fields = ['id', 'name', 'type', 'api_url', 'api_key', 'enabled']

class IntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = IntegrationConfig.objects.all()
    serializer_class = IntegrationConfigSerializer
    permission_classes = [permissions.IsAdminUser]

class EventPushViewSet(viewsets.ViewSet):
    """
    Endpoint for external PBX systems to push events.
    Auth: API Key in header 'X-API-Key'
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny] # We handle auth via API Key manually

    def create(self, request):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return Response({'error': 'Missing API Key'}, status=status.HTTP_401_UNAUTHORIZED)
        
        config = IntegrationConfig.objects.filter(api_key=api_key, enabled=True).first()
        if not config:
            return Response({'error': 'Invalid API Key'}, status=status.HTTP_401_UNAUTHORIZED)
            
        event = handle_incoming_event(config, request.data)
        
        if event:
            return Response({'status': 'received', 'event_id': event.id}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Processing failed'}, status=status.HTTP_400_BAD_REQUEST)
