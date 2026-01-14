from django.db import models
from tenants.models import TenantAwareModel
from agents.models import AgentProfile

class Shift(TenantAwareModel):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_duration = models.IntegerField(default=60) # minutes
    is_published = models.BooleanField(default=False)

    def duration(self):
        # Calculation logic needed here later
        pass

    def __str__(self):
        return f"{self.agent} - {self.date}"

class Adherence(TenantAwareModel):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status_choices = (
        ('available', 'Available'),
        ('on_call', 'On Call'),
        ('break', 'Break'),
        ('offline', 'Offline'),
    )
    status = models.CharField(max_length=20, choices=status_choices)

class ShiftChangeRequest(TenantAwareModel):
    REQUEST_TYPES = (
        ('swap', 'Swap Shift'),
        ('off', 'Request Off'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    requestor = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='sent_requests')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='change_requests')
    target_agent = models.ForeignKey(AgentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_requests')
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.request_type} - {self.requestor} ({self.status})"

class Notification(TenantAwareModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user}"
