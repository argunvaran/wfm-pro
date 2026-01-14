
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
            "name": "Başlangıç",
            "description": "Küçük ekipler için ideal",
            "price_monthly": 499.00,
            "max_agents": 10,
            "max_calls_monthly": 5000
        },
        {
            "name": "Profesyonel", 
            "description": "Büyüyen işletmeler için",
            "price_monthly": 999.00,
            "max_agents": 50,
            "max_calls_monthly": 20000
        },
        {
            "name": "Kurumsal",
            "description": "Büyük ölçekli operasyonlar",
            "price_monthly": 1999.00,
            "max_agents": 200,
            "max_calls_monthly": 100000
        }
    ]
    
    for p_data in plans_data:
        plan, created = Plan.objects.get_or_create(
            name=p_data['name'],
            defaults=p_data
        )
        if created:
            print(f"Created Plan: {plan}")
        else:
            print(f"Plan already exists: {plan}")

if __name__ == "__main__":
    try:
        init_plans()
    except Exception as e:
        print(f"Error: {e}")
