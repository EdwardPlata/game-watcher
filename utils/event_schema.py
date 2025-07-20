"""
Event schema definitions and validation utilities.
"""

from typing import Dict, List, Any
from datetime import datetime
import json


# Event schema template
EVENT_SCHEMA = {
    "sport": "",
    "date": "",  # ISO format: "2025-07-20T18:00:00Z"
    "event": "",
    "participants": [],
    "location": "",
    "leagues": []  # List of leagues/tags this event belongs to
}


def validate_event(event: Dict[str, Any]) -> bool:
    """
    Validate an event dictionary against the schema.
    
    Args:
        event: Event dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["sport", "date", "event", "participants", "location"]
    
    # Check all required fields are present
    for field in required_fields:
        if field not in event:
            return False
    
    # Validate data types
    if not isinstance(event["sport"], str):
        return False
    if not isinstance(event["date"], str):
        return False
    if not isinstance(event["event"], str):
        return False
    if not isinstance(event["participants"], list):
        return False
    if not isinstance(event["location"], str):
        return False
    
    # Validate leagues field (optional)
    if "leagues" in event and not isinstance(event["leagues"], list):
        return False
    
    # Validate date format (basic check)
    try:
        datetime.fromisoformat(event["date"].replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return False
    
    return True


def create_event(sport: str, date: str, event: str, participants: List[str], location: str, leagues: List[str] = None) -> Dict[str, Any]:
    """
    Create a standardized event dictionary.
    
    Args:
        sport: Sport name
        date: ISO formatted date string
        event: Event description
        participants: List of participants
        location: Event location
        leagues: List of leagues/tags this event belongs to
    
    Returns:
        Validated event dictionary
    """
    event_dict = {
        "sport": sport,
        "date": date,
        "event": event,
        "participants": participants,
        "location": location,
        "leagues": leagues or []
    }
    
    if not validate_event(event_dict):
        raise ValueError("Invalid event data")
    
    return event_dict
