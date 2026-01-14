import math

import numpy as np

def erlang_c(traffic_intensity, num_agents):
    """
    Calculates the probability that a call enters the queue (Erlang C formula).
    A: Traffic intensity (calls * AHT / period_duration)
    N: Number of agents
    """
    try:
        if num_agents <= traffic_intensity:
            return 1.0

        numerator = (traffic_intensity ** num_agents) / math.factorial(int(num_agents)) * (num_agents / (num_agents - traffic_intensity))
        
        sum_part = sum([(traffic_intensity ** i) / math.factorial(i) for i in range(int(num_agents))])
        
        return numerator / (sum_part + numerator)
    except OverflowError:
        return 1.0 # If overflow, likely saturated
    except Exception:
        return 1.0

def calculate_service_level(traffic_intensity, num_agents, target_time, aht):
    """
    Calculates Service Level: Probability that wait time <= target_time
    """
    if num_agents <= traffic_intensity:
        return 0.0
    
    ec = erlang_c(traffic_intensity, num_agents)
    # Probability(wait <= target_time) = 1 - (ErlangC * exp(-(N-A) * target_time / AHT))
    
    # Formula components
    # service_rate = 1 / AHT (calls per second per agent? No, AHT is usually seconds)
    # Actually standard formula: P(Wait < t) = 1 - P(Wait > 0) * e^(-(N*mu - lambda)*t)
    # lambda = calls per period
    # mu = 1 / AHT (service rate per agent)
    # N*mu = total service capacity
    
    # Let's normalize to same time units, e.g. seconds.
    # traffic_intensity A = lambda / mu = lambda * AHT
    
    try:
        exponent = - (num_agents - traffic_intensity) * (target_time / aht)
        return 1.0 - (ec * math.exp(exponent))
    except (OverflowError, ValueError, ZeroDivisionError):
        return 0.0

def calculate_required_agents(calls_vol, interval_seconds, aht_seconds, target_time_seconds, target_sla_percent):
    """
    Iteratively finds min agents to meet SLA.
    """
    if calls_vol == 0:
        return 0
    
    # Traffic Intensity (Erlangs) = (Calls * AHT) / Interval
    traffic_intensity = (calls_vol * aht_seconds) / interval_seconds
    
    # Start with at least intensity rounded up
    agents = math.ceil(traffic_intensity) + 1
    
    while True:
        sl = calculate_service_level(traffic_intensity, agents, target_time_seconds, aht_seconds)
        if sl >= target_sla_percent:
            return agents
        agents += 1
        if agents > 1000: # Safety break
            return agents

from datetime import datetime, timedelta, date, time
from django.db.models import Avg, Count
from django.db import transaction
from .models import Call, CallVolume, Queue

# ... Erlang C functions remain the same ...

def aggregate_actuals():
    """
    Aggregates Raw Calls into CallVolume (Actuals) at 15-min intervals.
    """
    with transaction.atomic():
        CallVolume.objects.filter(is_forecast=False).delete()
        
        dates = Call.objects.dates('timestamp', 'day')
        
        for d in dates:
            for h in range(24):
                for m in [0, 15, 30, 45]:
                    # Filter Calls
                    calls = Call.objects.filter(
                        timestamp__date=d, 
                        timestamp__hour=h,
                        timestamp__minute__gte=m,
                        timestamp__minute__lt=m+15
                    )
                    
                    queues = calls.values_list('queue', flat=True).distinct()
                    
                    for q_id in queues:
                        q_calls = calls.filter(queue_id=q_id)
                        count = q_calls.count()
                        if count == 0: continue
                        
                        avg_dur = q_calls.aggregate(Avg('duration'))['duration__avg'] or 0
                        
                        queue_obj = None
                        if q_id:
                            queue_obj = Queue.objects.get(id=q_id)
                        else:
                            continue
                            
                        CallVolume.objects.create(
                            queue=queue_obj,
                            date=d,
                            interval_start=time(h, m),
                            calls_offered=count,
                            aht_seconds=int(avg_dur),
                            is_forecast=False
                        )
    return True

def generate_forecast_data(start_date, end_date):
    """
    Generates Forecast CallVolume based on historical average (15-min granularity).
    """
    # 1. Identify "learning" period (e.g. last 4 weeks)
    # Simple logic: Take all available actuals, average by Weekday + Time.
    
    # weekday -> time -> {sums, count}
    stats = {} 
    
    actuals = CallVolume.objects.filter(is_forecast=False)
    
    for av in actuals:
        wd = av.date.weekday()
        t = av.interval_start # Time object
        key = (av.queue_id, wd, t)
        
        if key not in stats:
            stats[key] = {'calls_sum': 0, 'aht_sum': 0, 'samples': 0}
        
        stats[key]['calls_sum'] += av.calls_offered
        stats[key]['aht_sum'] += av.aht_seconds
        stats[key]['samples'] += 1

    # 2. Generate for target range
    forecasts = []
    
    current = start_date
    while current <= end_date:
        wd = current.weekday()
        for h in range(24):
            for m in [0, 15, 30, 45]:
                t_val = time(h, m)
                
                # Check known keys for current weekday + time
                unique_queues = set([k[0] for k in stats.keys()])
                
                for q_id in unique_queues:
                    key = (q_id, wd, t_val)
                    if key in stats:
                        avg_calls = stats[key]['calls_sum'] / stats[key]['samples']
                        avg_aht = stats[key]['aht_sum'] / stats[key]['samples']
                        
                        forecasts.append(CallVolume(
                            queue_id=q_id,
                            date=current,
                            interval_start=t_val,
                            calls_offered=int(avg_calls),
                            aht_seconds=int(avg_aht),
                            is_forecast=True
                        ))
        current += timedelta(days=1)
        
    with transaction.atomic():
        CallVolume.objects.filter(is_forecast=True, date__range=(start_date, end_date)).delete()
        CallVolume.objects.bulk_create(forecasts)
        
    return len(forecasts)
