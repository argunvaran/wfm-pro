from django.db import models
from tenants.models import Client

class Plan(models.Model):
    name = models.CharField(max_length=50) # Basic, Premium, Enterprise
    description = models.TextField(blank=True, null=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    max_agents = models.IntegerField(default=10)
    max_calls_monthly = models.IntegerField(default=1000)
    max_storage_gb = models.FloatField(default=1.0) # Data limit in GB
    
    def __str__(self):
        return f"{self.name} - {self.price_monthly} TL"

class Subscription(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    start_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    iyzico_subscription_uuid = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.client.name} - {self.plan.name}"
