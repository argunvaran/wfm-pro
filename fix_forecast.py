import os
import django
import sys

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from calls.utils import aggregate_actuals

print("--- FIXING FORECAST DATA ---")
print("Aggregating raw calls into 15-minute intervals...")
try:
    aggregate_actuals()
    print("[SUCCESS] Data aggregated successfully.")
    print("You can now use the 'Generate Forecast' button on the dashboard.")
except Exception as e:
    print(f"[ERROR] Aggregation failed: {e}")
print("----------------------------")
