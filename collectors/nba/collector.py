"""
NBA data collector using web scraping.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event


class NBACollector(BaseDataCollector):
    """Collects NBA schedule data using web scraping."""
    
    def __init__(self):
        super().__init__("nba")
        self.sources = [
            "https://www.nba.com/schedule",
            "https://www.espn.com/nba/schedule"
        ]
    
    def fetch_raw_data(self) -> Dict[str, str]:
        """
        Fetch NBA schedules from multiple sources.
        
        Returns:
            Dictionary with source URLs as keys and HTML content as values
        """
        results = {}
        
        for source in self.sources:
            try:
                response = self.make_request(source)
                results[source] = response.text
                self.logger.info(f"Successfully fetched data from {source}")
                break  # Use first successful source
            except Exception as e:
                self.logger.warning(f"Failed to fetch from {source}: {e}")
                continue
        
        if not results:
            self.logger.warning("No NBA sources were accessible")
            return {}
        
        return results
    
    def parse_events(self, raw_data: Dict[str, str]) -> List[Dict]:
        """
        Parse NBA data from HTML content into standardized format.
        
        Args:
            raw_data: Dictionary with HTML content from sources
        
        Returns:
            List of standardized event dictionaries
        """
        events = []
        
        for source_url, html_content in raw_data.items():
            try:
                if "nba.com" in source_url:
                    events.extend(self._parse_nba_official(html_content))
                elif "espn.com" in source_url:
                    events.extend(self._parse_espn_nba(html_content))
                    
            except Exception as e:
                self.logger.error(f"Error parsing NBA data from {source_url}: {e}")
                continue
        
        # Remove duplicates based on event name and date
        unique_events = []
        seen = set()
        for event in events:
            key = (event['event'], event['date'][:10])  # Use date without time
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        self.logger.info(f"Parsed {len(unique_events)} unique NBA events")
        return unique_events
    
    def _parse_nba_official(self, html_content: str) -> List[Dict]:
        """Parse NBA official website schedule."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for game containers - NBA.com uses various class names
        game_containers = soup.find_all(['div', 'article'], class_=re.compile(r'game|schedule|matchup', re.I))
        
        for container in game_containers:
            try:
                # Extract team names
                teams = []
                team_elements = container.find_all(['span', 'div', 'p'], class_=re.compile(r'team|name', re.I))
                for elem in team_elements:
                    team_text = elem.get_text(strip=True)
                    if team_text and len(team_text) > 1:
                        teams.append(team_text)
                
                # Extract date/time
                date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
                game_date = self._parse_nba_date(date_elem.get_text(strip=True) if date_elem else "")
                
                # Extract venue
                venue_elem = container.find(['span', 'div'], class_=re.compile(r'venue|arena|location', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                # Create event if we have enough information
                if len(teams) >= 2:
                    event = create_event(
                        sport="nba",
                        date=game_date,
                        event=f"{teams[0]} vs {teams[1]}",
                        participants=teams[:2],
                        location=venue
                    )
                    events.append(event)
                    
            except Exception as e:
                self.logger.debug(f"Error parsing NBA game container: {e}")
                continue
        
        return events
    
    def _parse_espn_nba(self, html_content: str) -> List[Dict]:
        """Parse ESPN NBA schedule."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # ESPN typically uses tables or specific game containers
        game_elements = soup.find_all(['tr', 'div'], class_=re.compile(r'game|event|matchup|row', re.I))
        
        for element in game_elements:
            try:
                # Look for team abbreviations or names
                team_elements = element.find_all(['abbr', 'span', 'a'], class_=re.compile(r'team|abbr', re.I))
                teams = [elem.get_text(strip=True) for elem in team_elements if elem.get_text(strip=True)]
                
                # Look for date/time information
                time_elem = element.find(['time', 'span'], class_=re.compile(r'time|date', re.I))
                game_date = self._parse_nba_date(time_elem.get_text(strip=True) if time_elem else "")
                
                # Look for venue information
                venue_elem = element.find(['span', 'div'], text=re.compile(r'@|vs|Arena|Center', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                if len(teams) >= 2:
                    event = create_event(
                        sport="nba",
                        date=game_date,
                        event=f"{teams[0]} vs {teams[1]}",
                        participants=teams[:2],
                        location=venue
                    )
                    events.append(event)
                    
            except Exception as e:
                self.logger.debug(f"Error parsing ESPN NBA game: {e}")
                continue
        
        return events
    
    def _parse_nba_date(self, date_str: str) -> str:
        """
        Parse NBA date string to ISO format.
        
        Args:
            date_str: Date string from NBA website
        
        Returns:
            ISO formatted date string
        """
        try:
            if not date_str:
                return (datetime.now() + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0).isoformat() + "Z"
            
            # Common NBA date patterns
            patterns = [
                "%m/%d/%Y %I:%M %p",  # "07/20/2025 8:00 PM"
                "%m/%d %I:%M %p",     # "07/20 8:00 PM"
                "%B %d, %Y %I:%M %p", # "July 20, 2025 8:00 PM"
                "%B %d %I:%M %p",     # "July 20 8:00 PM"
            ]
            
            current_year = datetime.now().year
            
            for pattern in patterns:
                try:
                    parsed_date = datetime.strptime(date_str, pattern)
                    # If year is missing, use current year
                    if parsed_date.year == 1900:
                        parsed_date = parsed_date.replace(year=current_year)
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    continue
            
            # If no pattern matches, return default NBA game time
            self.logger.warning(f"Could not parse NBA date: {date_str}")
            return (datetime.now() + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0).isoformat() + "Z"
            
        except Exception as e:
            self.logger.warning(f"Error parsing NBA date '{date_str}': {e}")
            return (datetime.now() + timedelta(days=1)).replace(hour=20, minute=0, second=0, microsecond=0).isoformat() + "Z"
