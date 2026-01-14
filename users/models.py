from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Team Manager'),
        ('agent', 'Agent'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')
    force_password_change = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
