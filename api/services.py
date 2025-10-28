"""
API service layer for decoupling frontend and backend.

This module provides a clean interface between the frontend routes and backend API,
making it easier to maintain and potentially migrate to a separate frontend application.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import json

from utils import DatabaseManager, get_logger
from collectors import COLLECTORS, get_collector
from collectors.betting import BettingOddsCollector

logger = get_logger(__name__)


def _parse_event_date(event: Dict[str, Any]) -> Optional[date]:
    """
    Parse event date from various formats.
    
    Args:
        event: Event dictionary containing 'date' field
    
    Returns:
        Parsed date object or None if parsing fails
    """
    try:
        date_str = event['date'].replace('Z', '+00:00')
        return datetime.fromisoformat(date_str).date()
    except (ValueError, KeyError, AttributeError):
        return None


class EventsService:
    """Service for handling event-related operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_all_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all events from database."""
        return self.db.get_all_events(limit=limit)
    
    def get_events_by_sport(self, sport: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get events for a specific sport."""
        return self.db.get_events_by_sport(sport, limit=limit)
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific event by ID."""
        return self.db.get_event_by_id(event_id)
    
    def get_events_by_date_range(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get events within a date range, optionally filtered by sport."""
        if sport:
            events = self.get_events_by_sport(sport)
        else:
            events = self.get_all_events()
        
        # Filter by date range
        if start_date or end_date:
            filtered_events = []
            for event in events:
                event_date = _parse_event_date(event)
                if event_date is None:
                    continue
                if start_date and event_date < start_date:
                    continue
                if end_date and event_date > end_date:
                    continue
                filtered_events.append(event)
            return filtered_events
        
        return events
    
    def get_events_for_day(
        self,
        target_date: date,
        sport: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all events for a specific day."""
        if sport:
            events = self.get_events_by_sport(sport)
        else:
            events = self.get_all_events()
        
        day_events = []
        for event in events:
            event_date = _parse_event_date(event)
            if event_date == target_date:
                day_events.append(event)
        
        # Sort by time
        day_events.sort(key=lambda x: x.get('date', ''))
        return day_events
    
    def group_events_by_date(self, events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group events by date."""
        events_by_date = {}
        for event in events:
            event_date = _parse_event_date(event)
            if event_date is not None:
                date_str = event_date.isoformat()
                if date_str not in events_by_date:
                    events_by_date[date_str] = []
                events_by_date[date_str].append(event)
        return events_by_date
    
    def normalize_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data for consistent output."""
        # Parse participants JSON if it's a string
        participants = event.get('participants', [])
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except (json.JSONDecodeError, TypeError):
                participants = [participants] if participants else []
        
        # Parse leagues JSON if it's a string
        leagues = event.get('leagues', [])
        if isinstance(leagues, str):
            try:
                leagues = json.loads(leagues)
            except (json.JSONDecodeError, TypeError):
                leagues = [leagues] if leagues else []
        
        return {
            'id': event['id'],
            'sport': event['sport'],
            'date': event['date'],
            'event': event['event'],
            'participants': participants,
            'location': event['location'],
            'leagues': leagues,
            'watch_link': event.get('watch_link'),
            'scraped_at': event['scraped_at']
        }


class CollectionService:
    """Service for handling data collection operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def collect_sport_data(self, sport: str) -> Dict[str, Any]:
        """Collect data for a specific sport."""
        try:
            start_time = datetime.now()
            
            # Get collector
            collector = get_collector(sport)
            
            # Fetch events
            events = collector.fetch_events()
            
            # Store in database
            new_events = self.db.insert_events(events)
            
            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'sport': sport,
                'events_collected': len(events),
                'new_events': new_events,
                'updated_events': len(events) - new_events,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to collect {sport} data: {e}")
            return {
                'sport': sport,
                'events_collected': 0,
                'new_events': 0,
                'updated_events': 0,
                'duration_seconds': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def collect_all_sports(self) -> Dict[str, Any]:
        """Collect data for all supported sports."""
        start_time = datetime.now()
        results = {}
        
        for sport in COLLECTORS.keys():
            result = self.collect_sport_data(sport)
            results[sport] = result
        
        duration = (datetime.now() - start_time).total_seconds()
        total_events = sum(r['events_collected'] for r in results.values())
        total_new = sum(r['new_events'] for r in results.values())
        
        return {
            'results': results,
            'total_events_collected': total_events,
            'total_new_events': total_new,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        }


class BettingOddsService:
    """Service for handling betting odds operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.collector = BettingOddsCollector()
    
    def get_all_odds(self) -> List[Dict[str, Any]]:
        """Get all betting odds."""
        return self.db.get_all_betting_odds()
    
    def get_odds_for_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get betting odds for a specific event."""
        return self.db.get_odds_for_event(event_id)
    
    def collect_betting_odds(self) -> Dict[str, Any]:
        """Collect betting odds for upcoming events."""
        try:
            start_time = datetime.now()
            
            # Fetch odds
            odds_data = self.collector.fetch_events()
            
            # Store in database
            inserted = 0
            for odds in odds_data:
                self.db.insert_betting_odds(odds)
                inserted += 1
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'odds_collected': len(odds_data),
                'odds_inserted': inserted,
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to collect betting odds: {e}")
            return {
                'odds_collected': 0,
                'odds_inserted': 0,
                'duration_seconds': 0,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }


class SportsService:
    """Service for handling sports-related operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_all_sports(self) -> List[Dict[str, Any]]:
        """Get list of all supported sports with statistics."""
        sports = []
        
        for sport_key in COLLECTORS.keys():
            try:
                # Get event count
                events = self.db.get_events_by_sport(sport_key)
                total_events = len(events)
                
                # Get last update time
                last_updated = None
                if events:
                    last_updated = max(event.get('scraped_at', '') for event in events)
                
                sports.append({
                    'name': sport_key,
                    'display_name': sport_key.upper(),
                    'description': f"{sport_key.title()} schedule and events",
                    'total_events': total_events,
                    'last_updated': last_updated
                })
                
            except Exception as e:
                logger.error(f"Error getting stats for {sport_key}: {e}")
                sports.append({
                    'name': sport_key,
                    'display_name': sport_key.upper(),
                    'description': f"{sport_key.title()} schedule and events",
                    'total_events': 0,
                    'last_updated': None
                })
        
        return sports
    
    def get_supported_sports_list(self) -> List[str]:
        """Get list of supported sport names."""
        return list(COLLECTORS.keys())


class HealthService:
    """Service for health and monitoring operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        try:
            total_events = self.db.get_event_count()
            db_connected = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            total_events = 0
            db_connected = False
        
        return {
            'status': 'healthy' if db_connected else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'database_connected': db_connected,
            'total_events': total_events,
            'supported_sports': list(COLLECTORS.keys())
        }
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        sports_service = SportsService(self.db)
        sports = sports_service.get_all_sports()
        
        return {
            'total_events': self.db.get_event_count(),
            'sports': sports,
            'timestamp': datetime.now().isoformat()
        }


# Factory function to get services with proper dependency injection
def get_events_service(db: Optional[DatabaseManager] = None) -> EventsService:
    """Get EventsService instance."""
    if db is None:
        db = DatabaseManager()
    return EventsService(db)


def get_collection_service(db: Optional[DatabaseManager] = None) -> CollectionService:
    """Get CollectionService instance."""
    if db is None:
        db = DatabaseManager()
    return CollectionService(db)


def get_betting_odds_service(db: Optional[DatabaseManager] = None) -> BettingOddsService:
    """Get BettingOddsService instance."""
    if db is None:
        db = DatabaseManager()
    return BettingOddsService(db)


def get_sports_service(db: Optional[DatabaseManager] = None) -> SportsService:
    """Get SportsService instance."""
    if db is None:
        db = DatabaseManager()
    return SportsService(db)


def get_health_service(db: Optional[DatabaseManager] = None) -> HealthService:
    """Get HealthService instance."""
    if db is None:
        db = DatabaseManager()
    return HealthService(db)
