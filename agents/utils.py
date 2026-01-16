from .models import AgentProfile

def get_allowed_agents(user):
    """
    Returns a QuerySet of AgentProfile objects that the given user is allowed to see.
    
    Rules:
    - Admin: All agents.
    - Manager: Agents in the manager's team.
    - Agent: Only themselves.
    """
    if not user.is_authenticated:
        return AgentProfile.objects.none()

    if user.role == 'admin' or user.is_superuser:
        return AgentProfile.objects.all()
    
    elif user.role == 'manager':
        # Manager sees their own team
        # Assuming manager has a profile linked to a team
        if hasattr(user, 'agent_profile') and user.agent_profile.team:
            return AgentProfile.objects.filter(team=user.agent_profile.team)
        # Fallback: if manager has no team, maybe they see nothing or just themselves?
        # Let's show themselves to avoid confusion
        return AgentProfile.objects.filter(user=user)
        
    else:
        # Regular agent sees only themselves
        return AgentProfile.objects.filter(user=user)
