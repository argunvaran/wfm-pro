from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Badge, UserBadge
from users.models import User
from django.db.models import Sum

@login_required
def gamification_dashboard(request):
    """
    My Badges & Leaderboard
    """
    # My Badges
    my_badges = UserBadge.objects.filter(user=request.user)
    total_points = my_badges.aggregate(Sum('badge__points'))['badge__points__sum'] or 0
    
    # Leaderboard
    # This is a bit complex in pure SQL because points are in the related Badge model
    # Simpler approach: Get all users, annotate with sum of badge points
    
    # Leaderboard
    leaderboard = []
    
    # RBAC: Filter Users for Leaderboard
    if request.user.role == 'manager':
        # Manager: See Team Members
        try:
            team = request.user.agent_profile.team
            users = User.objects.filter(is_active=True, agent_profile__team=team)
        except:
            users = User.objects.none()
    elif request.user.role == 'agent':
        # Agent: See Team (Optional) or Just Self + Top? 
        # Requirement: "agent için orda görevler tamamlaması halinde rozet kazanması gibi baya aktif bir alan olmalı"
        # Usually agents want to compete with team. Let's show Team leaderboard for agents too.
        try:
            team = request.user.agent_profile.team
            users = User.objects.filter(is_active=True, agent_profile__team=team)
        except:
            users = User.objects.none()
    else:
        # Admin: All
        users = User.objects.filter(is_active=True)
        
    for u in users:
        pts = UserBadge.objects.filter(user=u).aggregate(Sum('badge__points'))['badge__points__sum'] or 0
        leaderboard.append({'user': u, 'points': pts})
            
    # Sort by points desc
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    context = {
        'my_badges': my_badges,
        'total_points': total_points,
        'leaderboard': leaderboard[:10] # Top 10
    }
    return render(request, 'gamification/dashboard.html', context)
