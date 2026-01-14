import csv
import random
from datetime import datetime, timedelta
import uuid

# Configuration
AGENTS_COUNT = 25
DAILY_CALLS_AVG = 150
START_DATE = datetime(2025, 12, 1)
END_DATE = datetime(2026, 1, 13)

# Data Source
FIRST_NAMES = ["Ahmet", "Mehmet", "Ayşe", "Fatma", "Ali", "Zeynep", "Mustafa", "Emine", "Yusuf", "Elif", "Can", "Gamze", "Murat", "Selin", "Burak", "Esra", "Ozan", "Deniz", "Cem", "Derya"]
LAST_NAMES = ["Yılmaz", "Demir", "Çelik", "Kaya", "Koç", "Öztürk", "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Çetin", "Kara", "Şahin", "Yıldız"]
TEAMS = ["Satış", "Destek", "Teknik", "İade"]
SKILLS = ["Satış", "İkna", "Teknik", "İngilizce", "Almanca", "Müşteri İlişkileri"]
QUEUES = ["Satış Hattı", "Destek Hattı", "VIP Müşteri", "Genel Bilgi"]

def generate_agents(filename):
    print(f"Generating agents to {filename}...")
    agents = []
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Headers: agent_id,firstname,lastname,email,skills,team,employee_id
        writer.writerow(['agent_id', 'firstname', 'lastname', 'email', 'skills', 'team', 'employee_id'])
        
        assigned_usernames = set()
        
        for i in range(AGENTS_COUNT):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            username = f"{fn.lower()}.{ln.lower()}"
            
            # Ensure unique
            counter = 1
            base = username
            while username in assigned_usernames:
                username = f"{base}{counter}"
                counter += 1
            assigned_usernames.add(username)
            
            team = random.choice(TEAMS)
            
            # Generate Skills: SkillName:Level|...
            num_skills = random.randint(1, 3)
            agent_skills = random.sample(SKILLS, num_skills)
            skill_str_parts = []
            for s in agent_skills:
                level = random.randint(1, 5)
                skill_str_parts.append(f"{s}:{level}")
            skills_str = "|".join(skill_str_parts)
            
            email = f"{username}@example.com"
            emp_id = f"EMP{1000+i}"
            
            writer.writerow([username, fn, ln, email, skills_str, team, emp_id])
            agents.append(username)
    return agents

def generate_calls(filename, agent_list):
    print(f"Generating calls to {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Headers: call_id,timestamp,duration,agent,queue
        writer.writerow(['call_id', 'timestamp', 'duration', 'agent', 'queue'])
        
        current_date = START_DATE
        while current_date <= END_DATE:
            # Randomize daily volume
            vol = int(random.gauss(DAILY_CALLS_AVG, 30))
            if vol < 50: vol = 50
            
            # Generate calls for the day
            # Spread between 08:00 and 20:00
            start_hour = 8
            end_hour = 20
            
            day_calls = []
            for _ in range(vol):
                # Random time
                h = random.randint(start_hour, end_hour - 1)
                m = random.randint(0, 59)
                s = random.randint(0, 59)
                ts = current_date.replace(hour=h, minute=m, second=s)
                
                # Duration: Exponential distribution or simple random
                # AHT ~180s
                duration = int(random.gauss(180, 60))
                if duration < 10: duration = 10
                
                # Queue
                queue = random.choice(QUEUES) if random.random() > 0.05 else "" # 5% None
                
                # Agent
                # 90% answered, 10% abandoned (no agent)
                agent = random.choice(agent_list) if random.random() > 0.1 else ""
                
                call_id = uuid.uuid4().hex
                
                day_calls.append((ts, call_id, duration, agent, queue))
            
            # Sort by timestamp
            day_calls.sort(key=lambda x: x[0])
            
            for c in day_calls:
                writer.writerow([c[1], c[0].strftime("%Y-%m-%d %H:%M:%S"), c[2], c[3], c[4]])
            
            current_date += timedelta(days=1)

if __name__ == "__main__":
    agents = generate_agents("c:\\Antigravity\\import_agents_sample.csv")
    generate_calls("c:\\Antigravity\\import_calls_sample.csv", agents)
    print("Done.")
