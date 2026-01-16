import os
import sys
import django
from datetime import datetime

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wfm_core.settings")
django.setup()

from tenants.models import Client
from django_tenants.utils import schema_context
from django.core.management import call_command
from calls.utils import aggregate_actuals

def get_input(prompt, default=None, cast_type=str):
    if default:
        user_input = input(f"{prompt} [{default}]: ")
        if not user_input:
            return default
    else:
        user_input = input(f"{prompt}: ")
    
    try:
        return cast_type(user_input)
    except ValueError:
        print(f"Invalid input type. Expected {cast_type.__name__}.")
        return get_input(prompt, default, cast_type)

def main():
    print("=== Custom Data Generator ===")
    
    # 1. Select Tenant
    clients = Client.objects.all().order_by('name')
    print("\nAvailable Tenants:")
    for i, client in enumerate(clients):
        print(f"{i+1}. {client.name} ({client.schema_name})")
    
    while True:
        try:
            choice = int(input("\nSelect Tenant (Number): "))
            if 1 <= choice <= len(clients):
                selected_client = clients[choice-1]
                break
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

    print(f"\nSelected Tenant: {selected_client.name} ({selected_client.schema_name})")
    
    # 2. Parameters
    agent_count = get_input("Number of Agents", default=50, cast_type=int)
    call_count = get_input("Number of Calls", default=5000, cast_type=int)
    days = get_input("Days to simulate", default=30, cast_type=int)
    
    start_date_default = (datetime.now()).strftime('%Y-%m-%d')
    start_date = get_input("Start Date (YYYY-MM-DD)", default=start_date_default)

    print(f"\nReady to generate data for {selected_client.schema_name}...")
    print(f"Agents: {agent_count}, Calls: {call_count}, Days: {days}, Start: {start_date}")
    
    confirm = input("Proceed? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    # 3. Execute
    print("\nGenerating data... Please wait.")
    try:
        with schema_context(selected_client.schema_name):
            try:
                # Call generate_mock_data
                call_command(
                    'generate_mock_data',
                    agents=agent_count,
                    calls=call_count,
                    days=days,
                    start_date=start_date,
                    delete=False # Use Append mode mostly
                )
                
                print("Aggregating Call Data...")
                aggregate_actuals()

                print("Generating Optimized Shifts...")
                call_command(
                    'generate_shifts',
                    days=days,
                    start_date=start_date
                )

            except Exception as e:
                print(f"Error executing command: {e}")
                
        print("\n\nDONE! Data generation complete.")
        
    except Exception as e:
        print(f"Error accessing tenant context: {e}")

if __name__ == "__main__":
    main()
