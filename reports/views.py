from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from shifts.models import Shift
from calls.models import CallVolume, Call
from agents.models import AgentProfile
from django.db.models import Sum, Avg, Count, Max
from django.db import models
from datetime import date, timedelta
import csv
from django.http import HttpResponse
import json

@login_required
def report_dashboard(request):
    """
    Main landing page for reports.
    """
    return render(request, 'reports/dashboard.html')

@login_required
def agent_performance_report(request):
    """
    Agent Performance: Total Calls, Avg Duration, Shift Adherence (Mock)
    """
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    data = []
    agents = AgentProfile.objects.select_related('user').all()
    
    # Chart Data Arrays
    chart_labels = []
    chart_calls = []
    chart_aht = []
    
    for agent in agents:
        calls = Call.objects.filter(agent=agent, timestamp__date__range=[start_date, end_date])
        total_calls = calls.count()
        avg_handling_time = calls.aggregate(Avg('duration'))['duration__avg'] or 0
        
        shift_count = Shift.objects.filter(agent=agent, date__range=[start_date, end_date]).count()
        
        # Only add valid stats to display
        if total_calls > 0 or shift_count > 0:
            data.append({
                'agent': agent,
                'total_calls': total_calls,
                'avg_handling_time': round(avg_handling_time, 1),
                'shift_count': shift_count
            })
            
    # Sort for Charts (Top 10 by calls)
    sorted_data = sorted(data, key=lambda x: x['total_calls'], reverse=True)
    for row in sorted_data[:10]:
        chart_labels.append(f"{row['agent'].user.first_name}")
        chart_calls.append(row['total_calls'])
        chart_aht.append(row['avg_handling_time'])

    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="agent_performance_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Agent', 'Total Calls', 'Avg AHT (sec)', 'Shifts'])
        for row in data:
            writer.writerow([f"{row['agent'].user.first_name} {row['agent'].user.last_name}", row['total_calls'], row['avg_handling_time'], row['shift_count']])
            
        return response

    context = {
        'data': data,
        'start_date': start_date,
        'end_date': end_date,
        'chart_labels': json.dumps(chart_labels),
        'chart_calls': json.dumps(chart_calls),
        'chart_aht': json.dumps(chart_aht),
    }
    return render(request, 'reports/agent_performance.html', context)

@login_required
def sla_report(request):
    """
    Daily SLA Report based on CallVolume actuals.
    """
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    vols = CallVolume.objects.filter(date__range=[start_date, end_date], is_forecast=False).values('date').annotate(
        total_offered=Sum('calls_offered'),
        avg_aht=Avg('aht_seconds')
    ).order_by('date')
    
    # Chart Data
    chart_dates = []
    chart_offered = []
    chart_aht = []
    
    for v in vols:
        chart_dates.append(v['date'].strftime('%d-%m'))
        chart_offered.append(v['total_offered'])
        chart_aht.append(int(v['avg_aht'] or 0))
    
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sla_report_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Total Calls', 'Avg AHT'])
        for row in vols:
            writer.writerow([row['date'], row['total_offered'], row['avg_aht']])
        return response

    context = {
        'data': vols,
        'start_date': start_date,
        'end_date': end_date,
        'chart_dates': json.dumps(chart_dates),
        'chart_offered': json.dumps(chart_offered),
        'chart_aht': json.dumps(chart_aht),
    }
    return render(request, 'reports/sla_report.html', context)

@login_required
def adherence_report(request):
    """
    Adherence Report: Comparison of planned shift vs actual logged logic (Mocked).
    """
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    # Mock Calculation: 
    # Adherence = (Random % between 85-99 for demo purposes as we don't have full biometric logs)
    # Real implementation would sum up RealTimeAgentState durations vs ShiftType duration.
    
    import random
    
    data = []
    agents = AgentProfile.objects.select_related('user').all()
    
    for agent in agents:
        shift_days = Shift.objects.filter(agent=agent, date__range=[start_date, end_date]).count()
        if shift_days > 0:
            # Mock Adherence Data
            adherence_score = random.randint(80, 99) 
            data.append({
                'agent': agent,
                'shifts': shift_days,
                'adherence': adherence_score,
                'efficiency': min(100, adherence_score + random.randint(-5, 5))
            })

    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="adherence_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Agent', 'Shifts', 'Adherence %', 'Efficiency %'])
        for row in data:
            writer.writerow([row['agent'].user.get_full_name(), row['shifts'], row['adherence'], row['efficiency']])
        return response

    context = {
        'data': data,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'reports/adherence_report.html', context)

@login_required
def customer_journey_report(request):
    """
    Admin Only: Analyze customer repeat calls for the current month.
    """
    if not request.user.is_superuser:
        return render(request, '403.html', {'message': 'Bu raporu görüntüleme yetkiniz yok.'}, status=403)
        
    start_date = request.GET.get('start_date', date.today().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    # 1. Aggregate calls by customer
    # Exclude null or empty customer numbers
    customer_stats = Call.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).exclude(
        customer_number__isnull=True
    ).exclude(
        customer_number=''
    ).values('customer_number').annotate(
        total_calls=Count('id'),
        total_duration=Sum('duration'),
        last_call=models.Max('timestamp')
    ).order_by('-total_calls')
    
    # 2. Add details for repeat callers (more than 1 call)
    data = []
    for stat in customer_stats:
        if stat['total_calls'] > 1:
            stat['is_repeat'] = True
            stat['avg_duration'] = round(stat['total_duration'] / stat['total_calls'], 1)
        else:
            stat['is_repeat'] = False
            stat['avg_duration'] = stat['total_duration']
        data.append(stat)

    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="customer_journey_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Customer Number', 'Total Calls', 'Total Duration', 'Avg Duration', 'Last Call', 'Repeat Status'])
        for row in data:
            status = "Repeat Caller" if row['is_repeat'] else "Single Call"
            writer.writerow([row['customer_number'], row['total_calls'], row['total_duration'], row['avg_duration'], row['last_call'], status])
        return response

    # 3. Pagination
    if 'export' not in request.GET:
        from django.core.paginator import Paginator
        paginator = Paginator(data, 20) # Show 20 contacts per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        data = page_obj # Update data context to be the page object

    context = {
        'data': data,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'reports/customer_journey.html', context)

@login_required
def queue_performance_report(request):
    """
    Queue Breakdwon: Calls by Queue/Campaign.
    """
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    # Aggregate by Queue
    # If queue is null, label as 'Unassigned'
    stats = Call.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).values('queue__name').annotate(
        total_calls=Count('id'),
        avg_aht=Avg('duration'),
        total_duration=Sum('duration')
    ).order_by('-total_calls')
    
    data = []
    total_volume = 0
    
    # Calculate totals first for percentage
    for s in stats:
        total_volume += s['total_calls']

    chart_labels = []
    chart_data = []

    for s in stats:
        name = s['queue__name'] or 'Genel (Tanımsız)'
        percent = (s['total_calls'] / total_volume * 100) if total_volume > 0 else 0
        data.append({
            'name': name,
            'total_calls': s['total_calls'],
            'avg_aht': round(s['avg_aht'] or 0, 1),
            'percent': round(percent, 1)
        })
        chart_labels.append(name)
        chart_data.append(s['total_calls'])

    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="queue_performance_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Queue Name', 'Total Calls', 'Avg AHT', 'Volume %'])
        for row in data:
            writer.writerow([row['name'], row['total_calls'], row['avg_aht'], row['percent']])
        return response

    context = {
        'data': data,
        'start_date': start_date,
        'end_date': end_date,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'reports/queue_performance.html', context)

@login_required
def hourly_traffic_report(request):
    """
    Heatmap: Calls aggregated by Hour of Day (0-23).
    """
    start_date = request.GET.get('start_date', (date.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
    
    from django.db.models.functions import ExtractHour
    
    # Group by Hour
    hourly_stats = Call.objects.filter(
        timestamp__date__range=[start_date, end_date]
    ).annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        total_calls=Count('id'),
        avg_aht=Avg('duration')
    ).order_by('hour')
    
    # Normalize to ensure all 24 hours exist
    data_map = {x['hour']: x for x in hourly_stats}
    data = []
    
    chart_hours = []
    chart_calls = []
    
    max_vol = 0
    for h in range(24):
        stat = data_map.get(h, {'total_calls': 0, 'avg_aht': 0})
        vol = stat['total_calls']
        if vol > max_vol: max_vol = vol
        
        data.append({
            'hour_label': f"{h:02d}:00 - {h:02d}:59",
            'hour_int': h,
            'total_calls': vol,
            'avg_aht': round(stat['avg_aht'] or 0, 0)
        })
        chart_hours.append(f"{h:02d}")
        chart_calls.append(vol)

    # Add Intensity Score (0-100) for UI Heatmap
    for row in data:
        row['intensity'] = int((row['total_calls'] / max_vol * 100)) if max_vol > 0 else 0

    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="hourly_traffic_{start_date}_{end_date}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Hour Invoice', 'Total Calls', 'Avg AHT'])
        for row in data:
            writer.writerow([row['hour_label'], row['total_calls'], row['avg_aht']])
        return response

    context = {
        'data': data,
        'start_date': start_date,
        'end_date': end_date,
        'chart_hours': json.dumps(chart_hours),
        'chart_calls': json.dumps(chart_calls)
    }
    return render(request, 'reports/hourly_traffic.html', context)
