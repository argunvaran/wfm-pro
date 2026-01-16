from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CallVolume, Queue, Call
from shifts.models import Shift
from datetime import date, timedelta, datetime, time
from django.db.models import Sum, Avg, Count
import json
from django.contrib import messages
from .utils import aggregate_actuals, generate_forecast_data
# We need to import generate_schedule. Careful with circular imports.
# shifts/utils imports calls/models. calls/views imports shifts/utils.
# This loop: calls.views -> shifts.utils -> calls.models. (Safe)
# calls.views -> calls.models. (Safe)
from shifts.utils import generate_schedule
from agents.utils import get_allowed_agents

@login_required
def dashboard(request):
    # Public tenant check -> Serve Landing Page
    if request.tenant.schema_name == 'public':
        return render(request, 'landing.html')

    today = date.today()
    # Metrics
    # Only sum Actuals (is_forecast=False)
    vols = CallVolume.objects.filter(date=today, is_forecast=False)
    total_offered = sum([v.calls_offered for v in vols])
    
    # RBAC: Active shifts count scoped to user visibility
    allowed_agents = get_allowed_agents(request.user)
    active_shifts = Shift.objects.filter(date=today, agent__in=allowed_agents).count()
    
    # RBAC: Personal/Team Stats (for Non-Admins)
    personal_call_count = 0
    personal_avg_duration = 0
    
    if request.user.role != 'admin' and not request.user.is_superuser:
        # Last 7 Days
        start_date = today - timedelta(days=6)
        stats = Call.objects.filter(
            agent__in=allowed_agents,
            timestamp__date__range=[start_date, today]
        ).aggregate(
            total_calls=Count('id'),
            avg_duration=Avg('duration')
        )
        personal_call_count = stats['total_calls'] or 0
        personal_avg_duration = int(stats['avg_duration'] or 0)

    # Chart Data (Last 7 days) - ADMIN ONLY Calculation (Optimization)
    chart_labels = []
    chart_data = []
    
    if request.user.role == 'admin' or request.user.is_superuser:
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime('%Y-%m-%d'))
            vs = CallVolume.objects.filter(date=d, is_forecast=False)
            s = sum([v.calls_offered for v in vs])
            chart_data.append(s)

    context = {
        'total_offered': total_offered,
        'active_shifts': active_shifts,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'personal_call_count': personal_call_count,
        'personal_avg_duration': personal_avg_duration,
    }
    return render(request, 'dashboard.html', context)

@login_required
def forecast_view(request):
    # Date Params
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = date.today()
    
    # Default to current week if not provided
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=today.weekday())
        
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = start_date + timedelta(days=6)
    
    if request.method == 'POST':
        if 'update_actuals' in request.POST:
            aggregate_actuals()
            messages.success(request, "Gerçekleşen veriler güncellendi.")
        elif 'generate_forecast' in request.POST:
            count = generate_forecast_data(start_date, end_date)
            messages.success(request, f"Tahmin oluşturuldu: {count} kayıt.")
        elif 'run_schedule' in request.POST:
            count = generate_schedule(None, start_date, end_date)
            messages.success(request, f"{count} vardiya atandı. Yönlendiriliyor...")
            return redirect('schedule')
        
        # Redirect with params to keep state
        return redirect(f"{request.path}?start_date={start_date}&end_date={end_date}")

    # Chart Data Setup
    queue_id = request.POST.get('queue_id') or request.GET.get('queue_id')
    q_filter = {}
    if queue_id and queue_id.isdigit():
        q_filter['queue_id'] = int(queue_id)
    
    # Get all volumes
    vols = CallVolume.objects.filter(date__range=[start_date, end_date], **q_filter).order_by('date', 'interval_start')
    
    queues = Queue.objects.all()
    
    # Structure: Key -> {actual: 0, forecast: 0}
    data_map = {}
    
    is_daily_view = (start_date != end_date)
    
    for v in vols:
        if is_daily_view:
            # Daily Aggregation
            key = v.date.strftime('%Y-%m-%d')
        else:
            # Intraday
            key = v.interval_start.strftime('%H:%M')
            
        if key not in data_map:
            data_map[key] = {'actual': 0, 'forecast': 0}
        
        if v.is_forecast:
            data_map[key]['forecast'] = (data_map[key]['forecast'] or 0) + v.calls_offered
        else:
            data_map[key]['actual'] = (data_map[key]['actual'] or 0) + v.calls_offered
            
    labels = sorted(data_map.keys())
    actual_data = [data_map[k]['actual'] for k in labels]
    forecast_data = [data_map[k]['forecast'] for k in labels]
    
    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'labels': labels,
        'actual_data': actual_data,
        'forecast_data': forecast_data,
        'queues': queues,
        'selected_queue_id': int(queue_id) if queue_id and queue_id.isdigit() else None
    }
    return render(request, 'forecast.html', context)

@login_required
def heatmap_view(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    today = date.today()
    start_date = today
    end_date = today
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except: pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except: pass
    
    # 00:00 to 23:45 headers (96 intervals)
    time_headers = []
    for h in range(24):
        for m in [0, 15, 30, 45]:
            time_headers.append(time(h, m).strftime("%H:%M"))
            
    # Fetch Data
    # Fetch Data
    
    # Queue Filter
    queue_id = request.GET.get('queue_id')
    queue_filter = {}
    if queue_id and queue_id.isdigit():
        queue_filter['queue_id'] = int(queue_id)
        
    vols = CallVolume.objects.filter(
        date__range=[start_date, end_date], 
        is_forecast=False,
        **queue_filter
    ).order_by('date', 'interval_start')
    
    # Get Queues for Dropdown
    queues = Queue.objects.all()
    
    # Data Structure: Date -> Time -> Sum
    data_map = {}
    
    for v in vols:
        d_key = v.date
        t_key = v.interval_start.strftime("%H:%M")
        
        if d_key not in data_map:
            data_map[d_key] = {}
        
        # Sum if multiple queues
        data_map[d_key][t_key] = data_map[d_key].get(t_key, 0) + v.calls_offered

    # Build Rows
    table_rows = []
    current = start_date
    while current <= end_date:
        row = {'date': current, 'cells': []}
        day_total = 0
        d_data = data_map.get(current, {})
        
        for t_label in time_headers:
            val = d_data.get(t_label, 0)
            day_total += val
            # Color intensity class logic could be done here or in template
            # Let's pass raw value
            row['cells'].append(val)
            
        row['total'] = day_total
        table_rows.append(row)
        current += timedelta(days=1)

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'time_headers': time_headers,
        'table_rows': table_rows,
        'queues': queues,
        'selected_queue_id': int(queue_id) if queue_id and queue_id.isdigit() else None
    }
    return render(request, 'heatmap.html', context)
from .models import CallVolume, Queue, IntegrationConfig
import uuid

@login_required
def integration_view(request):
    config = IntegrationConfig.objects.first()
    
    if request.method == 'POST':
        if 'create_default' in request.POST and not config:
            config = IntegrationConfig.objects.create(
                name="Default Integration",
                type='generic',
                api_key=str(uuid.uuid4())
            )
            messages.success(request, "API Anahtarı oluşturuldu.")
            
    context = {
        'config': config
    }
    return render(request, 'integrations.html', context)
