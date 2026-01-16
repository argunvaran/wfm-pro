from django.core.management.base import BaseCommand
from django.utils import timezone
from agents.models import AgentProfile
from shifts.models import Shift, ShiftActivity
from datetime import datetime, timedelta, time
import random

class Command(BaseCommand):
    help = 'Generates shifts and activities for agents.'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30)
        parser.add_argument('--start_date', type=str, default=datetime.now().strftime('%Y-%m-%d'))
        parser.add_argument('--delete', action='store_true')

    def handle(self, *args, **options):
        days = options['days']
        start_date_str = options['start_date']
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=days)
        
        self.stdout.write(f"Generating optimized schedule from {start_date} to {end_date}...")
        
        from shifts.utils import generate_schedule
        count = generate_schedule(None, start_date, end_date)
            
        self.stdout.write(self.style.SUCCESS(f"Generated {count} shifts with detailed activities."))
