import pandas as pd
import numpy as np
from datetime import timedelta, datetime, time
from calls.models import CallVolume, Queue
from calls.utils import calculate_required_agents
from shifts.models import Shift
from agents.models import AgentProfile
from django.db import transaction

def generate_schedule(ignored_tenant, start_date, end_date):
    """
    Generates a schedule for the given range respecting Shift Types.
    """
    dates = pd.date_range(start_date, end_date)
    requirements = {} # (date, hour) -> required_agents
    
    queues = Queue.objects.all()
    
    # Pre-fetch ShiftTypes to minimize DB hits later? Not critical for small N.
    
    for d in dates:
        d_date = d.date()
        for h in range(24):
            # Fetch Volumes (Forecast or Actual)
            # Try to match hour exactly. 
            # Note: interval_start is TimeField.
            calls_list = CallVolume.objects.filter(date=d_date, interval_start__hour=h)
            
            agg_vol = sum([v.calls_offered for v in calls_list])
            if agg_vol > 0:
                # Weighted AHT
                total_product = sum([v.calls_offered * v.aht_seconds for v in calls_list])
                avg_aht = total_product / agg_vol
                req = calculate_required_agents(agg_vol, 3600, avg_aht, 20, 0.8)
                requirements[(d_date, h)] = req
            else:
                requirements[(d_date, h)] = 0

    # 2. Get Agents
    # Determine shift capabilities
    # If agent has no shift type, assign a default "Standard 09-18"
    
    agents = list(AgentProfile.objects.filter(user__is_active=True))
    from agents.models import ShiftType
    
    default_st, _ = ShiftType.objects.get_or_create(
        name="Standard 09-18",
        defaults={
            'start_time_min': time(9,0),
            'start_time_max': time(9,0),
            'duration_hours': 9.0,
            'paid_hours': 8.0
        }
    )
    
    agent_states = {a.id: {'hours_week': 0, 'last_shift_end': None} for a in agents}
    
    shifts_to_create = []

    for d in dates:
        d_date = d.date()
        daily_req = {h: requirements[(d_date, h)] for h in range(24)}
        coverage = {h: 0 for h in range(24)}
        
        # Sort agents by "least hours worked" to balance?
        agents.sort(key=lambda a: agent_states[a.id]['hours_week'])
        
        # Iterate Agents to assign ONE shift per day max
        for agent in agents:
            # Check weekly limit
            if agent_states[agent.id]['hours_week'] >= 45:
                continue
                
            # Rest check (11 hours)
            if agent_states[agent.id]['last_shift_end']:
                last_end = agent_states[agent.id]['last_shift_end']
                # Assume earliest possible start is ... 00:00?
                # We check this inside the candidate start time loop
                pass
            
            st = agent.shift_type if agent.shift_type else default_st
            
            # Determine feasible start times
            # start_time_min to start_time_max
            # For simplicity, step by hour
            
            s_min = st.start_time_min.hour
            s_max = st.start_time_max.hour
            
            # Handling overnight shifts? Simplified: assume same day start.
            if s_max < s_min: s_max = 23 # End of day wrap? Ignore for now
            
            feasible_starts = range(s_min, s_max + 1)
            
            best_start = -1
            max_impact = -1
            
            # Find best start time to cover deficits
            for s_hour in feasible_starts:
                # Rest Check
                potential_start_dt = datetime.combine(d_date, time(s_hour, 0))
                if agent_states[agent.id]['last_shift_end']:
                    diff = (potential_start_dt - agent_states[agent.id]['last_shift_end']).total_seconds()
                    if diff < 11 * 3600:
                        continue
                
                # Check impact
                impact = 0
                shift_len = int(st.duration_hours)
                break_offset = int(shift_len / 2) # Break in middle
                
                # Check coverage vs requirement
                for i in range(shift_len):
                    h = s_hour + i
                    if h >= 24: break # Next day logic skipped for simplicity
                    
                    if i == break_offset: continue # Break
                    
                    if coverage.get(h, 0) < daily_req.get(h, 0):
                        impact += 1
                
                if impact > max_impact:
                    max_impact = impact
                    best_start = s_hour
            
            # Assign if beneficial (impact > 0) OR if we want to force minimum hours?
            # Greedy: Only assign if needed.
            if max_impact > 0:
                shift_len = int(st.duration_hours)
                break_offset = int(shift_len / 2)
                
                shifts_to_create.append(Shift(
                    agent=agent,
                    date=d_date,
                    start_time=time(best_start, 0),
                    end_time=time(best_start + shift_len if best_start + shift_len < 24 else 23, 59), # Clipped
                    break_start=time(best_start + break_offset, 0)
                ))
                
                # Update State
                agent_states[agent.id]['hours_week'] += st.paid_hours
                agent_states[agent.id]['last_shift_end'] = datetime.combine(d_date, time(best_start, 0)) + timedelta(hours=shift_len)
                
                # Update Coverage
                for i in range(shift_len):
                    h = best_start + i
                    if h < 24 and i != break_offset:
                        coverage[h] += 1
                        
    with transaction.atomic():
        Shift.objects.filter(date__range=(start_date, end_date)).delete()
        Shift.objects.bulk_create(shifts_to_create)

    return len(shifts_to_create)
