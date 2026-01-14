from django.db import models
from tenants.models import TenantAwareModel
from django.conf import settings

class Team(TenantAwareModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

class Skill(TenantAwareModel):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class ShiftType(TenantAwareModel):
    name = models.CharField(max_length=50) # e.g. "09-18 Standard", "Part-Time Morning"
    start_time_min = models.TimeField(default="08:00")
    start_time_max = models.TimeField(default="10:00")
    duration_hours = models.FloatField(default=9.0) # Total duration including break
    paid_hours = models.FloatField(default=8.0) # Actual work hours
    
    def __str__(self):
        return self.name

class AgentProfile(TenantAwareModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agent_profile')
    employee_id = models.CharField(max_length=20, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    shift_type = models.ForeignKey(ShiftType, on_delete=models.SET_NULL, null=True, blank=True)
    skills = models.ManyToManyField(Skill, through='AgentSkill')
    hire_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class AgentSkill(TenantAwareModel):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.IntegerField(default=1) # 1-5 proficiency

    class Meta:
        unique_together = ('agent', 'skill')
