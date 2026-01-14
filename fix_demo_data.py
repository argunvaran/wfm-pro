
import os
import sys
import django
from datetime import date, timedelta

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from django_tenants.utils import schema_context
from calls.utils import aggregate_actuals, generate_forecast_data

def process():
    tenant_name = 'demo'
    print(f"Processing data for tenant '{tenant_name}'...")
    
    with schema_context(tenant_name):
        print("Aggregating actuals from raw calls...")
        aggregate_actuals()
        print("Aggregation complete.")
        
        # Forecast for next 4 weeks
        start = date.today()
        end = start + timedelta(weeks=4)
        print(f"Generating forecast from {start} to {end}...")
        count = generate_forecast_data(start, end)
        print(f"Generated {count} forecast intervals.")

if __name__ == "__main__":
    process()
