import csv
import random
import uuid
from datetime import datetime, timedelta
import argparse
import os

def generate_csv(filename, agent_count, call_count, days):
    print(f"Generating {filename}...")
    print(f"Agents: {agent_count}, Calls: {call_count}, Days: {days}")

    # 1. Setup Mock Organization
    departments = ['Customer Support', 'Sales', 'Technical Service']
    teams_map = {
        'Customer Support': ['Inbound A', 'Inbound B', 'VIP Support'],
        'Sales': ['Outbound Sales', 'Retention'],
        'Technical Service': ['Tech L1', 'Tech L2']
    }
    
    queues = ['General Support', 'Sales Line', 'VIP Line', 'Tech Support']

    # 2. Generate Agents
    agents = []
    print("Generating agent profiles...")
    for i in range(1, agent_count + 1):
        dept = random.choice(departments)
        team = random.choice(teams_map[dept])
        
        # 1 Team Leader per 10 agents roughly
        is_leader = (i % 10 == 0)
        
        agents.append({
            'username': f"agent.{i:03d}",
            'team': team,
            'department': dept,
            'leader': f"leader.{team.replace(' ', '').lower()}"
        })

    # 3. Generate Calls
    start_date = datetime.now() - timedelta(days=days)
    records = []
    
    print("Generating calls...")
    
    # Pre-generate some frequent callers (for Customer Journey report)
    frequent_customers = [f"+90555{random.randint(1000000, 9999999)}" for _ in range(50)]
    
    for _ in range(call_count):
        # Time
        day_offset = random.randint(0, days)
        hour = int(random.gauss(14, 4)) # Peak around 14:00
        hour = max(0, min(23, hour))
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dt = start_date + timedelta(days=day_offset)
        dt = dt.replace(hour=hour, minute=minute, second=second)
        
        # Agent (90% answered)
        if random.random() < 0.9:
            agent = random.choice(agents)
            agent_user = agent['username']
            team = agent['team']
            dept = agent['department']
            leader = agent['leader']
            duration = int(random.gauss(180, 60)) # Avg 3 mins
            duration = max(10, duration)
        else:
            # Abandoned / Unassigned
            agent_user = ""
            team = ""
            dept = ""
            leader = ""
            duration = 0

        # Queue
        queue = random.choice(queues)

        # Customer Number (20% chance of repeat caller)
        if random.random() < 0.2:
            cust_num = random.choice(frequent_customers)
        else:
            cust_num = f"+90555{random.randint(1000000, 9999999)}"

        records.append([
            f"GEN-{uuid.uuid4().hex[:8].upper()}",
            dt.strftime("%Y-%m-%d %H:%M:%S"),
            duration,
            agent_user,
            queue,
            team,
            dept,
            leader,
            cust_num
        ])

    # 4. Write CSV
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header matching imports/views.py
        writer.writerow(['call_id', 'timestamp', 'duration', 'agent', 'queue', 'team', 'department', 'team_leader', 'customer_number'])
        writer.writerows(records)

    print(f"Successfully created {filename} with {len(records)} rows.")

if __name__ == "__main__":
    # Default: 50 Agents, 5000 Calls, 30 Days
    generate_csv('manual_upload_data.csv', 50, 5000, 30)
