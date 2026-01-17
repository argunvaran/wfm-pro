from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Shift
from .utils import generate_schedule
from calls.utils import aggregate_actuals, generate_forecast_data
from calls.models import CallVolume
from agents.models import AgentProfile
from datetime import date, timedelta
from django.contrib import messages
from agents.utils import get_allowed_agents

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Shift
from .utils import generate_schedule
from calls.utils import aggregate_actuals, generate_forecast_data
from calls.models import CallVolume
from agents.models import AgentProfile
from datetime import date, timedelta
from django.contrib import messages
from django.http import JsonResponse
from .rta_utils import get_live_adherence_data

@login_required
def schedule_view(request):
    today = date.today()
    
    # Date Filtering
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str:
        try:
            start_of_week = date.fromisoformat(start_date_str)
        except ValueError:
            start_of_week = today - timedelta(days=today.weekday())
    else:
        start_of_week = today - timedelta(days=today.weekday())

    if end_date_str:
        try:
            end_of_week = date.fromisoformat(end_date_str)
        except ValueError:
             # Default to 7 days view if only start is given, or if no params
            end_of_week = start_of_week + timedelta(days=6)
    else:
        end_of_week = start_of_week + timedelta(days=6)


    if request.method == 'POST':
        if 'generate' in request.POST:
            # 1. Past Schedule Constraint
            if start_of_week < today:
                messages.error(request, "Hata: Geçmişe dönük vardiya ataması yapılamaz. Sadece ileri tarihler planlanabilir.")
                return redirect('schedule')

            # Generate Schedule Action (Re-run)
            count = generate_schedule(None, start_of_week, end_of_week) 
            messages.success(request, f"{count} shifts generated successfully.")
            return redirect('schedule')
            
    # RBAC: Get allowed agents
    agents = get_allowed_agents(request.user)
    
    # Search Filtering
    search_query = request.GET.get('q', '')
    if search_query:
        agents = agents.filter(user__username__icontains=search_query)

    # Search Filtering
    search_query = request.GET.get('q', '')
    if search_query:
        agents = agents.filter(user__username__icontains=search_query)

    # Optimization: Filter shifts only for allowed agents
    # But first, Pagination: Slice the agents list
    from django.core.paginator import Paginator
    paginator = Paginator(agents, 20) # 20 Agents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Use only paginated agents for further processing
    agents_page = page_obj.object_list
    
    # Filter shifts only for the VISIBLE agents on this page
    # This prevents loading all shifts for all agents
    shifts = Shift.objects.filter(date__range=[start_of_week, end_of_week], agent__in=agents_page).order_by('date', 'start_time')
    
    # Generate needed dates for headers
    delta = (end_of_week - start_of_week).days
    week_dates = [start_of_week + timedelta(days=i) for i in range(delta + 1)]
    
    schedule_table = []
    # Loop through the PAGINATED agents_page, not all agents
    for agent in agents_page:
        agent_row = {'agent': agent, 'shifts': []}
        for d in week_dates:
            s = shifts.filter(agent=agent, date=d).first()
            agent_row['shifts'].append(s)
        schedule_table.append(agent_row)

    context = {
        'week_dates': week_dates,
        'schedule_table': schedule_table,
        'start_date': start_of_week,
        'end_date': end_of_week,
        'page_obj': page_obj # Pass pagination object
    }
    return render(request, 'schedule.html', context)

@login_required
def rta_view(request):
    """
    Real-Time Adherence Dashboard (HTML)
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return JSON for AJAX poller
        data = get_live_adherence_data()
        return JsonResponse({'agents': data})
        
    # Initial Render
    context = {
        'initial_data': get_live_adherence_data()
    }
    return render(request, 'rta_dashboard.html', context)
