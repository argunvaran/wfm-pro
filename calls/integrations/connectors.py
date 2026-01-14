
from abc import ABC, abstractmethod
import json
from ..models import RealTimeEvent, RealTimeAgentState
from agents.models import AgentProfile
from django.utils import timezone
from datetime import datetime

class BaseConnector(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def process_event(self, data):
        """Processes raw event data and returns a normalized dictionary."""
        pass

class GenericConnector(BaseConnector):
    def process_event(self, data):
        # Generic API expects normalized JSON structure
        # { 
        #   "type": "agent_state", 
        #   "agent_id": "1001", 
        #   "state": "READY", 
        #   "timestamp": "ISO..." 
        # }
        return data

class AvayaConnector(BaseConnector):
    def process_event(self, data):
        # Mock logic for Avaya TSAPI XML/JSON translation
        normalized = {}
        # Example: <AgentState> ...
        if 'AgentState' in data:
            normalized['type'] = 'agent_state'
            normalized['agent_id'] = data.get('AgentID')
            normalized['state'] = self._map_state(data.get('State'))
        return normalized
    
    def _map_state(self, avaya_state):
        mapping = {'READY': 'Ready', 'AUX': 'Pause', 'ACD': 'Talking'}
        return mapping.get(avaya_state, 'Unknown')

# ... Other connectors ...

def handle_incoming_event(config, raw_data):
    """
    Main entry point for incoming webhook data.
    """
    connector = None
    if config.type == 'generic':
        connector = GenericConnector(config)
    elif config.type == 'avaya':
        connector = AvayaConnector(config)
    # ...
    
    if connector:
        normalized = connector.process_event(raw_data)
        if not normalized:
            return None
            
        # Log Event
        event = RealTimeEvent.objects.create(
            event_type=normalized.get('type', 'unknown'),
            agent_id=normalized.get('agent_id'),
            queue_id=normalized.get('queue_id'),
            payload=normalized,
            raw_data=raw_data
        )
        
        # Update Live State (Side Effect)
        if event.event_type == 'agent_state' and event.agent_id:
            try:
                profile = AgentProfile.objects.get(employee_id=event.agent_id)
                state, _ = RealTimeAgentState.objects.get_or_create(agent_profile=profile, defaults={'since': timezone.now()})
                state.state = normalized.get('state')
                state.since = timezone.now() # Update time on change
                state.save()
            except AgentProfile.DoesNotExist:
                pass # Log error
                
        return event
    return None
