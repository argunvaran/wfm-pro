from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from shifts.models import Shift
from calls.models import CallVolume, Call
from agents.models import AgentProfile
from django.db.models import Sum, Avg, Count
from datetime import date, timedelta
import csv
from django.http import HttpResponse

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
    
    # Simple Logic: Aggregate Calls per Agent
    # Since Call model links to AgentProfile
    
    data = []
    agents = AgentProfile.objects.all()
    
    for agent in agents:
        calls = Call.objects.filter(agent=agent, timestamp__date__range=[start_date, end_date])
        total_calls = calls.count()
        avg_handling_time = calls.aggregate(Avg('duration'))['duration__avg'] or 0
        
        # Shift Count
        shift_count = Shift.objects.filter(agent=agent, date__range=[start_date, end_date]).count()
        
        data.append({
            'agent': agent,
            'total_calls': total_calls,
            'avg_handling_time': round(avg_handling_time, 1),
            'shift_count': shift_count
        })
        
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
        'end_date': end_date
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
        'end_date': end_date
    }
    return render(request, 'reports/sla_report.html', context)
