import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

print("--- TENANT DEBUG INFO ---")
print(f"Total Clients: {Client.objects.count()}")
print(f"Total Domains: {Domain.objects.count()}")

for client in Client.objects.all():
    domains = client.domains.all()
    domain_names = [d.domain for d in domains]
    print(f"Tenant: {client.schema_name} | Name: {client.name} | Domains: {domain_names}")

print("-------------------------")
