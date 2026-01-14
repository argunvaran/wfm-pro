from django.utils import timezone
from .models import Shift
from calls.models import RealTimeAgentState
from agents.models import AgentProfile
from datetime import datetime, timedelta

def get_live_adherence_data():
    """
    Returns a snapshot of all agents, their current state, and adherence status.
    """
    now = timezone.now()
    now_time = now.time()
    today = now.date()
    
    agents = AgentProfile.objects.filter(user__is_active=True).select_related('user', 'live_state')
    data = []
    
    # Pre-fetch shifts for today
    # Optimization: Filter shifts where date=today
    shifts_today = list(Shift.objects.filter(date=today))
    
    for agent in agents:
        # 1. Get Live State
        try:
            live_state = agent.live_state.state
            since = agent.live_state.since
            duration = (now - since).seconds if since else 0
        except:
            live_state = 'Offline'
            duration = 0
            
        # 2. Get Scheduled State
        # Find shift for this agent
        current_shift = next((s for s in shifts_today if s.agent_id == agent.id), None)
        
        scheduled_state = 'Off'
        if current_shift:
            # Check within shift bounds
            if current_shift.start_time <= now_time <= current_shift.end_time:
                scheduled_state = 'Working'
                # Check Break
                if current_shift.break_start:
                    # Simple Break Logic: 1 hour duration
                    # We need explicit break end time. Assuming 60 mins from model default.
                    break_start_dt = datetime.combine(today, current_shift.break_start)
                    break_end_dt = break_start_dt + timedelta(minutes=current_shift.break_duration)
                    
                    if break_start_dt.time() <= now_time <= break_end_dt.time():
                        scheduled_state = 'Break'
            else:
                scheduled_state = 'Off'
        
        # 3. Compare (Adherence Logic)
        is_adherent = True
        
        # Mapping: Live State vs Scheduled
        # Live: Ready, Talking, Works -> Compatible with 'Working'
        # Live: Break, Aux -> Compatible with 'Break'
        # Live: Offline -> Compatible with 'Off'
        
        normalized_live = live_state.upper()
        
        if scheduled_state == 'Working':
            if normalized_live in ['OFFLINE', 'BREAK', 'AUX', 'PAUSE']: 
                is_adherent = False
        elif scheduled_state == 'Break':
            if normalized_live in ['READY', 'TALKING', 'ON CALL']:
                is_adherent = False
        elif scheduled_state == 'Off':
            # If scheduled off but working, usually fine, but strictly "Out of Adherence" (Overtime?)
            if normalized_live in ['READY', 'TALKING', 'ON CALL']:
                is_adherent = False # Unexpected overwork?
                
        data.append({
            'agent_name': f"{agent.user.first_name} {agent.user.last_name}",
            # 'avatar': agent.avatar.url if agent.avatar else None, # Avatar field might not exist on AgentProfile in minimal model
            'live_state': live_state,
            'scheduled_state': scheduled_state,
            'is_adherent': is_adherent,
            'duration_str': str(timedelta(seconds=duration)).split('.')[0], # H:M:S
            'team': agent.team.name if agent.team else 'General'
        })
        
    return data
