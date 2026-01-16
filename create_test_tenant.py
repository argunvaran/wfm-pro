import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context

User = get_user_model()

try:
    schema_name = 'demo'
    tenant_name = 'Demo Tenant'
    domain_url = 'demo.localhost' # Must match LOCALHOST usage for testing

    # Create Client
    client, created = Client.objects.get_or_create(
        schema_name=schema_name,
        defaults={
            'name': tenant_name,
            'is_active': True
        }
    )

    if created:
        print(f"Created Tenant: {tenant_name}")
    else:
        print(f"Found Tenant: {tenant_name}")

    # Create Domain
    domain, domain_created = Domain.objects.get_or_create(
        tenant=client,
        defaults={'domain': domain_url, 'is_primary': True}
    )
    
    if domain_created:
        print(f"Created Domain: {domain_url}")
    else:
        print(f"Found Domain: {domain_url}")
        if domain.domain != domain_url:
            domain.domain = domain_url
            domain.save()
            print(f"Updated domain to {domain_url}")

    # Create Admin User inside the tenant schema
    with schema_context(schema_name):
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_user(username='admin', password='password', role='admin')
            print(f"User 'admin' created for {schema_name}")
        else:
            print(f"User 'admin' already exists for {schema_name}")

except Exception as e:
    print(f"Error creating test tenant: {e}")
