
import os
import sys
import django

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from billing.models import Plan
from tenants.models import Client

def init_plans():
    # Only run in public schema
    # (By default the connection is public unless schema_context is used)
    
    plans_data = [
        {
            "name": "Ücretsiz Başlangıç",
            "description": "Küçük ekipler ve deneme için",
            "price_monthly": 0.00,
            "max_agents": 5,
            "max_calls_monthly": 1000,
            "max_storage_gb": 1.0
        },
        {
            "name": "Profesyonel", 
            "description": "Büyüyen işletmeler için sınırsız erişim",
            "price_monthly": 999.00,
            "max_agents": 9999, # Unlimited essentially
            "max_calls_monthly": 100000,
            "max_storage_gb": 50.0
        },
        {
            "name": "Kurumsal",
            "description": "Özel ihtiyaçlar için",
            "price_monthly": 1999.00,
            "max_agents": 9999,
            "max_calls_monthly": 1000000,
            "max_storage_gb": 100.0
        }
    ]
    
    for p_data in plans_data:
        plan, created = Plan.objects.update_or_create(
            name=p_data['name'],
            defaults=p_data
        )
        if created:
            print(f"Created Plan: {plan}")
        else:
            print(f"Updated Plan: {plan}")

if __name__ == "__main__":
    try:
        init_plans()
    except Exception as e:
        print(f"Error: {e}")
