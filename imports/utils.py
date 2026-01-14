import pandas as pd
from agents.models import AgentProfile, Team, Skill, AgentSkill
from users.models import User
from calls.models import CallVolume, Queue
from django.db import transaction
import datetime

def process_agent_import(file_path):
    df = pd.read_csv(file_path)
    logs = []
    
    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                # 1. Identify Username/AgentID
                username = None
                if 'agent_id' in row and pd.notna(row['agent_id']):
                    username = str(row['agent_id']).strip()
                elif 'username' in row and pd.notna(row['username']):
                    username = str(row['username']).strip()
                
                if not username:
                    logs.append(f"Row {index}: Missing agent_id or username. Skipped.")
                    continue

                # 2. Get or Create Team
                team = None
                if 'team' in row and pd.notna(row['team']):
                    team_name = row['team']
                    team, _ = Team.objects.get_or_create(name=team_name)
                
                # 3. Create/Get User
                email = row.get('email', '') if pd.notna(row.get('email')) else ''
                first_name = row.get('firstname', '') if pd.notna(row.get('firstname')) else ''
                last_name = row.get('lastname', '') if pd.notna(row.get('lastname')) else ''
                
                user, created_user = User.objects.get_or_create(username=username, defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'agent',
                    'force_password_change': True
                })
                
                if created_user:
                    user.set_password('Wfm1234!')
                    user.save()
                    logs.append(f"Created user {username}.")
                else:
                    # Update fields if provided? User didn't ask, but good practice. 
                    pass
                
                # 4. Create/Get Profile
                profile, created_profile = AgentProfile.objects.get_or_create(user=user)
                if created_profile:
                   pass
                
                # Update attributes
                if 'employee_id' in row and pd.notna(row['employee_id']):
                     profile.employee_id = row['employee_id']
                
                if team:
                    profile.team = team
                
                profile.save()
                
                # 5. Skills
                if 'skills' in row and pd.notna(row['skills']):
                    skills_str = str(row['skills'])
                    # Separator could be | or , or ;. Let's assume |.
                    for s_item in skills_str.split('|'): 
                        parts = s_item.split(':')
                        s_name = parts[0].strip()
                        if not s_name: continue
                        
                        level = int(parts[1]) if len(parts) > 1 else 1
                        
                        skill, _ = Skill.objects.get_or_create(name=s_name)
                        
                        AgentSkill.objects.update_or_create(
                            agent=profile,
                            skill=skill,
                            defaults={'level': level}
                        )
                        
            except Exception as e:
                logs.append(f"Error row {index}: {str(e)}")
                
    return logs

def process_call_import(file_path):
    df = pd.read_csv(file_path)
    logs = []
    
    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                # 1. Queue (Optional)
                queue = None
                if 'queue' in row and pd.notna(row['queue']):
                    queue_name = row['queue']
                    queue, _ = Queue.objects.get_or_create(name=queue_name)
                
                # 2. Agent (Optional but common)
                agent_profile = None
                if 'agent' in row and pd.notna(row['agent']):
                    username = str(row['agent']).strip()
                    # Ensure user exists
                    user, created = User.objects.get_or_create(username=username, defaults={
                        'role': 'agent',
                        'force_password_change': True
                    })
                    if created:
                        user.set_password('Wfm1234!')
                        user.save()
                        logs.append(f"Auto-created agent user {username} from call log.")
                        
                    agent_profile, _ = AgentProfile.objects.get_or_create(user=user)
                
                # 3. Call Details
                # timestamp/call_time
                ts_str = row.get('call_time') or row.get('timestamp')
                # Need proper parsing. Pandas usually reads as string or object.
                timestamp = pd.to_datetime(ts_str)
                
                duration = int(row.get('duration', 0))
                
                # 4. Unique ID
                call_id = None
                if 'call_id' in row and pd.notna(row['call_id']):
                    call_id = str(row['call_id'])
                else:
                    # Generate unique ID based on properties to be deterministic if possible?
                    # Or just random if we trust the source to provide IDs?
                    # User said: "agentid biz bir unique id üretelim ayrıca... çağrılara da unique id atayalım"
                    # "Assign unique id to calls".
                    import uuid
                    call_id = f"gen-{uuid.uuid4()}"
                
                # 5. Create Call
                from calls.models import Call
                Call.objects.update_or_create(
                    call_id=call_id,
                    defaults={
                        'timestamp': timestamp,
                        'duration': duration,
                        'queue': queue,
                        'agent': agent_profile
                    }
                )
                        
            except Exception as e:
                logs.append(f"Error row {index}: {str(e)}")
    return logs
