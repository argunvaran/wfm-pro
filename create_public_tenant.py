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
        
        domain = Domain()
        domain.domain = 'localhost' # Public domain
        domain.tenant = tenant
        domain.is_primary = True
        domain.save()
        print("Public tenant created successfully.")
    else:
        print("Public tenant already exists.")
        
except Exception as e:
    print(f"Error creating public tenant: {e}")
