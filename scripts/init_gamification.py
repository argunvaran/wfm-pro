
import os
import django
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django_tenants.utils import schema_context
from tenants.models import Client
from users.models import User
from gamification.models import Badge, UserBadge

def init_badges(tenant_name='public'):
    try:
        client = Client.objects.get(schema_name=tenant_name)
    except Client.DoesNotExist:
        print(f"Tenant {tenant_name} not found")
        return

    with schema_context(client.schema_name):
        print("Creating default badges...")
        badges = [
            {'name': 'İlk Adım', 'desc': 'Sisteme ilk giriş yapıldı', 'icon': 'bi-rocket-takeoff', 'points': 10},
            {'name': 'Çağrı Ustası', 'desc': '100 Çağrı barajı aşıldı', 'icon': 'bi-headset', 'points': 50},
            {'name': 'Dakik Çalışan', 'desc': 'Vardiyaya tam zamanında uyum', 'icon': 'bi-stopwatch', 'points': 30},
            {'name': 'Ayın Elemanı', 'desc': 'Yöneticiler tarafından seçildi', 'icon': 'bi-trophy', 'points': 100},
        ]
        
        created_badges = []
        for b in badges:
            obj, _ = Badge.objects.get_or_create(
                name=b['name'],
                defaults={'description': b['desc'], 'icon': b['icon'], 'points': b['points']}
            )
            created_badges.append(obj)
            
        print("Awarding badges to users (Simulation)...")
        users = User.objects.filter(is_active=True)
        for u in users:
            # Give everyone the 'First Step' badge
            UserBadge.objects.get_or_create(user=u, badge=created_badges[0])
            
            # Randomly give others
            import random
            if random.random() > 0.5:
                UserBadge.objects.get_or_create(user=u, badge=created_badges[1])
             
        print("Done.")

if __name__ == "__main__":
    init_badges('mobile_test')
