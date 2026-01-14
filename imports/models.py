from django.db import models
from tenants.models import TenantAwareModel
from django.conf import settings

class ImportJob(TenantAwareModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='imports/')
    import_type = models.CharField(max_length=50, choices=[('calls', 'Call Data'), ('agents', 'Agent List')])
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    logs = models.TextField(blank=True)
