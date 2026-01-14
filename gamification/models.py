from django.db import models
from tenants.models import TenantAwareModel
from users.models import User

class Badge(TenantAwareModel):
    CONDITION_CHOICES = (
        ('manual', 'Manuel Verilen'),
        ('first_call', 'İlk Çağrı'),
        ('100_calls', '100 Çağrı Uzmanı'),
        ('perfect_week', 'Kusursuz Hafta'),
        ('speed_demon', 'Hız Canavarı (AHT < 3dk)'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-star', help_text="Bootstrap Icon Class")
    condition_type = models.CharField(max_length=50, choices=CONDITION_CHOICES, default='manual')
    points = models.IntegerField(default=10)
    
    def __str__(self):
        return self.name

class UserBadge(TenantAwareModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-awarded_at']
        
    def __str__(self):
        return f"{self.user} - {self.badge}"

