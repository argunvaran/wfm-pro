import os
import sys
import django
import time
import random
import requests
import json
from datetime import datetime

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wfm_core.settings')
django.setup()

from django_tenants.utils import schema_context
from calls.models import IntegrationConfig
from agents.models import AgentProfile

API_URL = 'http://127.0.0.1:8000/api/v1/event/push/'
API_KEY = 'sim-key-123'
tenant_schema = 'tenant4e7c96'
tenant_domain = 'tenant4e7c96.localhost'



def ensure_config():
    """Ensure the IntegrationConfig exists for the simulator."""
    with schema_context(tenant_schema):
        config, created = IntegrationConfig.objects.get_or_create(
            name='Simulator',
            defaults={
                'type': 'generic',
                'api_key': API_KEY,
                'enabled': True
            }
        )
        if not config.enabled:
            config.enabled = True
            config.save()
            print("Enabled existing Simulator config.")
        elif created:
            print(f"Created new Simulator config with key: {API_KEY}")
        else:
            print(f"Using existing Simulator config.")
            
        # Ensure API Key matches what we use
        if config.api_key != API_KEY:
            config.api_key = API_KEY
            config.save()
            print(f"Updated API Key to: {API_KEY}")

from users.models import User

def ensure_agents():
    """Ensure at least a few agents exist for simulation."""
    with schema_context(tenant_schema):
        # 1. Backfill existing agents with missing IDs
        missing_id_profiles = AgentProfile.objects.filter(employee_id__isnull=True)
        for idx, profile in enumerate(missing_id_profiles, start=1):
            profile.employee_id = f"100{idx}"
            profile.save()
            print(f"Backfilled ID for {profile.user.username}: {profile.employee_id}")

        # 2. If still no agents with IDs, create some
        if not AgentProfile.objects.exclude(employee_id__isnull=True).exists():
            print("No valid agents found. Creating dummy agents...")
            for i in range(1, 6):
                username = f"agent{i}"
                email = f"agent{i}@example.com"
                user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'role': 'agent', 'first_name': f'Agent', 'last_name': f'{i}'})
                if created:
                    user.set_password('password')
                    user.save()
                
                profile, _ = AgentProfile.objects.get_or_create(user=user, defaults={
                    'employee_id': f"200{i}" # Use 200 series for new ones
                })
                # Ensure employee_id is set if it was missing
                if not profile.employee_id:
                    profile.employee_id = f"200{i}"
                    profile.save()
            print("Created 5 dummy agents.")

def get_agent_ids():
    ensure_agents()
    with schema_context(tenant_schema):
        agents = list(AgentProfile.objects.values_list('employee_id', flat=True))
        # Filter out None
        return [a for a in agents if a]

def generate_event(agent_id):
    states = ['Ready', 'Talking', 'Pause', 'NotReady', 'Offline']
    state = random.choice(states)
    
    payload = {
        "type": "agent_state",
        "agent_id": agent_id,
        "state": state,
        "timestamp": datetime.now().isoformat()
    }
    return payload

def run_simulation():
    ensure_config()
    
    agents = get_agent_ids()
    if not agents:
        print("No agents found with employee_id. Please create some agents first.")
        return

    print(f"Starting simulation for {len(agents)} agents...")
    print(f"Target: {API_URL}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            # Pick a random agent
            agent_id = random.choice(agents)
            event_data = generate_event(agent_id)
            
            headers = {
                'X-API-Key': API_KEY,
                'Content-Type': 'application/json',
                'Host': tenant_domain
            }
            
            try:
                response = requests.post(API_URL, json=event_data, headers=headers)
                if response.status_code in [200, 201]:
                    print(f"[OK] {agent_id} -> {event_data['state']}")
                else:
                    print(f"[FAIL] {response.status_code} - {response.text}")
            except Exception as e:
                print(f"[ERROR] Connection failed: {e}")

            time.sleep(random.uniform(0.5, 2.0)) # Random delay between events

    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    run_simulation()
