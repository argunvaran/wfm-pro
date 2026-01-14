import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

TARGET_DOMAIN = "wfm-pro.com"

print(f"--- STARTING DOMAIN FIXER (Target: {TARGET_DOMAIN}) ---")

for client in Client.objects.all():
    # Get primary domain
    domain_obj = Domain.objects.filter(tenant=client, is_primary=True).first()
    
    if not domain_obj:
        print(f"WARNING: Tenant {client.schema_name} has no domain!")
        continue

    # Determine Correct Domain Name
    if client.schema_name == 'public':
        expected_domain = TARGET_DOMAIN
    else:
        # specific tenants: tenantXXXX.wfm-pro.com
        expected_domain = f"{client.schema_name}.{TARGET_DOMAIN}"

    # Check and Fix
    if domain_obj.domain != expected_domain:
        print(f"FIXING: {client.schema_name} | Old: {domain_obj.domain} -> New: {expected_domain}")
        domain_obj.domain = expected_domain
        domain_obj.save()
    else:
        print(f"OK: {client.schema_name} -> {domain_obj.domain}")

print("--- FIX COMPLETE ---")
