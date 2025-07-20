"""
Futbol (Soccer) data collector using ESPN web scraping.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import re
from bs4 import BeautifulSoup
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event


class FutbolCollector(BaseDataCollector):
    """Collects soccer/football schedule data from ESPN."""
    
    def __init__(self):
        super().__init__("futbol")
        # ESPN soccer schedule URLs for multiple dates
        today = datetime.now()
        self.sources = []
        
        # Generate URLs for next 30 days to get comprehensive schedule
        for i in range(30):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y%m%d")
            url = f"https://www.espn.com/soccer/schedule/_/date/{date_str}"
            self.sources.append(url)
    
    def fetch_raw_data(self) -> Dict[str, str]:
        """
        Fetch soccer schedules from ESPN for multiple dates.
        
        Returns:
            Dictionary with source URLs as keys and HTML content as values
        """
        results = {}
        successful_fetches = 0
        
        for source in self.sources:
            try:
                response = self.make_request(source)
                if response.status_code == 200:
                    results[source] = response.text
                    successful_fetches += 1
                    self.logger.debug(f"Successfully fetched data from {source}")
                    
                    # Limit to avoid overwhelming the server
                    if successful_fetches >= 7:  # Get about a week's worth of data
                        break
                        
            except Exception as e:
                self.logger.debug(f"Failed to fetch from {source}: {e}")
                continue
        
        if not results:
            self.logger.warning("No ESPN soccer sources were accessible")
            return {}
        
        self.logger.info(f"Successfully fetched data from {successful_fetches} ESPN soccer pages")
        return results
    
    def parse_events(self, raw_data: Dict[str, str]) -> List[Dict]:
        """
        Parse soccer data from ESPN HTML content into standardized format.
        
        Args:
            raw_data: Dictionary with HTML content from ESPN sources
        
        Returns:
            List of standardized event dictionaries
        """
        events = []
        
        for source_url, html_content in raw_data.items():
            try:
                # Extract date from URL
                date_match = re.search(r'/date/(\d{8})', source_url)
                if date_match:
                    url_date = datetime.strptime(date_match.group(1), "%Y%m%d")
                else:
                    url_date = datetime.now()
                
                page_events = self._parse_espn_soccer(html_content, url_date)
                events.extend(page_events)
                    
            except Exception as e:
                self.logger.error(f"Error parsing soccer data from {source_url}: {e}")
                continue
        
        # Remove duplicates based on unique combination of teams, date, and league
        unique_events = []
        seen = set()
        for event in events:
            # Create unique key from teams, date, and league
            teams_key = "-".join(sorted(event['participants'])) if event['participants'] else event['event']
            key = (teams_key, event['date'][:16], event.get('leagues', [''])[0])  # Use hour precision
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        self.logger.info(f"Parsed {len(unique_events)} unique soccer events")
        return unique_events
    
    def _parse_espn_soccer(self, html_content: str, page_date: datetime) -> List[Dict]:
        """Parse ESPN soccer schedule page."""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # First, find all competition/league names on the page
        competition_keywords = ['championship', 'league', 'cup', 'euro', 'uefa', 'fifa', 'premier', 'liga', 'champions', 'women', 'friendly', 'international']
        found_competitions = []
        
        all_elements = soup.find_all(['div', 'h1', 'h2', 'h3', 'span'])
        for element in all_elements:
            text = element.get_text(strip=True)
            if (text and 
                len(text) > 5 and 
                len(text) < 80 and
                any(keyword in text.lower() for keyword in competition_keywords)):
                found_competitions.append(text)
        
        # Remove duplicates and create a mapping
        unique_competitions = list(set(found_competitions))
        self.logger.debug(f"Found competitions: {unique_competitions}")
        
        # ESPN soccer uses Table__TR--sm class for match rows
        match_rows = soup.find_all('tr', class_=re.compile(r'Table__TR--sm'))
        
        # Look for league/competition headers
        current_league = "International Football"
        
        for row in match_rows:
            try:
                # Skip header rows
                if 'MATCH' in row.get_text() and 'TIME' in row.get_text():
                    continue
                
                # Extract teams from ESPN team links
                team_links = row.find_all('a', href=re.compile(r'/soccer/team/'))
                teams = []
                
                for link in team_links:
                    team_text = link.get_text(strip=True)
                    if team_text and team_text not in teams:  # Avoid duplicates
                        teams.append(team_text)
                
                # Need exactly 2 teams for a match
                if len(teams) != 2:
                    continue
                
                # Extract time from row text
                row_text = row.get_text(strip=True)
                match_time = None
                
                # ESPN time patterns: "2:00 PM", "10:00 AM", etc.
                time_patterns = [
                    r'(\d{1,2}:\d{2}\s*(?:AM|PM))',
                    r'(\d{1,2}:\d{2})'
                ]
                
                for pattern in time_patterns:
                    time_match = re.search(pattern, row_text)
                    if time_match:
                        match_time = time_match.group(1).strip()
                        break
                
                # Create event date/time
                if match_time:
                    try:
                        # Parse time and combine with page date
                        time_str = match_time.upper()
                        if 'AM' in time_str or 'PM' in time_str:
                            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
                        else:
                            # Assume 24-hour format
                            time_obj = datetime.strptime(time_str, "%H:%M").time()
                        
                        event_datetime = datetime.combine(page_date.date(), time_obj)
                        event_date = event_datetime.isoformat() + "Z"
                    except ValueError:
                        # Fallback to page date if time parsing fails
                        event_date = page_date.replace(hour=12, minute=0, second=0).isoformat() + "Z"
                else:
                    # Default to noon on the page date
                    event_date = page_date.replace(hour=12, minute=0, second=0).isoformat() + "Z"
                
                # Extract venue/location from row text
                venue = "TBD"
                # Look for stadium/arena/location patterns
                venue_patterns = [
                    r'([A-Z][^,]+ Stadium[^,]*)',
                    r'([A-Z][^,]+ Arena[^,]*)',
                    r'(Estadio [^,]+)',
                    r'(Stade [^,]+)',
                    r'(Stadium [^,]+)',
                    r'([A-Z][a-z]+ [A-Z][a-z]+, [A-Z][a-z]+, [A-Z][a-z]+)'  # City, Country pattern
                ]
                
                for pattern in venue_patterns:
                    venue_match = re.search(pattern, row_text)
                    if venue_match:
                        venue = venue_match.group(1).strip()
                        break
                
                # Extract TV network
                tv_network = None
                tv_patterns = [
                    r'\b(FOX|ESPN|NBC|CBS|ABC|BBC|ITV|FS1|FS2|NBCSN|USA|TNT|TBS)\b'
                ]
                
                for pattern in tv_patterns:
                    tv_match = re.search(pattern, row_text)
                    if tv_match:
                        tv_network = tv_match.group(1)
                        break
                
                # Extract betting odds
                odds_info = []
                odds_patterns = [
                    r'Line: ([A-Z]+ [+-]\d+)',
                    r'O/U: ([\d.]+)'
                ]
                
                for pattern in odds_patterns:
                    odds_matches = re.findall(pattern, row_text)
                    odds_info.extend(odds_matches)
                
                # Determine the actual league/competition for this match
                leagues = ["International Football"]  # Default
                
                # Check if any competition from the page applies to this match
                team_text_lower = " ".join(teams).lower()
                
                # Look for specific league indicators based on teams or context
                if any(comp for comp in unique_competitions if 'women' in comp.lower() and 'euro' in comp.lower()):
                    # Check if this is a women's Euro match
                    if any(team in ['England', 'Germany', 'Spain', 'France', 'Italy', 'Netherlands'] for team in teams):
                        leagues = ["UEFA Women's European Championship", "European Football"]
                elif any(comp for comp in unique_competitions if 'champions league' in comp.lower()):
                    leagues = ["UEFA Champions League", "European Football"]
                elif any(comp for comp in unique_competitions if 'liga mx' in comp.lower() or 'mexican' in comp.lower()):
                    if any(word in team_text_lower for word in ['unam', 'pachuca', 'america', 'cruz azul', 'tigres']):
                        leagues = ["Liga MX", "Mexican Football"]
                elif any(comp for comp in unique_competitions if 'premier league' in comp.lower()):
                    leagues = ["Premier League", "English Football"]
                elif any(comp for comp in unique_competitions if 'friendly' in comp.lower()):
                    leagues = ["International Friendly", "Friendly Match"]
                else:
                    # Try to categorize based on team patterns
                    if any(word in team_text_lower for word in ['unam', 'pachuca', 'america']):
                        leagues = ["Liga MX", "Mexican Football"]
                    elif any(word in team_text_lower for word in ['galatasaray', 'fenerbahce', 'trabzonspor']):
                        leagues = ["Turkish Football", "International Football"]
                    elif any(word in team_text_lower for word in ['real madrid', 'barcelona', 'atletico']):
                        leagues = ["La Liga", "Spanish Football"]
                    else:
                        leagues = ["International Football", "Soccer"]
                
                # Create enhanced event name with additional info
                event_name = f"{teams[0]} vs {teams[1]}"
                if tv_network:
                    event_name += f" (TV: {tv_network})"
                if odds_info:
                    event_name += f" [Odds: {', '.join(odds_info)}]"
                
                event = create_event(
                    sport="futbol",
                    date=event_date,
                    event=event_name,
                    participants=teams,
                    location=venue,
                    leagues=leagues  # This should now be a proper list, not individual characters
                )
                events.append(event)
                
            except Exception as e:
                self.logger.debug(f"Error parsing ESPN soccer match row: {e}")
                continue
        
        return events
    
    def _parse_soccer_date(self, date_string: str, reference_date: datetime = None) -> str:
        """
        Parse various soccer date formats into ISO format.
        
        Args:
            date_string: Date string from website
            reference_date: Reference date for relative parsing
        
        Returns:
            ISO formatted date string
        """
        if not date_string:
            return (datetime.now() + timedelta(days=1)).isoformat() + "Z"
        
        reference_date = reference_date or datetime.now()
        
        try:
            # Common patterns for soccer dates
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
                        clean_date_with_year = f"{clean_date}, {reference_date.year}"
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
            self.logger.debug(f"Error parsing soccer date '{date_string}': {e}")
        
        # Default to tomorrow if parsing fails
        return (reference_date + timedelta(days=1)).isoformat() + "Z"