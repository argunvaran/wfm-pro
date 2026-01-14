import random
from datetime import datetime, timedelta
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from agents.models import AgentProfile, Team, ShiftType
from calls.models import Call, Queue
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates mock data (Agents and Calls) for testing.'

    def add_arguments(self, parser):
        parser.add_argument('--agents', type=int, default=100, help='Number of agents to ensure exist')
        parser.add_argument('--calls', type=int, default=100000, help='Number of calls to generate')
        parser.add_argument('--start_date', type=str, default=datetime.now().strftime('%Y-%m-%d'), help='Start date YYYY-MM-DD')
        parser.add_argument('--days', type=int, default=30, help='Duration in days to distribute calls')
        parser.add_argument('--delete', action='store_true', help='Delete existing data before generating')

    def handle(self, *args, **options):
        agent_count = options['agents']
        call_count = options['calls']
        start_date_str = options['start_date']
        days = options['days']
        delete = options['delete']

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        self.stdout.write(self.style.WARNING(f"Starting Data Generation..."))
        self.stdout.write(f"Target: {agent_count} Agents, {call_count} Calls over {days} Days starting {start_date}")

        if delete:
            self.stdout.write("Deleting existing data...")
            Call.objects.all().delete()
            # We don't delete agents usually as they might be Users, but for this script maybe?
            # Let's keep agents if not explicit, but here we just delete calls.
            # Agent cleanup is risky if it cascades to users.
            
        with transaction.atomic():
            # 1. Setup Basic Data (Queue, Team, ShiftType)
            queue, _ = Queue.objects.get_or_create(name='General Support')
            team, _ = Team.objects.get_or_create(name='Support Team')
            st, _ = ShiftType.objects.get_or_create(
                name='Standard 09-18',
                defaults={
                    'start_time_min': '09:00',
                    'start_time_max': '09:00',
                    'duration_hours': 9.0
                }
            )

            # 2. Generate Agents
            current_agents = AgentProfile.objects.count()
            needed_agents = max(0, agent_count - current_agents)
            
            if needed_agents > 0:
                self.stdout.write(f"Creating {needed_agents} new agents...")
                new_users = []
                new_profiles = []
                
                # Bulk create Users is tricky with password hashing. 
                # For 100 users, loop is fine.
                for i in range(needed_agents):
                    uid = uuid.uuid4().hex[:8]
                    username = f"agent_{uid}"
                    email = f"{username}@test.com"
                    
                    user = User(username=username, email=email, role='agent')
                    user.set_password('pass1234')
                    user.save()
                    
                    profile = AgentProfile(user=user, team=team, shift_type=st)
                    profile.save() # Doing save individually to ensure signals/ID usage if any
                
                self.stdout.write(self.style.SUCCESS(f"Created {needed_agents} agents."))
            
            all_agent_ids = list(AgentProfile.objects.values_list('id', flat=True))

            # 3. Generate Calls
            # We want to distribute calls across 'days' days.
            # Simple distribution: random date between start and start+days
            # Higher volume during day time (09-18)
            
            self.stdout.write(f"Generating {call_count} calls (this may take a moment)...")
            
            calls_to_create = []
            
            # Pre-calculate date range
            date_list = [start_date + timedelta(days=i) for i in range(days)]
            
            # Weights for hours (Focus on 09-18)
            hours_weights = []
            for h in range(24):
                if 9 <= h <= 18:
                    hours_weights.append(10) # High weight
                elif 7 <= h <= 23:
                    hours_weights.append(2)  # Low weight
                else:
                    hours_weights.append(1)  # Night
                    
            for _ in range(call_count):
                # Pick Random Date
                d = random.choice(date_list)
                
                # Pick Random Hour based on weights
                h = random.choices(range(24), weights=hours_weights, k=1)[0]
                m = random.randint(0, 59)
                s = random.randint(0, 59)
                
                call_dt = datetime.combine(d, datetime.min.time()) + timedelta(hours=h, minutes=m, seconds=s)
                
                # Pick Random Agent (or None for dropped calls)
                # 95% Answered
                is_answered = random.random() < 0.95
                agent_id = random.choice(all_agent_ids) if (is_answered and all_agent_ids) else None
                
                # Duration (Average 180s)
                duration = int(random.gauss(180, 60)) if is_answered else 0
                duration = max(10, duration) if is_answered else 0
                
                wait_time = int(random.expovariate(1.0/20)) # Avg 20s
                
                # Mock ANI/DNIS
                ani = f"555{random.randint(1000000, 9999999)}"
                
                calls_to_create.append(Call(
                    call_id=f"CALL-{uuid.uuid4().hex[:12].upper()}",
                    queue=queue,
                    agent_id=agent_id,
                    timestamp=call_dt,
                    duration=duration
                ))
                
                # Batch Insert
                if len(calls_to_create) >= 5000:
                    Call.objects.bulk_create(calls_to_create)
                    self.stdout.write(f"inserted batch 5000 calls...")
                    calls_to_create = []

            if calls_to_create:
                Call.objects.bulk_create(calls_to_create)
                
            self.stdout.write(self.style.SUCCESS(f"Successfully generated {call_count} calls."))

            # 4. Aggregate Data for Forecasts
            self.stdout.write("Aggregating actuals for forecasting...")
            from calls.utils import aggregate_actuals
            aggregate_actuals()
            self.stdout.write(self.style.SUCCESS("Aggregation Complete. Data ready for forecasting."))
