import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django.test import RequestFactory
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import Client, Domain

print("--- DOMAIN RESOLUTION TEST ---")

factory = RequestFactory()
middleware = TenantMainMiddleware(lambda r: None)

for client in Client.objects.all():
    domains = client.domains.all()
    for domain in domains:
        print(f"Testing Tenant: {client.schema_name} | Domain: {domain.domain}")
        
        # Simulate request
        try:
            request = factory.get('/', HTTP_HOST=domain.domain)
            middleware.process_request(request)
            
            if hasattr(request, 'tenant'):
                print(f"  [SUCCESS] Resolved to tenant: {request.tenant.schema_name}")
            else:
                print(f"  [FAILED] No tenant found on request object.")
                
        except Exception as e:
            print(f"  [ERROR] {e}")

print("------------------------------")
