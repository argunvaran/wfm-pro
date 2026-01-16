import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

try:
    client = Client.objects.get(schema_name='public')
    domain, created = Domain.objects.get_or_create(domain='localhost', tenant=client, is_primary=False)
    if created:
        print("Added localhost to public tenant")
    else:
        print("localhost already exists for public tenant")
except Exception as e:
    print(f"Error: {e}")
