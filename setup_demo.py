
import os
import sys
import django
from datetime import date

# Add project root to path
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django_tenants.utils import schema_context
from tenants.models import Client, Domain
import produce_samples
from imports.utils import process_agent_import, process_call_import

def setup():
    # 1. Create Demo Tenant
    tenant_name = 'demo'
    if not Client.objects.filter(schema_name=tenant_name).exists():
        print(f"Creating tenant '{tenant_name}'...")
        client = Client(schema_name=tenant_name, name='Demo Tenant', is_active=True, paid_until=date(2030, 1, 1))
        client.save()
        
        domain = Domain()
        domain.domain = 'demo.localhost'
        domain.tenant = client
        domain.is_primary = True
        domain.save()
        print("Tenant created.")
    else:
        print(f"Tenant '{tenant_name}' already exists.")
        client = Client.objects.get(schema_name=tenant_name)

    # 2. Produce Sample Data
    agents_file = r"c:\Antigravity\import_agents_sample.csv"
    calls_file = r"c:\Antigravity\import_calls_sample.csv"
    
    print("Generating sample CSVs...")
    agents = produce_samples.generate_agents(agents_file)
    produce_samples.generate_calls(calls_file, agents)
    print("Sample CSVs generated.")

    # 3. Import Data into Tenant
    print(f"Importing data into '{tenant_name}' context...")
    with schema_context(tenant_name):
        print("Importing agents...")
        logs = process_agent_import(agents_file)
        print(f"Agent import logs: {len(logs)} entries.")
        
        print("Importing calls...")
        logs = process_call_import(calls_file)
        print(f"Call import logs: {len(logs)} entries.")
        
    print("Setup complete.")

if __name__ == "__main__":
    setup()
