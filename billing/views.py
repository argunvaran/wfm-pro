from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Plan, Subscription
from users.models import User
from tenants.models import Client, Domain
from django.contrib import messages
import json
from .utils import IyzicoService
from django.views.decorators.csrf import csrf_exempt
import os
import uuid
from django_tenants.utils import schema_context
from django.core.management import call_command

DOMAIN_NAME = os.getenv('DOMAIN_NAME', 'wfm-pro.com')

def provision_tenant(plan):
    """
    Creates a new tenant, domain, subscription, and admin user.
    Returns a dict with connection details.
    """
    # Generate unique schema info
    unique_id = uuid.uuid4().hex[:6]
    schema_name = f"tenant{unique_id}"
    domain_url = f"{schema_name}.{DOMAIN_NAME}"
    
    # 1. Client
    client = Client.objects.create(
        schema_name=schema_name,
        name=f"Tenant {unique_id}",
        is_active=True
    )
    
    # 2. Domain
    Domain.objects.create(
        domain=domain_url,
        tenant=client,
        is_primary=True
    )
    
    # 3. Subscription
    Subscription.objects.create(
        client=client, 
        plan=plan,
        is_active=True
    )
    
    # 4. User (Admin) inside Tenant
    username = 'admin'
    password = 'password123'
    
    with schema_context(schema_name):
        if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                username=username,
                email='admin@example.com',
                password=password,
                role='admin'
            )
        
        
        # Default mock data generation disabled by user request [2026-01-16]
        # try:
        #     call_command('generate_mock_data', agents=5, calls=100, days=3)
        # except Exception as e:
        #     print(f"Mock Data Generation Failed: {e}")

    return {
        'status': 'success',
        'domain_url': f"https://{domain_url}" if os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True' else f"http://{domain_url}:8000",
        'username': username,
        'password': password,
        'plan_name': plan.name
    }

def pricing_page(request):
    plans = Plan.objects.all().order_by('price_monthly')
    return render(request, 'pricing.html', {'plans': plans})

def init_payment(request, plan_id):
    # For now, simplistic flow: User enters email/password to create account first?
    # Or assuming user is logged in?
    # Let's assume user creates account at this step or provides details.
    
    # Simplified: Simulating a user session or temporary reg
    if request.method == 'POST':
        # Create a temp user or use logged in
        if request.user.is_authenticated:
            user = request.user
        else:
            # Quick flow: Pricing -> Register -> Payment
            # Redirect to register with Plan param?
            # Or just redirect to Register for now.
             return redirect('test_signup') # Using test_signup for simplicity, ideally custom signup
    
    # Ideally: Show checkout form
    plan = get_object_or_404(Plan, id=plan_id)

    # --- FREE PLAN LOGIC ---
    if plan.price_monthly == 0:
        try:
            context = provision_tenant(plan)
            return render(request, 'payment_success.html', context)
        except Exception as e:
            return render(request, 'payment_success.html', {'status': 'failure', 'error': str(e)})
    # -----------------------
    
    # Mock User for Iyzico (Real prod needs actual user data)
    class MockUser:
        id = 999
        first_name = "Guest"
        last_name = "User"
        email = "guest@example.com"
        
    user = request.user if request.user.is_authenticated else MockUser()
    
    service = IyzicoService()
    # Callback to our payment_result view
    import socket
    # Auto-detect host?
    host = request.get_host() # localhost:8000
    protocol = 'https' if request.is_secure() else 'http'
    callback_url = f"{protocol}://{host}/billing/callback/"
    
    form_result = service.initialize_checkout_form(user, plan, callback_url)
    result_json = json.loads(form_result)
    
    if result_json.get('status') == 'success':
        return render(request, 'payment_page.html', {
            'checkout_form_content': result_json.get('checkoutFormContent'),
            'plan': plan
        })
    else:
        messages.error(request, f"Payment Init Failed: {result_json.get('errorMessage')}")
        return redirect('pricing')

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        service = IyzicoService()
        result = service.retrieve_checkout_form(token)
        res_json = json.loads(result)
        
        if res_json.get('paymentStatus') == 'SUCCESS':
            basket_id = res_json.get('basketId', '') # B1
            plan_id = basket_id.replace('B', '')
            
            try:
                plan = Plan.objects.get(id=plan_id)
            except Plan.DoesNotExist:
                messages.error(request, "Plan not found in callback.")
                return redirect('pricing')

            # Create Tenant using Helper
            try:
                context = provision_tenant(plan)
                return render(request, 'payment_success.html', context)
                
            except Exception as e:
                return render(request, 'payment_success.html', {'status': 'failure', 'error': str(e)})
                


        else:
            return render(request, 'payment_success.html', {'status': 'failure', 'error': f"Payment Failed: {res_json}"})
            
    return redirect('pricing')
