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

def provision_tenant(plan, reg_data=None):
    """
    Creates a new tenant, domain, subscription, and admin user.
    reg_data: dict containing 'subdomain', 'company_name', 'admin_username', 'admin_password', 'admin_email'
    """
    if not reg_data:
        # Fallback / Error
        raise Exception("Registration data missing")

    schema_name = reg_data.get('subdomain')
    
    # 1. Client
    client = Client.objects.create(
        schema_name=schema_name,
        name=reg_data.get('company_name'),
        is_active=True
    )
    
    # 2. Domain
    # Use environment variable for the root domain (defaults to wfm-pro.com)
    root_domain = os.getenv('DOMAIN_NAME', 'wfm-pro.com') 
    
    # If running locally without a custom domain, standard is usually localhost
    # But for AWS, user will set DOMAIN_NAME=wfm-pro.com
    domain_url = f"{schema_name}.{root_domain}"

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
    username = reg_data.get('admin_username')
    password = reg_data.get('admin_password')
    email = reg_data.get('admin_email', 'admin@example.com')
    
    with schema_context(schema_name):
        if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                username=username,
                email=email,
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

def init_payment(request):
    # 1. Get Registration Data from Session
    reg_data = request.session.get('reg_data')
    if not reg_data:
        messages.error(request, "Kayıt bilgisi bulunamadı. Lütfen tekrar deneyin.")
        return redirect('pricing')

    plan_id = reg_data.get('plan_id')
    plan = get_object_or_404(Plan, id=plan_id)

    # 2. Check for Free Plan
    if plan.price_monthly == 0:
        try:
            context = provision_tenant(plan, reg_data)
            # Clear session
            del request.session['reg_data']
            return render(request, 'payment_success.html', context)
        except Exception as e:
            return render(request, 'payment_success.html', {'status': 'failure', 'error': str(e)})

    # 3. Prepare Iyzico User (from Session Data)
    class TempUser:
        id = str(uuid.uuid4()) # Unique ID for payment tracking
        first_name = reg_data.get('company_name')[:20] # Iyzico limits? Use simplistic approach
        last_name = "Admin"
        email = reg_data.get('admin_email')
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
    user = TempUser()
    
    service = IyzicoService()
    
    # Callback URL
    host = request.get_host()
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
        # Error from Iyzico
        messages.error(request, f"Ödeme Başlatılamadı: {result_json.get('errorMessage')}")
        return redirect('register')

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
            reg_data = request.session.get('reg_data')
            
            try:
                context = provision_tenant(plan, reg_data)
                
                # Success - Clear Session
                if 'reg_data' in request.session:
                    del request.session['reg_data']
                    
                return render(request, 'payment_success.html', context)
                
            except Exception as e:
                return render(request, 'payment_success.html', {'status': 'failure', 'error': str(e)})
                


        else:
            return render(request, 'payment_success.html', {'status': 'failure', 'error': f"Payment Failed: {res_json}"})
            
    return redirect('pricing')
