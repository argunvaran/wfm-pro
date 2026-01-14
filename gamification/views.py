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
    
    leaderboard = []
    users = User.objects.filter(is_active=True)
    for u in users:
        pts = UserBadge.objects.filter(user=u).aggregate(Sum('badge__points'))['badge__points__sum'] or 0
        if pts > 0:
            leaderboard.append({'user': u, 'points': pts})
            
    # Sort by points desc
    leaderboard.sort(key=lambda x: x['points'], reverse=True)
    
    context = {
        'my_badges': my_badges,
        'total_points': total_points,
        'leaderboard': leaderboard[:10] # Top 10
    }
    return render(request, 'gamification/dashboard.html', context)
