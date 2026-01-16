from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AgentProfile, Team, Skill, ShiftType, ShiftTemplateActivity
from django.shortcuts import render, redirect, get_object_or_404
from calls.models import Queue
from django.contrib import messages
from django.db import transaction
import json
from django.http import JsonResponse
from .models import Department
from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def settings_view(request):
    # This import was incorrectly placed inside the function in the instruction.
    # It should be at the top of the file.
    # from django.db.models import Q
    # from django.core.paginator import Paginator
    skills = Skill.objects.all()
    queues = Queue.objects.all()
    shift_types = ShiftType.objects.all()
    # 'teams' variable is not defined here, assuming it's defined elsewhere or meant to be fetched.
    # For now, I'll assume it's meant to be `Team.objects.all()` for syntactic correctness.
    teams = Team.objects.all()
    return render(request, 'settings.html', {
        'teams': teams, 
        'skills': skills, 
        'queues': queues,
        'shift_types': shift_types
    })

# Simple Create Actions
@login_required
def create_team(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Team.objects.create(name=name)
            messages.success(request, f"Takım '{name}' oluşturuldu.")
    return redirect('settings')

@login_required
def create_skill(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Skill.objects.create(name=name)
            messages.success(request, f"Yetenek '{name}' oluşturuldu.")
    return redirect('settings')

@login_required
def create_queue(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Queue.objects.create(name=name)
            messages.success(request, f"Kuyruk '{name}' oluşturuldu.")
    return redirect('settings')

@login_required
def create_shift_type(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        duration = request.POST.get('duration_hours')
        start_min = request.POST.get('start_time_min')
        start_max = request.POST.get('start_time_max')
        
        # New Rule Inputs
        break_start = request.POST.get('break_start')
        break_duration = request.POST.get('break_duration')
        lunch_start = request.POST.get('lunch_start')
        lunch_duration = request.POST.get('lunch_duration')
        
        if name and duration:
            st = ShiftType.objects.create(
                name=name,
                duration_hours=float(duration),
                start_time_min=start_min or "08:00",
                start_time_max=start_max or "10:00"
            )
            
            # Create Lunch Rule if provided
            if lunch_start and lunch_duration:
                ShiftTemplateActivity.objects.create(
                    shift_type=st,
                    activity_type='LUNCH',
                    start_offset_minutes=int(lunch_start),
                    duration_minutes=int(lunch_duration)
                )

            # Create Break Rules (Multiple)
            break_starts = request.POST.getlist('break_start[]')
            break_durations = request.POST.getlist('break_duration[]')
            
            for start, duration in zip(break_starts, break_durations):
                if start and duration:
                    ShiftTemplateActivity.objects.create(
                        shift_type=st,
                        activity_type='BREAK',
                        start_offset_minutes=int(start),
                        duration_minutes=int(duration)
                    )

            messages.success(request, f"Vardiya Tipi '{name}' ve kuralları oluşturuldu.")
    return redirect('settings')

@login_required
def edit_shift_type(request, pk):
    st = get_object_or_404(ShiftType, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_type':
            st.name = request.POST.get('name')
            st.duration_hours = float(request.POST.get('duration_hours'))
            st.start_time_min = request.POST.get('start_time_min')
            st.start_time_max = request.POST.get('start_time_max')
            st.save()
            messages.success(request, "Vardiya tipi güncellendi.")
            
        elif action == 'delete_type':
            st.delete()
            messages.success(request, "Vardiya tipi silindi.")
            return redirect('settings')
            
        elif action == 'add_activity':
            ShiftTemplateActivity.objects.create(
                shift_type=st,
                activity_type=request.POST.get('activity_type'),
                start_offset_minutes=int(request.POST.get('start_offset')),
                duration_minutes=int(request.POST.get('duration'))
            )
            messages.success(request, "Aktivite eklendi.")
            
        elif action == 'delete_activity':
            act_id = request.POST.get('activity_id')
            ShiftTemplateActivity.objects.filter(id=act_id).delete()
            messages.success(request, "Aktivite silindi.")
            
        return redirect('edit_shift_type', pk=pk)

    activities = st.template_activities.all()
    return render(request, 'shift_config.html', {'shift_type': st, 'activities': activities})


from .utils import get_allowed_agents

@login_required
def agent_list(request):
    query = request.GET.get('q', '')
    show_inactive = request.GET.get('show_inactive', 'false') == 'true'
    
    # RBAC: Get base queryset allowed for this user
    agents = get_allowed_agents(request.user).select_related('team__department', 'user')

    # Search
    if query:
        agents = agents.filter(user__username__icontains=query)
    
    # Active/Inactive Filter
    if not show_inactive:
        agents = agents.filter(user__is_active=True)
    
    # Ordering
    agents = agents.order_by('user__username')
    
    # Pagination
    paginator = Paginator(agents, 20) # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': query,
        'show_inactive': show_inactive
    }
    return render(request, 'agents.html', context)



from .models import AgentProfile, Team, Department, Skill, ShiftType, ShiftTemplateActivity
from django.http import JsonResponse
import json

@login_required
def org_chart_view(request):
    departments = Department.objects.prefetch_related('teams__agentprofile_set').all()
    
    # Teams with no department (Unassigned Teams)
    unassigned_teams = Team.objects.filter(department__isnull=True).prefetch_related('agentprofile_set')
    
    # Agents with no team (Unassigned Agents)
    unassigned_agents = AgentProfile.objects.filter(team__isnull=True)
    
    context = {
        'departments': departments,
        'unassigned_teams': unassigned_teams,
        'unassigned_agents': unassigned_agents
    }
    return render(request, 'org_chart.html', context)

@login_required
def agent_detail_view(request, pk):
    agent = get_object_or_404(AgentProfile, pk=pk)
    
    # Permission Check (Who can EDIT?)
    # Admin: Yes
    # Manager: Only if it's their team member
    # Agent: No
    can_edit = False
    if request.user.role == 'admin' or request.user.is_superuser:
        can_edit = True
    elif request.user.role == 'manager':
        # Check if manager's team matches agent's team
        try:
            if request.user.agent_profile.team == agent.team:
                can_edit = True
        except: pass
        
    if request.method == 'POST':
        if not can_edit:
            messages.error(request, "Bu işlemi yapmaya yetkiniz yok.")
            return redirect('agent_detail', pk=pk)
            
        action = request.POST.get('action')
        
        if action == 'update_info':
            # Update basic info
            agent.employee_id = request.POST.get('employee_id')
            agent.hire_date = request.POST.get('hire_date') or None
            agent.save()
            
            # Update User fields if needed (e.g. Email)
            user = agent.user
            user.email = request.POST.get('email')
            user.save()
            
            messages.success(request, "Bilgiler güncellendi.")
            
        elif action == 'update_role':
            # RBAC Check: STRICTLY Admin only
            if not (request.user.role == 'admin' or request.user.is_superuser):
                messages.error(request, "Rol değiştirme yetkiniz yok.")
                return redirect('agent_detail', pk=pk)
                
            new_role = request.POST.get('role')
            if new_role not in ['admin', 'manager', 'agent']:
                messages.error(request, "Geçersiz rol.")
            else:
                agent.user.role = new_role
                agent.user.save()
                messages.success(request, f"Kullanıcı rolü '{new_role}' olarak güncellendi.")
        
        return redirect('agent_detail', pk=pk)

    context = {
        'agent': agent,
        'can_edit': can_edit
    }
    return render(request, 'agent_detail.html', context)

@login_required
def update_hierarchy(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Support both single item (legacy/fallback) and list (batch)
            items = data if isinstance(data, list) else [data]
            
            with transaction.atomic():
                for item in items:
                    item_type = item.get('item_type') # 'team' or 'agent'
                    item_id = item.get('item_id')
                    parent_type = item.get('parent_type') # 'department', 'team', or 'none'
                    parent_id = item.get('parent_id')
                    
                    if item_type == 'team':
                        team = Team.objects.get(id=item_id)
                        if parent_type == 'department' and parent_id and parent_id != 'none':
                            dept = Department.objects.get(id=parent_id)
                            team.department = dept
                        else:
                            team.department = None
                        team.save()
                        
                    elif item_type == 'agent':
                        agent = AgentProfile.objects.get(id=item_id)
                        if parent_type == 'team' and parent_id and parent_id != 'none':
                            team = Team.objects.get(id=parent_id)
                            agent.team = team
                        else:
                            agent.team = None
                        agent.save()
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid Method'}, status=405)

@login_required
def create_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Department.objects.create(name=name)
            messages.success(request, f"Departman '{name}' oluşturuldu.")
    return redirect('org_chart')

@login_required
def user_management_view(request):
    # Strictly Admin Only
    if not (request.user.role == 'admin' or request.user.is_superuser):
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        
        if action == 'update_role' and user_id and new_role:
            try:
                from users.models import User
                u = User.objects.get(id=user_id)
                if new_role in ['admin', 'manager', 'agent']:
                    u.role = new_role
                    # Auto-promote to Staff if Admin
                    u.is_staff = (new_role == 'admin')
                    u.save()
                    messages.success(request, f"{u.username} kullanıcısının rolü güncellendi.")
                else:
                    messages.error(request, "Geçersiz rol.")
            except User.DoesNotExist:
                messages.error(request, "Kullanıcı bulunamadı.")
                
        elif action == 'create_profile' and user_id:
            try:
                from users.models import User
                from agents.models import AgentProfile
                u = User.objects.get(id=user_id)
                if not hasattr(u, 'agent_profile'):
                    AgentProfile.objects.create(user=u)
                    messages.success(request, f"{u.username} için profil oluşturuldu.")
                else:
                    messages.warning(request, "Profil zaten mevcut.")
            except Exception as e:
                messages.error(request, f"Hata: {str(e)}")
        
        elif action == 'update_managed_teams':
            try:
                from agents.models import Team, AgentProfile
                u = User.objects.get(id=user_id)
                profile, _ = AgentProfile.objects.get_or_create(user=u) # Ensure profile
                
                team_ids = request.POST.getlist('team_ids') # Expecting list of IDs
                profile.managed_teams.set(team_ids)
                profile.save()
                messages.success(request, f"{u.username} için yönetilen takımlar güncellendi.")
            except Exception as e:
                messages.error(request, f"Hata: {str(e)}")

        return redirect('user_management')
        
    # List all users
    from users.models import User
    from agents.models import Team
    
    # 3. Base Query
    users_list = User.objects.all().select_related('agent_profile').order_by('username')
    
    # 4. Search Filter
    search_query = request.GET.get('q', '')
    if search_query:
        users_list = users_list.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # 5. Pagination
    paginator = Paginator(users_list, 20) # 20 users per page
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    all_teams = Team.objects.select_related('department').order_by('department__name', 'name')
    context = {
        'users': users,
        'all_teams': all_teams,
        'search_query': search_query
    }
    return render(request, 'user_list.html', context)
