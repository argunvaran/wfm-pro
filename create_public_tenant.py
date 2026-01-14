import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

try:
    target_domain = os.getenv('DOMAIN_NAME', 'wfm-pro.com')
    
    client, created = Client.objects.get_or_create(
        schema_name='public',
        defaults={
            'name': 'Public Tenant',
            'is_active': True
        }
    )
    
    if created:
        print("Created Public Tenant.")
    else:
        print("Found Public Tenant.")

    # Ensure Domain is correct
    domain, domain_created = Domain.objects.get_or_create(
        tenant=client,
        defaults={'domain': target_domain, 'is_primary': True}
    )
    
    if not domain_created and domain.domain != target_domain:
        print(f"Updating domain from {domain.domain} to {target_domain}")
        domain.domain = target_domain
        domain.save()
    elif domain_created:
        print(f"Created domain: {target_domain}")
    else:
        print(f"Domain correct: {target_domain}")
        
except Exception as e:
    print(f"Error creating public tenant: {e}")
