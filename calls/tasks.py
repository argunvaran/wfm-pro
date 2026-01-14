from celery import shared_task
from django_tenants.utils import schema_context
from .models import Call, Queue
from tenants.models import Client
from datetime import datetime

@shared_task
def process_webhook_call(tenant_schema, call_data):
    """
    Async task to process webhook data.
    """
    with schema_context(tenant_schema):
        call_id = call_data.get('call_id')
        duration = call_data.get('duration', 0)
        queue_name = call_data.get('queue')
        ts_str = call_data.get('timestamp')
        
        try:
            ts = datetime.fromisoformat(ts_str)
        except:
            ts = datetime.now()

        # Find or Create Queue
        queue_obj = None
        if queue_name:
            queue_obj, _ = Queue.objects.get_or_create(name=queue_name)

        Call.objects.update_or_create(
            call_id=call_id,
            defaults={
                'timestamp': ts,
                'duration': duration,
                'queue': queue_obj,
            }
        )
    return f"Processed call {call_id} for {tenant_schema}"
