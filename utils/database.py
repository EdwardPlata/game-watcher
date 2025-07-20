"""
Database management utilities.
Handles SQLite database operations for sports events.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .logger import LoggerMixin


class DatabaseManager(LoggerMixin):
    """Handles SQLite database operations for sports events."""
    
    def __init__(self, db_name: str = 'sports_calendar.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create the events table with all columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sport TEXT NOT NULL,
                    date TEXT NOT NULL,
                    event TEXT NOT NULL,
                    participants TEXT NOT NULL,  -- JSON array
                    location TEXT,
                    leagues TEXT,  -- JSON array of leagues/tags
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_calendar BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Check if leagues column exists, if not add it
            cursor.execute("PRAGMA table_info(events)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'leagues' not in columns:
                cursor.execute('ALTER TABLE events ADD COLUMN leagues TEXT DEFAULT "[]"')
                self.logger.info("Added leagues column to events table")
            
            # Create index for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sport_date ON events(sport, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON events(scraped_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leagues ON events(leagues)')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
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
                        INSERT INTO events (sport, date, event, participants, location, leagues, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        event['sport'],
                        event['date'],
                        event['event'],
                        json.dumps(event['participants']),
                        event['location'],
                        json.dumps(event.get('leagues', []))
                    ))
                    inserted_count += 1
            
            conn.commit()
        
        self.logger.info(f"Inserted {inserted_count} new events into database")
        return inserted_count
    
    def get_upcoming_events(self, sport: Optional[str] = None, days: int = 7) -> List[Dict]:
        """Get upcoming events for a specific sport or all sports."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            end_date = (datetime.now() + timedelta(days=days)).isoformat()
            
            if sport:
                cursor.execute('''
                    SELECT sport, date, event, participants, location, leagues
                    FROM events 
                    WHERE sport = ? AND date >= datetime('now') AND date <= ?
                    ORDER BY date
                ''', (sport, end_date))
            else:
                cursor.execute('''
                    SELECT sport, date, event, participants, location, leagues
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
                    'location': row[4],
                    'leagues': json.loads(row[5]) if row[5] else []
                })
            
            return events
    
    def get_unsynced_events(self) -> List[Dict]:
        """Get events that haven't been synced to calendar."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sport, date, event, participants, location 
                FROM events 
                WHERE synced_to_calendar = FALSE
                ORDER BY date
            ''')
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row[0],
                    'sport': row[1],
                    'date': row[2],
                    'event': row[3],
                    'participants': json.loads(row[4]),
                    'location': row[5]
                })
            
            return events
    
    def mark_synced(self, event_ids: List[int]):
        """Mark events as synced to calendar."""
        if not event_ids:
            return
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            placeholders = ','.join('?' * len(event_ids))
            cursor.execute(f'''
                UPDATE events 
                SET synced_to_calendar = TRUE 
                WHERE id IN ({placeholders})
            ''', event_ids)
            conn.commit()
            
        self.logger.info(f"Marked {len(event_ids)} events as synced")
    
    def insert_event(self, event: Dict) -> bool:
        """Insert a single event into the database."""
        return self.insert_events([event]) > 0
    
    def get_event_count(self) -> int:
        """Get total count of events in database."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM events')
            return cursor.fetchone()[0]
    
    def get_events_by_sport(self, sport: str, limit: int = 1000) -> List[Dict]:
        """Get all events for a specific sport."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sport, date, event, participants, location, leagues, scraped_at
                FROM events 
                WHERE sport = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (sport, limit))
            
            events = []
            for row in cursor.fetchall():
                events.append(dict(row))
            
            return events
    
    def get_all_events(self, limit: int = 1000) -> List[Dict]:
        """Get all events from database."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sport, date, event, participants, location, leagues, scraped_at
                FROM events 
                ORDER BY date DESC
                LIMIT ?
            ''', (limit,))
            
            events = []
            for row in cursor.fetchall():
                events.append(dict(row))
            
            return events
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Get a specific event by ID."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sport, date, event, participants, location, leagues, scraped_at
                FROM events 
                WHERE id = ?
            ''', (event_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
