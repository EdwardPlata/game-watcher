"""
Python API Client for Game Watcher

This module provides a convenient Python client for interacting with the Game Watcher API.
It can be used by external applications, frontend frameworks, or automation scripts.

Usage:
    from api.client import GameWatcherClient
    
    client = GameWatcherClient(base_url="http://localhost:8000")
    
    # Get events
    events = client.get_events(sport="futbol")
    
    # Trigger collection
    result = client.collect_sport_data("futbol")
    
    # Get betting odds
    odds = client.get_betting_odds()
"""

from typing import List, Dict, Any, Optional
import requests
from datetime import date


class GameWatcherClient:
    """
    Python client for Game Watcher API.
    
    This client provides a clean interface to all API endpoints and handles
    request formatting, error handling, and response parsing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API server (default: http://localhost:8000)
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
        self.timeout = timeout
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON request body
        
        Returns:
            Response data as dictionary
        
        Raises:
            APIError: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', error_detail)
            except:
                pass
            raise APIError(f"API request failed: {error_detail}") from e
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}") from e
    
    # Health & Status
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.
        
        Returns:
            Health status information
        """
        return self._make_request('GET', '/health')
    
    # Sports
    
    def get_sports(self) -> List[Dict[str, Any]]:
        """
        Get list of supported sports with statistics.
        
        Returns:
            List of sports with their statistics
        """
        response = self._make_request('GET', '/sports')
        return response['sports']
    
    # Events
    
    def get_events(
        self,
        sport: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get events with optional filtering.
        
        Args:
            sport: Filter by sport (futbol, nfl, nba, f1, boxing, mma)
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            limit: Maximum number of events (1-1000)
        
        Returns:
            List of events
        """
        params = {'limit': limit}
        if sport:
            params['sport'] = sport
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = self._make_request('GET', '/events', params=params)
        return response['events']
    
    def get_event(self, event_id: int) -> Dict[str, Any]:
        """
        Get a specific event by ID.
        
        Args:
            event_id: Event ID
        
        Returns:
            Event data
        """
        return self._make_request('GET', f'/events/{event_id}')
    
    # Data Collection
    
    def collect_sport_data(self, sport: str) -> Dict[str, Any]:
        """
        Trigger data collection for a specific sport.
        
        Args:
            sport: Sport to collect (futbol, nfl, nba, f1, boxing, mma)
        
        Returns:
            Collection result
        """
        return self._make_request('POST', f'/collect/{sport}')
    
    def collect_all_data(self) -> Dict[str, Any]:
        """
        Trigger data collection for all sports.
        
        Returns:
            Collection results for all sports
        """
        return self._make_request('POST', '/collect/all')
    
    # Betting Odds
    
    def get_betting_odds(self) -> List[Dict[str, Any]]:
        """
        Get all betting odds data.
        
        Returns:
            List of betting odds
        """
        response = self._make_request('GET', '/betting/odds')
        return response.get('odds', [])
    
    def get_event_odds(self, event_id: str) -> Dict[str, Any]:
        """
        Get betting odds for a specific event.
        
        Args:
            event_id: Event ID
        
        Returns:
            Betting odds data for the event
        """
        return self._make_request('GET', f'/betting/odds/{event_id}')
    
    # Calendar
    
    def get_calendar_month(
        self,
        year: int,
        month: int,
        sport: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get calendar view for a specific month.
        
        Args:
            year: Year (YYYY)
            month: Month (1-12)
            sport: Optional sport filter
        
        Returns:
            Calendar data with events
        """
        params = {}
        if sport:
            params['sport'] = sport
        
        return self._make_request('GET', f'/calendar/{year}/{month}', params=params)
    
    # Webhooks
    
    def register_webhook(
        self,
        url: str,
        sports: List[str],
        event_types: List[str]
    ) -> Dict[str, Any]:
        """
        Register a webhook for notifications.
        
        Args:
            url: Webhook URL
            sports: List of sports to monitor
            event_types: List of event types to monitor
        
        Returns:
            Webhook registration details
        """
        payload = {
            'url': url,
            'sports': sports,
            'event_types': event_types
        }
        return self._make_request('POST', '/webhooks/register', json=payload)
    
    def test_webhook(self, url: str) -> Dict[str, Any]:
        """
        Test a webhook URL.
        
        Args:
            url: Webhook URL to test
        
        Returns:
            Test result
        """
        payload = {'url': url}
        return self._make_request('POST', '/webhooks/test', json=payload)


class APIError(Exception):
    """Exception raised for API errors."""
    pass


# Convenience functions for common operations

def get_upcoming_events(
    client: Optional[GameWatcherClient] = None,
    sport: Optional[str] = None,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Get upcoming events for the next N days.
    
    Args:
        client: GameWatcherClient instance (creates new if None)
        sport: Optional sport filter
        days: Number of days to look ahead
    
    Returns:
        List of upcoming events
    """
    if client is None:
        client = GameWatcherClient()
    
    from datetime import datetime, timedelta
    
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=days)
    
    return client.get_events(
        sport=sport,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        limit=1000
    )


def collect_and_wait(
    client: Optional[GameWatcherClient] = None,
    sport: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger data collection and return results.
    
    Args:
        client: GameWatcherClient instance (creates new if None)
        sport: Sport to collect (None for all sports)
    
    Returns:
        Collection results
    """
    if client is None:
        client = GameWatcherClient()
    
    if sport:
        return client.collect_sport_data(sport)
    else:
        return client.collect_all_data()


# Example usage
if __name__ == '__main__':
    # Create client
    client = GameWatcherClient()
    
    # Check health
    print("Health Check:")
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"Total Events: {health['total_events']}")
    print()
    
    # Get sports
    print("Supported Sports:")
    sports = client.get_sports()
    for sport in sports:
        print(f"- {sport['display_name']}: {sport['total_events']} events")
    print()
    
    # Get upcoming futbol events
    print("Upcoming Futbol Events:")
    events = get_upcoming_events(client, sport="futbol", days=7)
    for event in events[:5]:  # Show first 5
        print(f"- {event['event']} on {event['date']}")
    print()
    
    # Get betting odds
    print("Betting Odds:")
    try:
        odds = client.get_betting_odds()
        print(f"Found {len(odds)} events with odds")
        if odds:
            sample = odds[0]
            print(f"Example: {sample['home_team']} vs {sample['away_team']}")
            print(f"Best odds: Home {sample['best_home_odds']}, Away {sample['best_away_odds']}")
    except APIError as e:
        print(f"Error: {e}")
