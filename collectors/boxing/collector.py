"""
Boxing data collector using BoxingScene web scraping.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event


class BoxingCollector(BaseDataCollector):
    """Collects boxing schedule data from BoxingScene."""
    
    def __init__(self):
        super().__init__("boxing")
        self.sources = [
            "https://www.boxingscene.com/schedule"
        ]
    
    def fetch_raw_data(self) -> Dict[str, str]:
        """
        Fetch boxing schedules from BoxingScene.
        
        Returns:
            Dictionary with source URLs as keys and HTML content as values
        """
        results = {}
        
        for source in self.sources:
            try:
                response = self.make_request(source)
                if response.status_code == 200:
                    results[source] = response.text
                    self.logger.info(f"Successfully fetched data from {source}")
                else:
                    self.logger.warning(f"HTTP {response.status_code} from {source}")
            except Exception as e:
                self.logger.warning(f"Failed to fetch from {source}: {e}")
                continue
        
        if not results:
            self.logger.warning("No boxing sources were accessible")
            return {}
        
        return results
    
    def parse_events(self, raw_data: Dict[str, str]) -> List[Dict]:
        """
        Parse boxing data from BoxingScene HTML content into standardized format.
        
        Args:
            raw_data: Dictionary with HTML content from BoxingScene
        
        Returns:
            List of standardized event dictionaries
        """
        events = []
        
        for source_url, html_content in raw_data.items():
            try:
                if "boxingscene.com" in source_url:
                    events.extend(self._parse_boxingscene(html_content))
                    
            except Exception as e:
                self.logger.error(f"Error parsing boxing data from {source_url}: {e}")
                continue
        
        # Remove duplicates
        unique_events = []
        seen = set()
        for event in events:
            key = (event['event'], event['date'][:10])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        self.logger.info(f"Parsed {len(unique_events)} unique boxing events")
        return unique_events
    
    def _parse_boxingscene(self, html_content: str) -> List[Dict]:
        """Parse BoxingScene schedule page."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # BoxingScene uses various containers for events
        # Look for schedule items, event containers, or fight cards
        event_containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'event|fight|card|schedule|match', re.I))
        
        if not event_containers:
            # Fallback to broader search
            event_containers = soup.find_all(['div'], class_=re.compile(r'item|post|card', re.I))
        
        for container in event_containers:
            try:
                # Extract fight/event information
                title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|headline', re.I))
                if not title_elem:
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4', 'a'])
                
                if not title_elem:
                    continue
                
                event_title = title_elem.get_text(strip=True)
                
                # Skip if title is too short or generic
                if not event_title or len(event_title) < 5:
                    continue
                
                # Extract participants (fighters)
                participants = []
                
                # Look for "vs", "v", "versus" patterns in the title
                vs_match = re.search(r'(.+?)\s+(?:vs\.?|v\.?|versus)\s+(.+)', event_title, re.I)
                if vs_match:
                    fighter1 = vs_match.group(1).strip()
                    fighter2 = vs_match.group(2).strip()
                    participants = [fighter1, fighter2]
                    # Clean the event title
                    event_title = f"{fighter1} vs {fighter2}"
                else:
                    # Look for fighter names in separate elements
                    fighter_elements = container.find_all(['span', 'div'], class_=re.compile(r'fighter|name|participant', re.I))
                    for elem in fighter_elements:
                        fighter_name = elem.get_text(strip=True)
                        if fighter_name and len(fighter_name) > 2 and len(fighter_name) < 50:
                            participants.append(fighter_name)
                    
                    # Limit to 2 main fighters
                    participants = participants[:2]
                
                # Extract date/time
                date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when', re.I))
                if not date_elem:
                    # Look for date patterns in text
                    date_elem = container.find(string=re.compile(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{4}|\d{4}-\d{2}-\d{2}'))
                
                event_date = self._parse_boxing_date(date_elem.get_text(strip=True) if date_elem else "")
                
                # Extract venue/location
                venue_elem = container.find(['span', 'div'], class_=re.compile(r'venue|location|place|arena', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                # Clean venue
                if venue and len(venue) > 100:
                    venue = venue[:100] + "..."
                
                # Extract weight class or division
                weight_elem = container.find(['span', 'div'], class_=re.compile(r'weight|division|class', re.I))
                weight_class = weight_elem.get_text(strip=True) if weight_elem else None
                
                # Determine leagues/categories
                leagues = ["Professional Boxing"]
                
                if weight_class:
                    leagues.append(weight_class)
                
                # Look for championship indicators
                if any(word in event_title.lower() for word in ['title', 'championship', 'belt', 'wbc', 'wba', 'wbo', 'ibf']):
                    leagues.append("Title Fight")
                
                # Look for amateur/professional indicators
                if 'amateur' in event_title.lower():
                    leagues = ["Amateur Boxing"]
                elif any(word in event_title.lower() for word in ['pro', 'professional']):
                    leagues.insert(0, "Professional Boxing")
                
                # Enhance event name with weight class if available
                if weight_class and weight_class not in event_title:
                    event_title += f" ({weight_class})"
                
                event = create_event(
                    sport="boxing",
                    date=event_date,
                    event=event_title,
                    participants=participants,
                    location=venue,
                    leagues=leagues
                )
                events.append(event)
                
            except Exception as e:
                self.logger.debug(f"Error parsing boxing event container: {e}")
                continue
        
        return events
    
    def _parse_boxing_date(self, date_string: str) -> str:
        """
        Parse various boxing date formats into ISO format.
        
        Args:
            date_string: Date string from BoxingScene
        
        Returns:
            ISO formatted date string
        """
        if not date_string:
            return (datetime.now() + timedelta(days=7)).isoformat() + "Z"
        
        try:
            # Common patterns for boxing dates
            patterns = [
                "%B %d, %Y",          # December 25, 2024
                "%b %d, %Y",          # Dec 25, 2024
                "%m/%d/%Y",           # 12/25/2024
                "%d/%m/%Y",           # 25/12/2024
                "%Y-%m-%d",           # 2024-12-25
                "%d.%m.%Y",           # 25.12.2024
                "%B %d",              # December 25 (current year)
                "%b %d",              # Dec 25 (current year)
                "%m/%d",              # 12/25 (current year)
            ]
            
            # Clean the date string
            clean_date = re.sub(r'[^\w\s,./:-]', '', date_string).strip()
            
            for pattern in patterns:
                try:
                    if "%Y" not in pattern:
                        # Add current year if not specified
                        current_year = datetime.now().year
                        clean_date_with_year = f"{clean_date}, {current_year}"
                        pattern_with_year = f"{pattern}, %Y"
                        parsed_date = datetime.strptime(clean_date_with_year, pattern_with_year)
                    else:
                        parsed_date = datetime.strptime(clean_date, pattern)
                    
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    continue
            
            # Try to extract date with regex
            date_match = re.search(r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})', clean_date)
            if date_match:
                month, day, year = date_match.groups()
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.isoformat() + "Z"
            
        except Exception as e:
            self.logger.debug(f"Error parsing boxing date '{date_string}': {e}")
        
        # Default to next week if parsing fails
        return (datetime.now() + timedelta(days=7)).isoformat() + "Z"