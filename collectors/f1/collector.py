"""
F1 data collector using web scraping.
"""

from datetime import datetime
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event


class F1Collector(BaseDataCollector):
    """Collects F1 race schedule data using web scraping."""
    
    def __init__(self):
        super().__init__("f1")
        self.sources = [
            "https://en.wikipedia.org/wiki/2025_Formula_One_World_Championship",
            "https://www.formula1.com/en/racing/2025.html"
        ]
    
    def fetch_raw_data(self) -> Dict[str, str]:
        """
        Fetch F1 race schedule from multiple sources.
        
        Returns:
            Dictionary with source URLs as keys and HTML content as values
        
        Raises:
            requests.RequestException: If API request fails
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
            self.logger.warning("No F1 sources were accessible")
            return {}
        
        return results
    
    def parse_events(self, raw_data: Dict[str, str]) -> List[Dict]:
        """
        Parse F1 data from HTML content into standardized format.
        
        Args:
            raw_data: Dictionary with HTML content from sources
        
        Returns:
            List of standardized event dictionaries
        """
        events = []
        
        for source_url, html_content in raw_data.items():
            try:
                if "wikipedia.org" in source_url:
                    events.extend(self._parse_wikipedia_f1(html_content))
                elif "formula1.com" in source_url:
                    events.extend(self._parse_f1_official(html_content))
                    
            except Exception as e:
                self.logger.error(f"Error parsing F1 data from {source_url}: {e}")
                continue
        
        # Remove duplicates based on event name and date
        unique_events = []
        seen = set()
        for event in events:
            key = (event['event'], event['date'][:10])  # Use date without time
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        self.logger.info(f"Parsed {len(unique_events)} unique F1 events")
        return unique_events
    
    def _parse_wikipedia_f1(self, html_content: str) -> List[Dict]:
        """Parse F1 schedule from Wikipedia."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the race calendar table
        tables = soup.find_all('table', class_=re.compile(r'wikitable|sortable', re.I))
        
        for table in tables:
            # Look for table headers to identify the race schedule table
            headers = table.find_all('th')
            header_text = ' '.join([th.get_text() for th in headers]).lower()
            
            if any(keyword in header_text for keyword in ['grand prix', 'race', 'circuit', 'date']):
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    try:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 3:
                            continue
                        
                        # Extract race information
                        race_name = ""
                        race_date = ""
                        circuit = ""
                        location = ""
                        
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            
                            # Try to identify what each cell contains
                            if "grand prix" in cell_text.lower() or "gp" in cell_text.lower():
                                race_name = cell_text
                            elif self._is_date(cell_text):
                                race_date = cell_text
                            elif any(keyword in cell_text.lower() for keyword in ['circuit', 'track', 'speedway']):
                                circuit = cell_text
                            elif any(keyword in cell_text.lower() for keyword in ['country', 'city']) or len(cell_text.split()) <= 3:
                                location = cell_text
                        
                        # If we couldn't identify by content, use position
                        if not race_name and len(cells) > 1:
                            race_name = cells[1].get_text(strip=True)
                        if not race_date and len(cells) > 0:
                            race_date = cells[0].get_text(strip=True)
                        if not circuit and len(cells) > 2:
                            circuit = cells[2].get_text(strip=True)
                        if not location and len(cells) > 3:
                            location = cells[3].get_text(strip=True)
                        
                        # Clean and validate data
                        if race_name and race_date:
                            parsed_date = self._parse_f1_date(race_date)
                            if parsed_date:
                                event_name = f"F1 {race_name}"
                                event_location = f"{circuit}, {location}" if circuit and location else circuit or location or "TBD"
                                
                                # Determine leagues/categories
                                leagues = ["Formula 1"]
                                if "sprint" in race_name.lower():
                                    leagues.append("Sprint")
                                if "grand prix" in race_name.lower():
                                    leagues.append("Grand Prix")
                                
                                # Create watch link for F1 races
                                watch_link = "https://www.formula1.com/en/racing/2025.html"
                                
                                event = create_event(
                                    sport="f1",
                                    date=parsed_date,
                                    event=event_name,
                                    participants=["F1 Drivers"],
                                    location=event_location,
                                    leagues=leagues,
                                    watch_link=watch_link
                                )
                                events.append(event)
                                
                    except Exception as e:
                        self.logger.debug(f"Error parsing F1 Wikipedia row: {e}")
                        continue
        
        return events
    
    def _parse_f1_official(self, html_content: str) -> List[Dict]:
        """Parse F1 official website schedule."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for race event containers
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|race|gp|grand-prix', re.I))
        
        for container in event_containers:
            try:
                # Extract race name
                name_elem = container.find(['h1', 'h2', 'h3'], class_=re.compile(r'title|name|race', re.I))
                race_name = name_elem.get_text(strip=True) if name_elem else ""
                
                # Extract date
                date_elem = container.find(['time', 'span', 'div'], class_=re.compile(r'date|time', re.I))
                race_date = date_elem.get_text(strip=True) if date_elem else ""
                
                # Extract location
                location_elem = container.find(['span', 'div'], class_=re.compile(r'location|circuit|venue', re.I))
                location = location_elem.get_text(strip=True) if location_elem else "TBD"
                
                # Create event
                if race_name and race_date:
                    parsed_date = self._parse_f1_date(race_date)
                    if parsed_date:
                        event_name = f"F1 {race_name}" if not race_name.startswith("F1") else race_name
                        
                        # Extract watch link from official F1 site
                        watch_link = None
                        links = container.find_all('a', href=True)
                        for link in links:
                            href = link.get('href', '')
                            if 'watch' in href.lower() or 'race' in href.lower():
                                watch_link = href if href.startswith('http') else f"https://www.formula1.com{href}"
                                break
                        
                        if not watch_link:
                            watch_link = "https://www.formula1.com/en/racing/2025.html"
                        
                        event = create_event(
                            sport="f1",
                            date=parsed_date,
                            event=event_name,
                            participants=["F1 Drivers"],
                            location=location,
                            watch_link=watch_link
                        )
                        events.append(event)
                        
            except Exception as e:
                self.logger.debug(f"Error parsing F1 official event: {e}")
                continue
        
        return events
    
    def _is_date(self, text: str) -> bool:
        """Check if text contains a date."""
        date_patterns = [
            r'\d{1,2}[-/.]\d{1,2}[-/.]\d{4}',  # DD/MM/YYYY or MM/DD/YYYY
            r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}',  # YYYY/MM/DD
            r'\b\w+ \d{1,2}, \d{4}\b',         # Month DD, YYYY
            r'\d{1,2} \w+ \d{4}',              # DD Month YYYY
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _parse_f1_date(self, date_string: str) -> str:
        """
        Parse various F1 date formats into ISO format.
        
        Args:
            date_string: Date string from website
        
        Returns:
            ISO formatted date string or None if parsing fails
        """
        if not date_string:
            return None
        
        try:
            # Common patterns for F1 dates
            patterns = [
                "%d %B %Y",       # 15 January 2025
                "%d %b %Y",       # 15 Jan 2025
                "%B %d, %Y",      # January 15, 2025
                "%b %d, %Y",      # Jan 15, 2025
                "%d/%m/%Y",       # 15/01/2025
                "%m/%d/%Y",       # 01/15/2025
                "%Y-%m-%d",       # 2025-01-15
                "%d.%m.%Y",       # 15.01.2025
                "%d-%m-%Y",       # 15-01-2025
            ]
            
            # Clean the date string
            clean_date = re.sub(r'[^\w\s,./:-]', '', date_string).strip()
            
            # Extract just the date part if there are multiple dates
            if "–" in clean_date or "-" in clean_date:
                # Take the first date in a range
                clean_date = clean_date.split("–")[0].split("-")[0].strip()
            
            for pattern in patterns:
                try:
                    parsed_date = datetime.strptime(clean_date, pattern)
                    # Set default time to 14:00 (2 PM) for F1 races
                    parsed_date = parsed_date.replace(hour=14, minute=0, second=0)
                    return parsed_date.isoformat() + "Z"
                except ValueError:
                    continue
            
            # Try to extract date components with regex
            date_match = re.search(r'(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})', clean_date)
            if date_match:
                day, month, year = date_match.groups()
                parsed_date = datetime(int(year), int(month), int(day), 14, 0, 0)
                return parsed_date.isoformat() + "Z"
            
        except Exception as e:
            self.logger.debug(f"Error parsing F1 date '{date_string}': {e}")
        
        return None