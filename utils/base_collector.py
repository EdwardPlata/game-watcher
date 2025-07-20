"""
Base data collector class that all sport-specific collectors inherit from.
"""

import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .logger import LoggerMixin
from .event_schema import validate_event


class BaseDataCollector(LoggerMixin, ABC):
    """Base class for all sports data collectors."""
    
    def __init__(self, sport_name: str, timeout: int = 10):
        self.sport_name = sport_name
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'Daily-Sports-Calendar-App/1.0 ({sport_name.upper()}-Collector)'
        })
    
    @abstractmethod
    def fetch_raw_data(self) -> Any:
        """
        Fetch raw data from the sports API.
        
        Returns:
            Raw data from the API
        
        Raises:
            requests.RequestException: If API request fails
        """
        pass
    
    @abstractmethod
    def parse_events(self, raw_data: Any) -> List[Dict]:
        """
        Parse raw data into standardized event format.
        
        Args:
            raw_data: Raw data from the API
        
        Returns:
            List of standardized event dictionaries
        """
        pass
    
    def fetch_events(self) -> List[Dict]:
        """
        Main method to fetch and parse events.
        
        Returns:
            List of validated event dictionaries
        """
        try:
            self.logger.info(f"Fetching {self.sport_name} events...")
            raw_data = self.fetch_raw_data()
            events = self.parse_events(raw_data)
            
            # Validate all events
            validated_events = []
            for event in events:
                if validate_event(event):
                    validated_events.append(event)
                else:
                    self.logger.warning(f"Invalid event data: {event}")
            
            self.logger.info(f"Successfully fetched {len(validated_events)} {self.sport_name} events")
            return validated_events
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch {self.sport_name} data: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {self.sport_name} data: {e}")
            return []
    
    def get_base_url(self) -> Optional[str]:
        """
        Get the base URL for the sport's API.
        Override in subclasses if needed.
        
        Returns:
            Base URL string or None
        """
        return None
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get additional headers for API requests.
        Override in subclasses if API requires specific headers.
        
        Returns:
            Dictionary of headers
        """
        return {}
    
    def make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Make an HTTP request with proper error handling.
        
        Args:
            url: Request URL
            params: Optional query parameters
        
        Returns:
            Response object
        
        Raises:
            requests.RequestException: If request fails
        """
        headers = self.get_headers()
        if headers:
            self.session.headers.update(headers)
        
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response
