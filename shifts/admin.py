from django.contrib import admin
from .models import Shift, ShiftChangeRequest, Notification, Adherence
from django.contrib import messages
from django.db import transaction

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'agent', 'start_time', 'end_time', 'is_published')
    list_filter = ('date', 'is_published', 'agent__team')
    actions = ['publish_shifts']

    def publish_shifts(self, request, queryset):
        rows_updated = queryset.update(is_published=True)
        # Notify agents
        for shift in queryset:
            Notification.objects.create(
                user=shift.agent.user,
                title="Vardiya Yayınlandı",
                message=f"{shift.date} tarihindeki vardiyanız yayınlandı: {shift.start_time}",
            )
        self.message_user(request, f"{rows_updated} shifts published and notifications sent.")
    publish_shifts.short_description = "Seçili vardiyaları yayınla"

@admin.register(ShiftChangeRequest)
class ShiftChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('requestor', 'request_type', 'shift', 'target_agent', 'status', 'created_at')
    list_filter = ('status', 'request_type')
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        count = 0
        with transaction.atomic():
            for req in queryset.filter(status='pending'):
                if req.request_type == 'swap':
                    # Logic: Swap the AGENTS of the two shifts
                    # We need the target agent to have a shift on that day? 
                    # Usually swap means "I take yours, you take mine".
                    # Let's assume the UI enforces picking a specific shift or we find the shift of the target on that day.
                    
                    shift_a = req.shift
                    target = req.target_agent
                    
                    if not target:
                        messages.error(request, f"Request {req.id} has no target agent.")
                        continue

                    # Find target's shift on same day? Or user selected a specific target shift?
                    # Simplified: Find single shift of target on same day
                    shift_b = Shift.objects.filter(agent=target, date=shift_a.date).first()
                    
                    if shift_b:
                        # Perform Swap
                        shift_a.agent, shift_b.agent = shift_b.agent, shift_a.agent
                        shift_a.save()
                        shift_b.save()
                        
                        Notification.objects.create(user=req.requestor.user, title="Takas Onaylandı", message="Vardiya takas talebiniz onaylandı.")
                        Notification.objects.create(user=target.user, title="Takas Onaylandı", message=f"{req.requestor} ile vardiya takasınız onaylandı.")
                        count += 1
                    else:
                        messages.error(request, f"Target agent {target} has no shift on {shift_a.date} to swap.")
                        continue
                        
                elif req.request_type == 'off':
                    # Logic: Delete shift or mark unavailable
                    shift = req.shift
                    date_ref = shift.date
                    shift.delete()
                    Notification.objects.create(user=req.requestor.user, title="İzin Onaylandı", message=f"{date_ref} tarihi için izin talebiniz onaylandı.")
                    count += 1

                req.status = 'approved'
                req.save()
        
        self.message_user(request, f"{count} requests approved and processed.")

    def reject_requests(self, request, queryset):
        for req in queryset.filter(status='pending'):
            req.status = 'rejected'
            req.save()
            Notification.objects.create(user=req.requestor.user, title="Talep Reddedildi", message="Vardiya talebiniz reddedildi.")
        self.message_user(request, "Selected requests rejected.")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')

@admin.register(Adherence)
class AdherenceAdmin(admin.ModelAdmin):
    list_display = ('agent', 'status', 'timestamp')

