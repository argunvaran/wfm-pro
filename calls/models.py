from django.db import models
from tenants.models import TenantAwareModel
from agents.models import Skill

class Queue(TenantAwareModel):
    name = models.CharField(max_length=100)
    required_skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    sla_target_seconds = models.IntegerField(default=20) # e.g., 80/20 rule
    sla_target_percent = models.FloatField(default=0.8)

    def __str__(self):
        return self.name

class CallVolume(TenantAwareModel):
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE)
    date = models.DateField()
    interval_start = models.TimeField() # Start of the 15/30/60 min interval
    calls_offered = models.IntegerField(default=0)
    aht_seconds = models.IntegerField(default=180) # Average Handle Time
    is_forecast = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'interval_start']

class Call(TenantAwareModel):
    call_id = models.CharField(max_length=100, unique=True)
    timestamp = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in seconds")
    queue = models.ForeignKey(Queue, on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey('agents.AgentProfile', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.call_id

class IntegrationConfig(TenantAwareModel):
    INTEGRATION_TYPES = (
        ('generic', 'Generic API'),
        ('avaya', 'Avaya AES'),
        ('genesys', 'Genesys PureCloud'),
        ('cisco', 'Cisco Finesse'),
        ('alcatel', 'Alcatel-Lucent'),
    )
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=INTEGRATION_TYPES, default='generic')
    api_url = models.URLField(blank=True, null=True, help_text="Endpoint to push/pull data")
    api_key = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"

class RealTimeEvent(TenantAwareModel):
    EVENT_TYPES = (
        ('agent_state', 'Agent State Change'),
        ('call', 'Call Event'),
        ('queue', 'Queue Metric'),
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    
    # Normalized Data
    agent_id = models.CharField(max_length=50, blank=True, null=True) # Employee ID or similar
    queue_id = models.CharField(max_length=50, blank=True, null=True) # Queue Name/ID
    
    # Flexible Payload
    payload = models.JSONField(help_text="Normalized Event Data")
    raw_data = models.JSONField(blank=True, null=True, help_text="Raw Vendor Data")

    class Meta:
        ordering = ['-timestamp']

class RealTimeAgentState(TenantAwareModel):
    """Snapshot of current agent state"""
    agent_profile = models.OneToOneField('agents.AgentProfile', on_delete=models.CASCADE, related_name='live_state')
    state = models.CharField(max_length=50) # Ready, NotReady, Talking
    since = models.DateTimeField()
    reason_code = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.agent_profile} - {self.state}"
