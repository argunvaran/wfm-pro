from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from .models import User
from tenants.models import Client, Domain # Updated import
from django_tenants.utils import schema_context
import uuid

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if we are on the public tenant
        # In django-tenants, request.tenant is set by middleware
        if hasattr(self.request, 'tenant'):
            context['is_public_tenant'] = (self.request.tenant.schema_name == 'public')
            context['tenant_name'] = self.request.tenant.name
        else:
             # Fallback if something is wrong with middleware, act as public or safely handling
            context['is_public_tenant'] = True
        return context

def register_view(request):
    plan_id = request.GET.get('plan_id')
    
    if request.method == 'POST':
        company_name = request.POST.get('company_name')
        subdomain = request.POST.get('subdomain').lower()
        admin_username = request.POST.get('admin_username')
        admin_email = request.POST.get('admin_email')
        admin_password = request.POST.get('admin_password')
        plan_id = request.POST.get('plan_id') # Get from hidden input

        # Basic Validation
        if Client.objects.filter(schema_name=subdomain).exists():
            return render(request, 'register.html', {'error': 'Bu alan adı (subdomain) zaten kullanılıyor.', 'plan_id': plan_id})
            
        import re
        if not re.match(r'^[a-z0-9]+$', subdomain):
             return render(request, 'register.html', {'error': 'Subdomain sadece harf ve rakam içerebilir.', 'plan_id': plan_id})

        try:
            # Store in Session
            request.session['reg_data'] = {
                'company_name': company_name,
                'subdomain': subdomain,
                'admin_username': admin_username,
                'admin_email': admin_email,
                'admin_password': admin_password,
                'plan_id': plan_id
            }
            request.session.modified = True

            # Redirect to Payment
            return redirect('init_payment')

        except Exception as e:
            return render(request, 'register.html', {'error': f'Hata oluştu: {str(e)}', 'plan_id': plan_id})

    return render(request, 'register.html', {'plan_id': plan_id})
