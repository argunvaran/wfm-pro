from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CallVolume, Queue
from shifts.models import Shift
from datetime import date, timedelta, datetime, time
import json
from django.contrib import messages
from .utils import aggregate_actuals, generate_forecast_data
# We need to import generate_schedule. Careful with circular imports.
# shifts/utils imports calls/models. calls/views imports shifts/utils.
# This loop: calls.views -> shifts.utils -> calls.models. (Safe)
# calls.views -> calls.models. (Safe)
from shifts.utils import generate_schedule

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
    
    active_shifts = Shift.objects.filter(date=today).count()
    
    # Chart Data (Last 7 days)
    chart_labels = []
    chart_data = []
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
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'dashboard.html', context)

@login_required
def forecast_view(request):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    if request.method == 'POST':
        if 'update_actuals' in request.POST:
            aggregate_actuals()
            messages.success(request, "Gerçekleşen veriler güncellendi.")
        elif 'generate_forecast' in request.POST:
            count = generate_forecast_data(start_of_week, end_of_week)
            messages.success(request, f"Tahmin oluşturuldu: {count} kayıt.")
        elif 'run_schedule' in request.POST:
            count = generate_schedule(None, start_of_week, end_of_week)
            messages.success(request, f"{count} vardiya atandı. Yönlendiriliyor...")
            return redirect('schedule')
        return redirect('forecast')

    # Chart Data Setup
    # We want to show Actuals vs Forecast for this week
    
    # Filter
    queue_id = request.POST.get('queue_id') or request.GET.get('queue_id')
    q_filter = {}
    if queue_id and queue_id.isdigit():
        q_filter['queue_id'] = int(queue_id)
    
    # Get all volumes
    vols = CallVolume.objects.filter(date__range=[start_of_week, end_of_week], **q_filter).order_by('date', 'interval_start')
    
    queues = Queue.objects.all()
    
    # Structure: timestamp -> {actual: 0, forecast: 0}
    data_map = {}
    
    for v in vols:
        dt_str = f"{v.date.strftime('%Y-%m-%d')} {v.interval_start.strftime('%H:%M')}"
        if dt_str not in data_map:
            data_map[dt_str] = {'actual': None, 'forecast': None}
        
        if v.is_forecast:
            data_map[dt_str]['forecast'] = (data_map[dt_str]['forecast'] or 0) + v.calls_offered
        else:
            data_map[dt_str]['actual'] = (data_map[dt_str]['actual'] or 0) + v.calls_offered
            
    labels = sorted(data_map.keys())
    actual_data = [data_map[k]['actual'] for k in labels]
    forecast_data = [data_map[k]['forecast'] for k in labels]
    
    context = {
        'start_date': start_of_week,
        'end_date': end_of_week,
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
