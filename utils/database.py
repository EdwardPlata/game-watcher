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
                    watch_link TEXT,  -- Link to watch event online
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
            
            # Check if watch_link column exists, if not add it
            if 'watch_link' not in columns:
                cursor.execute('ALTER TABLE events ADD COLUMN watch_link TEXT')
                self.logger.info("Added watch_link column to events table")
            
            # Create index for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sport_date ON events(sport, date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON events(scraped_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_leagues ON events(leagues)')
            
            # Create webhook_config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS webhook_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    url TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create betting_odds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS betting_odds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    sport TEXT NOT NULL,
                    commence_time TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    participants TEXT NOT NULL,  -- JSON array
                    odds_data TEXT NOT NULL,  -- JSON array of all odds
                    best_odds TEXT NOT NULL,  -- JSON object with best odds
                    bookmaker_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(event_id, sport, commence_time)
                )
            ''')
            
            # Create index for faster odds queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_sport_time ON betting_odds(sport, commence_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_odds_scraped ON betting_odds(scraped_at)')
            
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
                        INSERT INTO events (sport, date, event, participants, location, leagues, watch_link, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        event['sport'],
                        event['date'],
                        event['event'],
                        json.dumps(event['participants']),
                        event['location'],
                        json.dumps(event.get('leagues', [])),
                        event.get('watch_link')
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
                SELECT id, sport, date, event, participants, location, leagues, watch_link, scraped_at
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
                SELECT id, sport, date, event, participants, location, leagues, watch_link, scraped_at
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
                SELECT id, sport, date, event, participants, location, leagues, watch_link, scraped_at
                FROM events 
                WHERE id = ?
            ''', (event_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_webhook_configs(self) -> List[Dict]:
        """Get all enabled webhook configurations."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, url, enabled
                FROM webhook_config 
                WHERE enabled = TRUE
            ''')
            
            configs = []
            for row in cursor.fetchall():
                configs.append(dict(row))
            
            return configs
    
    def add_webhook_config(self, name: str, url: str, enabled: bool = True) -> int:
        """Add a new webhook configuration."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO webhook_config (name, url, enabled)
                VALUES (?, ?, ?)
            ''', (name, url, enabled))
            conn.commit()
            return cursor.lastrowid
    
    def get_new_events_since(self, since_timestamp: str) -> List[Dict]:
        """Get events added since a specific timestamp."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, sport, date, event, participants, location, leagues, watch_link, scraped_at
                FROM events 
                WHERE scraped_at > ?
                ORDER BY scraped_at ASC
            ''', (since_timestamp,))
            
            events = []
            for row in cursor.fetchall():
                events.append(dict(row))
            
            return events
    
    def insert_betting_odds(self, odds_data: List[Dict]) -> int:
        """Insert betting odds into database, updating existing entries."""
        if not odds_data:
            return 0
        
        inserted_count = 0
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            for odds in odds_data:
                try:
                    # Insert or replace odds entry
                    cursor.execute('''
                        INSERT OR REPLACE INTO betting_odds 
                        (event_id, sport, commence_time, home_team, away_team, 
                         participants, odds_data, best_odds, bookmaker_count, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        odds.get('event_id', ''),
                        odds.get('sport', ''),
                        odds.get('commence_time', ''),
                        odds.get('home_team', ''),
                        odds.get('away_team', ''),
                        json.dumps(odds.get('participants', [])),
                        json.dumps(odds.get('odds_data', [])),
                        json.dumps(odds.get('best_odds', {})),
                        odds.get('bookmaker_count', 0)
                    ))
                    inserted_count += 1
                except Exception as e:
                    self.logger.error(f"Error inserting betting odds: {e}")
                    continue
            
            conn.commit()
        
        self.logger.info(f"Inserted/Updated {inserted_count} betting odds entries")
        return inserted_count
    
    def get_odds_for_event(self, sport: str, participants: List[str]) -> Optional[Dict]:
        """Get betting odds for a specific event by matching participants."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get recent odds for this sport
            cursor.execute('''
                SELECT id, event_id, sport, commence_time, home_team, away_team,
                       participants, odds_data, best_odds, bookmaker_count, scraped_at
                FROM betting_odds
                WHERE sport = ?
                AND datetime(commence_time) >= datetime('now')
                ORDER BY scraped_at DESC
                LIMIT 100
            ''', (sport,))
            
            odds_entries = []
            for row in cursor.fetchall():
                odds_entries.append(dict(row))
            
            # Match by participants
            for odds_entry in odds_entries:
                odds_participants = json.loads(odds_entry['participants'])
                # Check if there's overlap in participants
                if any(p.lower() in ' '.join(participants).lower() for p in odds_participants):
                    # Parse JSON fields
                    odds_entry['participants'] = odds_participants
                    odds_entry['odds_data'] = json.loads(odds_entry['odds_data'])
                    odds_entry['best_odds'] = json.loads(odds_entry['best_odds'])
                    return odds_entry
            
            return None
    
    def get_all_betting_odds(self, sport: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all betting odds, optionally filtered by sport."""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if sport:
                cursor.execute('''
                    SELECT id, event_id, sport, commence_time, home_team, away_team,
                           participants, odds_data, best_odds, bookmaker_count, scraped_at
                    FROM betting_odds
                    WHERE sport = ?
                    AND datetime(commence_time) >= datetime('now')
                    ORDER BY commence_time ASC
                    LIMIT ?
                ''', (sport, limit))
            else:
                cursor.execute('''
                    SELECT id, event_id, sport, commence_time, home_team, away_team,
                           participants, odds_data, best_odds, bookmaker_count, scraped_at
                    FROM betting_odds
                    WHERE datetime(commence_time) >= datetime('now')
                    ORDER BY commence_time ASC
                    LIMIT ?
                ''', (limit,))
            
            odds_list = []
            for row in cursor.fetchall():
                odds_entry = dict(row)
                # Parse JSON fields
                odds_entry['participants'] = json.loads(odds_entry['participants'])
                odds_entry['odds_data'] = json.loads(odds_entry['odds_data'])
                odds_entry['best_odds'] = json.loads(odds_entry['best_odds'])
                odds_list.append(odds_entry)
            
            return odds_list

