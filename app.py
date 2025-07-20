#!/usr/bin/env python3
"""
Daily Sports Calendar App
A comprehensive sports schedule tracker with API integration and calendar sync.

Fetches and stores daily schedules for:
- Fútbol (Soccer)
- NFL
- NBA
- F1
- Boxing
- MMA/UFC
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import json

# Core imports
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Optional Google Calendar integration
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False
    print("Google Calendar integration not available. Install google-api-python-client for calendar sync.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sports_calendar.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_NAME = 'sports_calendar.db'

# Event schema template
EVENT_SCHEMA = {
    "sport": "",
    "date": "",  # ISO format: "2025-07-20T18:00:00Z"
    "event": "",
    "participants": [],
    "location": ""
}


class DatabaseManager:
    """Handles SQLite database operations for sports events."""
    
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL,
                    date TEXT NOT NULL,
                    event TEXT NOT NULL,
                    participants TEXT NOT NULL,  -- JSON array
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_calendar BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sport_date ON events(sport, date)')
            conn.commit()
            logger.info("Database initialized successfully")
    
    def insert_events(self, events: List[Dict]) -> int:
        """Insert new events into the database, avoiding duplicates."""
        if not events:
            return 0
        
        inserted_count = 0
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            for event in events:
                # Check if event already exists
                cursor.execute('''
                    SELECT id FROM events 
                    WHERE sport = ? AND date = ? AND event = ?
                ''', (event['sport'], event['date'], event['event']))
                
                if cursor.fetchone() is None:
                    cursor.execute('''
                        INSERT INTO events (sport, date, event, participants, location)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        event['sport'],
                        event['date'],
                        event['event'],
                        json.dumps(event['participants']),
                        event['location']
                    ))
                    inserted_count += 1
            
            conn.commit()
        
        logger.info(f"Inserted {inserted_count} new events into database")
        return inserted_count
    
    def get_upcoming_events(self, sport: Optional[str] = None, days: int = 7) -> List[Dict]:
        """Get upcoming events for a specific sport or all sports."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            end_date = (datetime.now() + timedelta(days=days)).isoformat()
            
            if sport:
                cursor.execute('''
                    SELECT sport, date, event, participants, location 
                    FROM events 
                    WHERE sport = ? AND date >= datetime('now') AND date <= ?
                    ORDER BY date
                ''', (sport, end_date))
            else:
                cursor.execute('''
                    SELECT sport, date, event, participants, location 
                    FROM events 
                    WHERE date >= datetime('now') AND date <= ?
                    ORDER BY date
                ''', (end_date,))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'sport': row[0],
                    'date': row[1],
                    'event': row[2],
                    'participants': json.loads(row[3]),
                    'location': row[4]
                })
            
            return events


class SportsFetcher:
    """Base class for sports data fetchers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Daily-Sports-Calendar-App/1.0'
        })
    
    def fetch_events(self, sport: str) -> List[Dict]:
        """Fetch events for a specific sport."""
        method_name = f"fetch_{sport}"
        if hasattr(self, method_name):
            return getattr(self, method_name)()
        else:
            logger.warning(f"No fetch method implemented for sport: {sport}")
            return []
    
    def parse_events(self, sport: str, raw_data: any) -> List[Dict]:
        """Parse raw data into standardized event format."""
        method_name = f"parse_{sport}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(raw_data)
        else:
            logger.warning(f"No parse method implemented for sport: {sport}")
            return []
    
    # F1 Implementation using Ergast API
    def fetch_f1(self) -> List[Dict]:
        """Fetch F1 race schedule from Ergast API."""
        try:
            current_year = datetime.now().year
            url = f"http://ergast.com/api/f1/{current_year}.json"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self.parse_f1(data)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch F1 data: {e}")
            return []
    
    def parse_f1(self, raw_data: Dict) -> List[Dict]:
        """Parse F1 data from Ergast API into standardized format."""
        events = []
        
        try:
            races = raw_data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
            
            for race in races:
                # Convert race date and time to ISO format
                race_date = race.get('date', '')
                race_time = race.get('time', '00:00:00Z')
                
                if race_date:
                    # Remove 'Z' from time if present and add it back
                    if race_time.endswith('Z'):
                        race_time = race_time[:-1]
                    
                    datetime_str = f"{race_date}T{race_time}Z"
                    
                    # Get circuit information
                    circuit = race.get('Circuit', {})
                    location = f"{circuit.get('circuitName', 'Unknown Circuit')}, {circuit.get('Location', {}).get('country', 'Unknown')}"
                    
                    event = {
                        "sport": "f1",
                        "date": datetime_str,
                        "event": f"F1 {race.get('raceName', 'Grand Prix')}",
                        "participants": ["F1 Drivers"],  # Could be expanded with driver list
                        "location": location
                    }
                    
                    events.append(event)
                    
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing F1 data: {e}")
        
        logger.info(f"Parsed {len(events)} F1 events")
        return events
    
    # Placeholder methods for other sports
    def fetch_futbol(self) -> List[Dict]:
        """Fetch soccer/football schedules."""
        # TODO: Implement using API-Football or similar
        logger.info("Futbol fetching not yet implemented")
        return []
    
    def parse_futbol(self, raw_data: any) -> List[Dict]:
        """Parse soccer/football data."""
        return []
    
    def fetch_nfl(self) -> List[Dict]:
        """Fetch NFL schedules."""
        # TODO: Implement using SportsDataIO or ESPN API
        logger.info("NFL fetching not yet implemented")
        return []
    
    def parse_nfl(self, raw_data: any) -> List[Dict]:
        """Parse NFL data."""
        return []
    
    def fetch_nba(self) -> List[Dict]:
        """Fetch NBA schedules."""
        # TODO: Implement using NBA API or SportsDataIO
        logger.info("NBA fetching not yet implemented")
        return []
    
    def parse_nba(self, raw_data: any) -> List[Dict]:
        """Parse NBA data."""
        return []
    
    def fetch_boxing(self) -> List[Dict]:
        """Fetch boxing schedules."""
        # TODO: Implement using web scraping or specialized API
        logger.info("Boxing fetching not yet implemented")
        return []
    
    def parse_boxing(self, raw_data: any) -> List[Dict]:
        """Parse boxing data."""
        return []
    
    def fetch_mma(self) -> List[Dict]:
        """Fetch MMA/UFC schedules."""
        # TODO: Implement using UFC API or RapidAPI
        logger.info("MMA fetching not yet implemented")
        return []
    
    def parse_mma(self, raw_data: any) -> List[Dict]:
        """Parse MMA data."""
        return []


class CalendarSync:
    """Google Calendar synchronization functionality."""
    
    def __init__(self):
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar
        
        if GOOGLE_CALENDAR_AVAILABLE:
            self.setup_google_calendar()
    
    def setup_google_calendar(self):
        """Setup Google Calendar API credentials."""
        # TODO: Implement OAuth2 flow
        logger.info("Google Calendar sync not yet configured")
        pass
    
    def sync_events(self, events: List[Dict]) -> int:
        """Sync events to Google Calendar."""
        if not GOOGLE_CALENDAR_AVAILABLE or not self.service:
            logger.warning("Google Calendar sync not available")
            return 0
        
        # TODO: Implement calendar event creation
        logger.info(f"Would sync {len(events)} events to Google Calendar")
        return 0


class SportsCalendarApp:
    """Main application class."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.fetcher = SportsFetcher()
        self.calendar_sync = CalendarSync()
        self.supported_sports = ['f1', 'futbol', 'nfl', 'nba', 'boxing', 'mma']
    
    def fetch_all_sports(self) -> int:
        """Fetch events for all supported sports."""
        total_events = 0
        all_events = []
        
        for sport in self.supported_sports:
            logger.info(f"Fetching {sport} events...")
            events = self.fetcher.fetch_events(sport)
            all_events.extend(events)
            total_events += len(events)
        
        # Store events in database
        inserted = self.db.insert_events(all_events)
        logger.info(f"Fetched {total_events} total events, inserted {inserted} new events")
        
        return inserted
    
    def show_upcoming_events(self, sport: Optional[str] = None, days: int = 7):
        """Display upcoming events."""
        events = self.db.get_upcoming_events(sport, days)
        
        if not events:
            print(f"No upcoming events found for {sport or 'any sport'}")
            return
        
        print(f"\nUpcoming {sport or 'sports'} events (next {days} days):")
        print("-" * 60)
        
        for event in events:
            date_obj = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            print(f"{event['sport'].upper()}: {event['event']}")
            print(f"  Date: {date_obj.strftime('%Y-%m-%d %H:%M %Z')}")
            print(f"  Location: {event['location']}")
            print(f"  Participants: {', '.join(event['participants'])}")
            print()
    
    def sync_to_calendar(self):
        """Sync new events to Google Calendar."""
        # Get unsynced events
        # TODO: Implement sync logic
        logger.info("Calendar sync functionality not yet implemented")
    
    def start_scheduler(self):
        """Start the daily scheduler."""
        scheduler = BlockingScheduler()
        
        # Schedule daily fetch at 2:00 AM
        scheduler.add_job(
            self.fetch_all_sports,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_fetch',
            replace_existing=True
        )
        
        logger.info("Scheduler started. Daily fetch scheduled for 2:00 AM")
        
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Daily Sports Calendar App')
    parser.add_argument('command', choices=['fetch', 'show', 'sync', 'schedule'],
                       help='Command to execute')
    parser.add_argument('sport', nargs='?', 
                       choices=['f1', 'futbol', 'nfl', 'nba', 'boxing', 'mma'],
                       help='Specific sport (for show command)')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to show (default: 7)')
    
    args = parser.parse_args()
    
    app = SportsCalendarApp()
    
    if args.command == 'fetch':
        app.fetch_all_sports()
    
    elif args.command == 'show':
        app.show_upcoming_events(args.sport, args.days)
    
    elif args.command == 'sync':
        app.sync_to_calendar()
    
    elif args.command == 'schedule':
        app.start_scheduler()


if __name__ == '__main__':
    main()