
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wfm_core.settings')
django.setup()

from tenants.models import Client, Domain
from users.models import User
from django.db.utils import IntegrityError

def setup_mobile_test():
    tenant_name = "mobile_test"
    domain_url = "mobile.10.0.2.2.nip.io" # Magic domain that resolves to localhost (10.0.2.2 for emulator)
    
    print(f"--- Setting up Mobile Test Tenant ---")
    
    # 1. Create or Get Tenant
    try:
        tenant = Client.objects.get(schema_name=tenant_name)
        print(f"Tenant '{tenant_name}' already exists.")
    except Client.DoesNotExist:
        print(f"Creating tenant '{tenant_name}'...")
        tenant = Client(schema_name=tenant_name, name="Mobile Test Corp", is_active=True)
        tenant.save()
        print("Tenant created.")

    # 2. Create Domain
    # We need to port as well if running on 8000? django-tenants matches domain only usually, but let's see.
    # Usually we add the domain without port in the DB, but the Host header includes port sometimes or django-tenants strips it.
    # Standard practice: just the domain name.
    
    if not Domain.objects.filter(domain=domain_url).exists():
        print(f"Creating domain '{domain_url}'...")
        domain = Domain()
        domain.domain = domain_url
        domain.tenant = tenant
        domain.is_primary = True
        domain.save()
        print("Domain created.")
    else:
        print(f"Domain '{domain_url}' already exists.")

    # 3. Create User inside the tenant
    print(f"Creating user in tenant '{tenant_name}'...")
    with django_tenants.utils.schema_context(tenant_name):
        from users.models import User
        if not User.objects.filter(email='mobile@test.com').exists():
            user = User.objects.create_user(
                username='mobile_user',
                email='mobile@test.com',
                password='password123',
                role='agent'
            )
            print("User 'mobile_user' (password: password123) created.")
            
            # Create Agent Profile if needed
            from agents.models import AgentProfile
            if not AgentProfile.objects.filter(user=user).exists():
                AgentProfile.objects.create(user=user, employee_id="MOB001")
                print("Agent Profile created.")
        else:
            print("User 'mobile_user' already exists.")

    print("\n---------------------------------------------------")
    print("SETUP COMPLETE!")
    print(f"Workspace Name: {tenant_name}")
    print(f"Domain URL:     {domain_url}")
    print(f"User Email:     mobile@test.com")
    print(f"User Password:  password123")
    print("---------------------------------------------------")
    print("Make sure runserver is running on port 8000.")

if __name__ == '__main__':
    import django_tenants.utils
    setup_mobile_test()
