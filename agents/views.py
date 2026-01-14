from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AgentProfile, Team, Skill
from django.shortcuts import render, redirect
from calls.models import Queue
from django.contrib import messages

@login_required
def settings_view(request):
    teams = Team.objects.all()
    skills = Skill.objects.all()
    queues = Queue.objects.all()
    return render(request, 'settings.html', {'teams': teams, 'skills': skills, 'queues': queues})

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
def agent_list(request):
    agents = AgentProfile.objects.all()
    return render(request, 'agents.html', {'agents': agents})
