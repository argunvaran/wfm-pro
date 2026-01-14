
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# Setup Django Environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django_tenants.utils import schema_context
from agents.models import AgentProfile
from calls.models import RealTimeAgentState
from tenants.models import Client

def generate_mock_rta(tenant_name='public'):
    """
    Updates RealTimeAgentState for all agents with random valid/invalid states
    to simulate a live call center.
    """
    try:
        client = Client.objects.get(schema_name=tenant_name)
    except Client.DoesNotExist:
        print(f"Tenant {tenant_name} not found.")
        return

    with schema_context(client.schema_name):
        agents = AgentProfile.objects.all()
        print(f"Simulating RTA for {agents.count()} agents in {tenant_name}...")
        
        start_states = ['READY', 'TALKING', 'BREAK', 'OFFLINE', 'AUX', 'PAUSE']
        
        for agent in agents:
            # 80% chance to be Adherent (Good state), 20% Non-Adherent
            # For simplicity, just random states now, let the dashboard calculate logic.
            
            new_state = random.choice(start_states)
            
            # Update or Create
            state_obj, created = RealTimeAgentState.objects.get_or_create(agent_profile=agent, defaults={'since': timezone.now()})
            
            # Chance to keep same state (simulate duration) or change
            if random.random() > 0.7: 
                state_obj.state = new_state
                state_obj.since = timezone.now() # Reset timer
            
            state_obj.save()
            print(f"Updated {agent}: {state_obj.state}")

if __name__ == "__main__":
    # Default to mobile_test or public
    generate_mock_rta('mobile_test') 
