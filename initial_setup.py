
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client, Domain
from users.models import User
from agents.models import AgentProfile
from django_tenants.utils import schema_context

def run_setup():
    print("🚀 Initial System Setup Initiated...")

    # 1. PUBLIC TENANT
    if not Client.objects.filter(schema_name='public').exists():
        print("Creating Public Tenant...")
        public = Client(schema_name='public', name='WFM Public')
        public.save()
        Domain.objects.create(domain='wfm-pro.com', tenant=public, is_primary=True)
    else:
        print("✅ Public Tenant exists.")

    # 2. TEST TENANT
    if not Client.objects.filter(schema_name='test').exists():
        print("Creating Test Tenant (Tablolar oluşturuluyor)...")
        test_client = Client(schema_name='test', name='Test Customer')
        test_client.save()
        if not Domain.objects.filter(domain='test.wfm-pro.com').exists():
            Domain.objects.create(domain='test.wfm-pro.com', tenant=test_client, is_primary=True)
    else:
        print("✅ Test Tenant exists.")

    # 3. ADMIN USER (Inside Test Tenant)
    with schema_context('test'):
        if not User.objects.filter(username='argun').exists():
            print("Creating Admin User 'argun' in Test Tenant...")
            u = User.objects.create_superuser('argun', 'argun@example.com', '123')
            AgentProfile.objects.create(user=u)
            print("✅ User created: argun / 123")
        else:
            print("✅ User 'argun' already exists.")

    print("\n🎉 SETUP COMPLETE! You can now login at https://test.wfm-pro.com")

if __name__ == '__main__':
    run_setup()
