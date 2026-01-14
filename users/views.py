from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .models import User
from tenants.models import Client, Domain # Updated import
from django_tenants.utils import schema_context
import uuid

class CustomLoginView(LoginView):
    template_name = 'login.html'

def test_signup(request):
    if request.method == 'POST':
        # Create Test Tenant
        # Use a random subdomain
        sub_part = uuid.uuid4().hex[:6]
        tenant_name = f"Test Tenant {sub_part}"
        schema_name = f"tenant_{sub_part}"
        domain_url = f"{sub_part}.localhost"
        
        # Create Client (Trigger schema creation)
        client = Client(schema_name=schema_name, name=tenant_name, paid_until=None, is_active=True)
        client.save()
        
        # Create Domain
        domain = Domain()
        domain.domain = domain_url
        domain.tenant = client
        domain.is_primary = True
        domain.save()
        
        # Create Admin User inside the tenant schema
        try:
            with schema_context(schema_name):
                username = f"admin" # Simple admin username for the tenant
                password = "Wfm1234!" # Default Password
                user = User.objects.create_user(username=username, password=password, role='admin')
                user.force_password_change = True
                user.save()
                print(f"User created for {schema_name}: {user.username}")
        except Exception as e:
            print(f"Error creating user in schema {schema_name}: {e}")
            # Ensure we don't leave a broken tenant/domain if user creation fails
            # But for test_signup we might just let it be or cleanup.
            pass
        
        # Redirect to the new tenant's login page
        return redirect(f"http://{domain_url}:8000/login/?new_tenant=true")
    
    return redirect('login')
