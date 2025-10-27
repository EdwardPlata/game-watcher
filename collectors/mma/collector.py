"""
MMA/UFC data collector using web scraping.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event


class MMACollector(BaseDataCollector):
    """Collects MMA/UFC schedule data using web scraping."""
    
    def __init__(self):
        super().__init__("mma")
        self.sources = [
            "https://www.ufc.com/events",
            "https://www.mmafighting.com/schedule",
            "https://www.tapology.com/fightcenter"
        ]
    
    def fetch_raw_data(self) -> Dict[str, str]:
        """
        Fetch MMA/UFC schedules from multiple sources.
        
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
            self.logger.warning("No MMA sources were accessible")
            return {}
        
        return results
    
    def parse_events(self, raw_data: Dict[str, str]) -> List[Dict]:
        """
        Parse MMA data from HTML content into standardized format.
        
        Args:
            raw_data: Dictionary with HTML content from sources
        
        Returns:
            List of standardized event dictionaries
        """
        events = []
        
        for source_url, html_content in raw_data.items():
            try:
                if "ufc.com" in source_url:
                    events.extend(self._parse_ufc_official(html_content))
                elif "mmafighting.com" in source_url:
                    events.extend(self._parse_mma_fighting(html_content))
                elif "tapology.com" in source_url:
                    events.extend(self._parse_tapology_mma(html_content))
                    
            except Exception as e:
                self.logger.error(f"Error parsing MMA data from {source_url}: {e}")
                continue
        
        # Remove duplicates based on event name and date
        unique_events = []
        seen = set()
        for event in events:
            key = (event['event'], event['date'][:10])  # Use date without time
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        self.logger.info(f"Parsed {len(unique_events)} unique MMA events")
        return unique_events
    
    def _parse_ufc_official(self, html_content: str) -> List[Dict]:
        """Parse UFC official website events."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for event containers on UFC.com
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|card|fight', re.I))
        
        for container in event_containers:
            try:
                # Extract event title
                title_elem = container.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|name|event', re.I))
                event_title = title_elem.get_text(strip=True) if title_elem else None
                
                # Extract main event fighters
                fighters = []
                fighter_elements = container.find_all(['span', 'div'], class_=re.compile(r'fighter|name|opponent', re.I))
                for elem in fighter_elements:
                    fighter_text = elem.get_text(strip=True)
                    if fighter_text and len(fighter_text) > 1:
                        fighters.append(fighter_text)
                
                # Extract date/time
                date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
                event_date = self._parse_mma_date(date_elem.get_text(strip=True) if date_elem else "")
                
                # Extract venue
                venue_elem = container.find(['span', 'div'], class_=re.compile(r'venue|location|arena', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                # Create event
                if event_title:
                    # For UFC events, use the card name and main event fighters
                    main_event = f"{fighters[0]} vs {fighters[1]}" if len(fighters) >= 2 else "Main Event TBD"
                    participants = fighters[:2] if len(fighters) >= 2 else ["TBD", "TBD"]
                    
                    # Determine league/organization
                    leagues = ["UFC"]
                    if "bellator" in event_title.lower():
                        leagues = ["Bellator"]
                    elif "one" in event_title.lower() and "championship" in event_title.lower():
                        leagues = ["ONE Championship"]
                    elif "pfl" in event_title.lower():
                        leagues = ["PFL"]
                    
                    # Try to extract watch link
                    watch_link = None
                    links = container.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        if 'watch' in href.lower() or 'stream' in href.lower() or 'ppv' in href.lower():
                            if href.startswith('http'):
                                watch_link = href
                            elif href.startswith('/'):
                                watch_link = f"https://www.ufc.com{href}"
                            break
                    
                    # Default UFC watch link
                    if not watch_link:
                        watch_link = "https://www.ufc.com/events"
                    
                    event = create_event(
                        sport="mma",
                        date=event_date,
                        event=f"{event_title}: {main_event}",
                        participants=participants,
                        location=venue,
                        leagues=leagues,
                        watch_link=watch_link
                    )
                    events.append(event)
                    
            except Exception as e:
                self.logger.debug(f"Error parsing UFC event container: {e}")
                continue
        
        return events
    
    def _parse_mma_fighting(self, html_content: str) -> List[Dict]:
        """Parse MMA Fighting schedule."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # MMA Fighting uses article or event containers
        event_elements = soup.find_all(['article', 'div'], class_=re.compile(r'event|fight|card|schedule', re.I))
        
        for element in event_elements:
            try:
                # Extract event title
                title_elem = element.find(['h1', 'h2', 'h3', 'a'])
                event_title = title_elem.get_text(strip=True) if title_elem else None
                
                # Extract fighters from title or separate elements
                fighters = []
                if event_title and "vs" in event_title.lower():
                    # Extract fighters from title
                    vs_split = event_title.split(" vs ")
                    if len(vs_split) >= 2:
                        fighters = [vs_split[0].strip(), vs_split[1].strip()]
                else:
                    # Look for separate fighter elements
                    fighter_elements = element.find_all(['span', 'div'], class_=re.compile(r'fighter|name', re.I))
                    for fighter_elem in fighter_elements:
                        fighter_name = fighter_elem.get_text(strip=True)
                        if fighter_name and len(fighter_name) > 2:
                            fighters.append(fighter_name)
                
                # Extract date
                date_elem = element.find(['time', 'span'], class_=re.compile(r'date|time', re.I))
                event_date = self._parse_mma_date(date_elem.get_text(strip=True) if date_elem else "")
                
                # Extract venue
                venue_elem = element.find(['span', 'div'], class_=re.compile(r'venue|location', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                # Extract watch link
                watch_link = None
                links = element.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'watch' in href.lower() or 'stream' in href.lower():
                        watch_link = href if href.startswith('http') else f"https://www.mmafighting.com{href}"
                        break
                if not watch_link:
                    watch_link = "https://www.mmafighting.com/schedule"
                
                # Create event
                if event_title or len(fighters) >= 2:
                    if not event_title:
                        event_title = f"{fighters[0]} vs {fighters[1]}" if len(fighters) >= 2 else "MMA Event"
                    
                    participants = fighters[:2] if len(fighters) >= 2 else ["TBD", "TBD"]
                    
                    event = create_event(
                        sport="mma",
                        date=event_date,
                        event=event_title,
                        participants=participants,
                        location=venue,
                        watch_link=watch_link
                    )
                    events.append(event)
                    
            except Exception as e:
                self.logger.debug(f"Error parsing MMA Fighting event: {e}")
                continue
        
        return events
    
    def _parse_tapology_mma(self, html_content: str) -> List[Dict]:
        """Parse Tapology MMA schedule."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tapology uses table rows or event containers
        event_elements = soup.find_all(['tr', 'div'], class_=re.compile(r'event|fight|bout|listing', re.I))
        
        for element in event_elements:
            try:
                # Extract event/organization name
                org_elem = element.find(['span', 'a'], class_=re.compile(r'org|promotion|event', re.I))
                organization = org_elem.get_text(strip=True) if org_elem else "MMA"
                
                # Extract fighter names
                fighters = []
                name_elements = element.find_all(['a', 'span'], class_=re.compile(r'fighter|name', re.I))
                for name_elem in name_elements:
                    name = name_elem.get_text(strip=True)
                    if name and len(name) > 2 and name not in fighters:
                        fighters.append(name)
                
                # Extract date
                date_elem = element.find(['span', 'div'], class_=re.compile(r'date|time', re.I))
                event_date = self._parse_mma_date(date_elem.get_text(strip=True) if date_elem else "")
                
                # Extract venue
                venue_elem = element.find(['span', 'div'], class_=re.compile(r'venue|location', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "TBD"
                
                # Extract watch link
                watch_link = None
                links = element.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'event' in href.lower() or 'fightcenter' in href.lower():
                        watch_link = href if href.startswith('http') else f"https://www.tapology.com{href}"
                        break
                if not watch_link:
                    watch_link = "https://www.tapology.com/fightcenter"
                
                # Create event
                if len(fighters) >= 2:
                    event_title = f"{organization}: {fighters[0]} vs {fighters[1]}"
                    
                    event = create_event(
                        sport="mma",
                        date=event_date,
                        event=event_title,
                        participants=fighters[:2],
                        location=venue,
                        watch_link=watch_link
                    )
                    events.append(event)
                    
            except Exception as e:
                self.logger.debug(f"Error parsing Tapology MMA event: {e}")
                continue
        
        return events
    
    def _parse_mma_date(self, date_string: str) -> str:
        """
        Parse various MMA date formats into ISO format.
        
        Args:
            date_string: Date string from website
        
        Returns:
            ISO formatted date string
        """
        if not date_string:
            return (datetime.now() + timedelta(days=7)).isoformat() + "Z"
        
        try:
            # Common patterns for MMA dates
            patterns = [
                "%B %d, %Y",      # January 15, 2025
                "%b %d, %Y",      # Jan 15, 2025
                "%m/%d/%Y",       # 01/15/2025
                "%d/%m/%Y",       # 15/01/2025
                "%Y-%m-%d",       # 2025-01-15
                "%d.%m.%Y",       # 15.01.2025
                "%B %d",          # January 15 (current year)
                "%b %d",          # Jan 15 (current year)
            ]
            
            # Clean the date string
            clean_date = re.sub(r'[^\w\s,./:-]', '', date_string).strip()
            
            for pattern in patterns:
                try:
                    if "%Y" not in pattern:
                        # Add current year if not specified
                        clean_date_with_year = f"{clean_date}, {datetime.now().year}"
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
                day, month, year = date_match.groups()
                parsed_date = datetime(int(year), int(month), int(day))
                return parsed_date.isoformat() + "Z"
            
        except Exception as e:
            self.logger.debug(f"Error parsing MMA date '{date_string}': {e}")
        
        # Default to next week if parsing fails
        return (datetime.now() + timedelta(days=7)).isoformat() + "Z"
