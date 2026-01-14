import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

try:
    if not Client.objects.filter(schema_name='public').exists():
        tenant = Client(schema_name='public', name='Public Tenant', paid_until=None, is_active=True)
        tenant.save()
        
        domain_name = os.getenv('DOMAIN_NAME', 'localhost')
        domain = Domain()
        domain.domain = domain_name
        domain.tenant = tenant
        domain.is_primary = True
        domain.save()
        print("Public tenant created successfully.")
    else:
        print("Public tenant already exists.")
        
except Exception as e:
    print(f"Error creating public tenant: {e}")
