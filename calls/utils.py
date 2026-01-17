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

def generate_forecast_data(start_date, end_date, model_type='simple_avg'):
    """
    Generates Forecast CallVolume based on historical data.
    Models:
    - simple_avg: Average of all available history for matching Weekday/Time.
    - weighted_avg: Weighted average of last 4 weeks (40%, 30%, 20%, 10%).
    """
    
    # 1. Fetch History
    # We fetch all non-forecast volumes
    actuals = CallVolume.objects.filter(is_forecast=False).order_by('date')
    
    # Structure: (queue_id, weekday, time) -> [list of values]
    history_map = {} 
    
    for av in actuals:
        wd = av.date.weekday()
        t = av.interval_start
        key = (av.queue_id, wd, t)
        
        if key not in history_map:
            history_map[key] = {'calls': [], 'aht': []}
        
        # We store tuples of (date, value) to sort if needed
        history_map[key]['calls'].append((av.date, av.calls_offered))
        history_map[key]['aht'].append((av.date, av.aht_seconds))

    # 2. Generate for target range
    forecasts = []
    current = start_date
    
    # Weights for last 4 occurrences (Most recent -> Least recent)
    WEIGHTS = [0.4, 0.3, 0.2, 0.1] 
    
    while current <= end_date:
        wd = current.weekday()
        
        # Find unique times & queues existing in history for this weekday
        # Optimization: We could iterate 00:00-23:45, but let's stick to what we have data for vs full range.
        # Actually better to iterate full 24h range to ensure coverage if we have partial data.
        
        for h in range(24):
            for m in [0, 15, 30, 45]:
                t_val = time(h, m)
                
                # Identify queues that have ANY data for this WD/Time
                # This logic is a bit expensive in loop. 
                # Better: Pre-calculate the set of (queue, wd, time) keys.
                # But let's check history_map directly.
                
                # Get all unique queues from history map to iterate
                # (Ideally we'd use Queue.objects.all(), for now let's use data-driven)
                unique_queues = set([k[0] for k in history_map.keys()])
                
                for q_id in unique_queues:
                    # key = (q_id, wd, t_val)
                    
                    found_data = False
                    calls_hist = []
                    aht_hist = []
                    
                    # 1. Try Exact Match (Weekday + Time)
                    if key in history_map:
                         calls_hist = sorted(history_map[key]['calls'], key=lambda x: x[0], reverse=True)
                         aht_hist = sorted(history_map[key]['aht'], key=lambda x: x[0], reverse=True)
                         found_data = True
                    else:
                        # 2. Fallback: Try "Any Weekday" for this Time (General Pattern)
                        # Useful for sparse data (e.g. uploaded only Monday, trying to predict Tuesday)
                        fallback_calls = []
                        fallback_aht = []
                        for k, v in history_map.items():
                            # k = (q_id, wd, t)
                            if k[0] == q_id and k[2] == t_val:
                                fallback_calls.extend(v['calls'])
                                fallback_aht.extend(v['aht'])
                        
                        if fallback_calls:
                            calls_hist = sorted(fallback_calls, key=lambda x: x[0], reverse=True)
                            aht_hist = sorted(fallback_aht, key=lambda x: x[0], reverse=True)
                            found_data = True

                    if not found_data:
                        continue
                    
                    # Calculate Forecast Value
                    forecast_calls = 0
                    forecast_aht = 0
                    
                    if model_type == 'weighted_avg':
                        # Take last 4
                        sample_calls = [x[1] for x in calls_hist[:4]]
                        sample_aht = [x[1] for x in aht_hist[:4]]
                        
                        # Normalize weights if samples < 4
                        w_subset = WEIGHTS[:len(sample_calls)]
                        w_sum = sum(w_subset)
                        
                        if w_sum > 0:
                            forecast_calls = sum([s * w for s, w in zip(sample_calls, w_subset)]) / w_sum
                            forecast_aht = sum([s * w for s, w in zip(sample_aht, w_subset)]) / w_sum
                        else:
                            forecast_calls = 0 # Should not happen if len > 0
                            
                    else: # simple_avg
                        # Simple Mean
                        vals_c = [x[1] for x in calls_hist]
                        vals_a = [x[1] for x in aht_hist]
                        if vals_c:
                            forecast_calls = sum(vals_c) / len(vals_c)
                            forecast_aht = sum(vals_a) / len(vals_a)
                    
                    if forecast_calls > 0:
                        forecasts.append(CallVolume(
                            queue_id=q_id,
                            date=current,
                            interval_start=t_val,
                            calls_offered=int(round(forecast_calls)),
                            aht_seconds=int(round(forecast_aht)),
                            is_forecast=True
                        ))
                        
        current += timedelta(days=1)
        
    with transaction.atomic():
        CallVolume.objects.filter(is_forecast=True, date__range=(start_date, end_date)).delete()
        CallVolume.objects.bulk_create(forecasts)
        
    return len(forecasts)
