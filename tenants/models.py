from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    paid_until = models.DateField(null=True, blank=True)
    
    # Testing feature: Allow creating a tenant freely
    is_test_tenant = models.BooleanField(default=False)

    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass

class TenantAwareModel(models.Model):
    # No longer needed to have explicit tenant FK with schema isolation
    pass

    class Meta:
        abstract = True
