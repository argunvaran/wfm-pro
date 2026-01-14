
import os
import sys
import django
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django_tenants.utils import schema_context
from calls.models import Call
from agents.models import AgentProfile

def check_data():
    tenant_name = 'demo'
    print(f"Checking data for tenant '{tenant_name}'...")
    
    with schema_context(tenant_name):
        agent_count = AgentProfile.objects.count()
        call_count = Call.objects.count()
        
        print(f"Agent Count: {agent_count}")
        print(f"Call Count: {call_count}")
        
        if call_count > 0:
            first_call = Call.objects.order_by('timestamp').first()
            last_call = Call.objects.order_by('timestamp').last()
            print(f"First Call: {first_call.timestamp}")
            print(f"Last Call: {last_call.timestamp}")
        else:
            print("No calls found.")

if __name__ == "__main__":
    check_data()
