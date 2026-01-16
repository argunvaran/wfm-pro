from django.db import models
from tenants.models import TenantAwareModel
from agents.models import AgentProfile

class Shift(TenantAwareModel):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='shifts')
    shift_type = models.ForeignKey('agents.ShiftType', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_start = models.TimeField(null=True, blank=True)
    break_duration = models.IntegerField(default=60) # minutes
    is_published = models.BooleanField(default=False)

    def populate_activities(self):
        from datetime import datetime, date, timedelta, time
        # Helper to do time math
        def add_time(t, delta):
            dt = datetime.combine(date.today(), t) + delta
            return dt.time()
        
        def diff_minutes(t1, t2):
            dt1 = datetime.combine(date.today(), t1)
            dt2 = datetime.combine(date.today(), t2)
            return (dt2 - dt1).total_seconds() / 60

        # Clear existing
        self.activities.all().delete()

        # Check for ShiftType Template
        if self.shift_type and self.shift_type.template_activities.exists():
            # Dynamic Logic
            cursor = self.start_time
            # Get defined breaks/lunches (and maybe explicit work blocks)
            templates = self.shift_type.template_activities.all().order_by('start_offset_minutes')
            
            for tmpl in templates:
                # Calculate activity start/end
                act_start = add_time(self.start_time, timedelta(minutes=tmpl.start_offset_minutes))
                act_end = add_time(act_start, timedelta(minutes=tmpl.duration_minutes))
                
                # 1. Fill gap with WORK if gap > 0
                if diff_minutes(cursor, act_start) > 0:
                    ShiftActivity.objects.create(
                        shift=self, 
                        activity_type='WORK', 
                        start_time=cursor, 
                        end_time=act_start
                    )
                
                # 2. Create the defined activity
                ShiftActivity.objects.create(
                    shift=self,
                    activity_type=tmpl.activity_type,
                    start_time=act_start,
                    end_time=act_end
                )
                
                # Move cursor
                cursor = act_end
            
            # 3. Fill remaining time with WORK
            if diff_minutes(cursor, self.end_time) > 0:
                ShiftActivity.objects.create(
                     shift=self,
                     activity_type='WORK',
                     start_time=cursor,
                     end_time=self.end_time
                )
        else:
            # Fallback: Hardcoded Standard Logic
            # 1. Work: Start -> Start + 3h
            t1_end = add_time(self.start_time, timedelta(hours=3))
            ShiftActivity.objects.create(shift=self, activity_type='WORK', start_time=self.start_time, end_time=t1_end)
            
            # 2. Lunch: 1h
            t2_end = add_time(t1_end, timedelta(hours=1))
            ShiftActivity.objects.create(shift=self, activity_type='LUNCH', start_time=t1_end, end_time=t2_end)
            
            # 3. Work: Lunch End -> Start + 6h
            t3_end = add_time(self.start_time, timedelta(hours=6))
            ShiftActivity.objects.create(shift=self, activity_type='WORK', start_time=t2_end, end_time=t3_end)
            
            # 4. Break: 15min
            t4_end = add_time(t3_end, timedelta(minutes=15))
            ShiftActivity.objects.create(shift=self, activity_type='BREAK', start_time=t3_end, end_time=t4_end)
            
            # 5. Work: Break End -> End
            # If break end is before end time, add final work block
            if t4_end < self.end_time:
                ShiftActivity.objects.create(shift=self, activity_type='WORK', start_time=t4_end, end_time=self.end_time)

    @property
    def shift_name(self):
        h = self.start_time.hour
        if h < 10:
            return "Sabah"
        elif h < 16:
            return "Öğlen"
        else:
            return "Akşam"

    def duration(self):
        from datetime import datetime, date
        d1 = datetime.combine(date.today(), self.start_time)
        d2 = datetime.combine(date.today(), self.end_time)
        return (d2 - d1).total_seconds() / 3600

    def __str__(self):
        return f"{self.agent} - {self.date}"

class ShiftActivity(TenantAwareModel):
    ACTIVITY_TYPES = (
        ('WORK', 'Work'),
        ('BREAK', 'Break'),
        ('LUNCH', 'Lunch'),
        ('MEETING', 'Meeting'),
        ('TRAINING', 'Training'),
    )
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.activity_type} ({self.start_time} - {self.end_time})"

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
