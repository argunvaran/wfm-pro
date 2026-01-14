import os
import django
import sys
from django.conf import settings

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain

print(f"--- DB INTEGRITY CHECK ---")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

for domain in Domain.objects.all():
    print(f"\nChecking Domain ID: {domain.id}")
    print(f"  Raw String: '{domain.domain}'")
    print(f"  Repr: {repr(domain.domain)}")
    print(f"  Tenant: {domain.tenant.schema_name}")
    
    # MANUAL LOOKUP TEST
    try:
        d = Domain.objects.get(domain=domain.domain)
        print(f"  [PASS] Exact get() lookup successful.")
    except Exception as e:
        print(f"  [FAIL] Exact get() lookup FAILED: {e}")

    # RESOLUTION SIMULATION (Manual)
    try:
        # Simulate logic from TenantMainMiddleware
        hostname = domain.domain
        qs = Domain.objects.select_related('tenant')
        domain_obj = qs.get(domain=hostname)
        tenant = domain_obj.tenant
        print(f"  [PASS] Tenant Resolution Logic successful -> {tenant.schema_name}")
    except Exception as e:
        print(f"  [FAIL] Tenant Resolution Logic FAILED: {e}")

print("\n--- CHECK COMPLETE ---")
