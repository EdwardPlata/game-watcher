"""
Anvil Server Module for Game Watcher
Converts FastAPI routes to Anvil server callable functions
"""

from utils.event_schema import validate_event
from utils.logger import get_logger
from collectors.betting import BettingOddsCollector
from collectors import COLLECTORS, get_collector
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import json
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

# Import our existing collectors - they can still be used with Anvil
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


logger = get_logger(__name__)


# Data Table Schema Setup
# These would be created in Anvil's Data Tables section
# events table: id, sport, date, event, participants, location, leagues, watch_link, created_at, scraped_at, synced_to_calendar
# betting_odds table: id, event_id, bookmaker, market_type, odds_data, inserted_at


@anvil.server.callable
def health_check():
    """Health check endpoint - converted from FastAPI route."""
    try:
        # Test database connection by counting events
        total_events = len(list(app_tables.events.search()))
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        total_events = 0
        db_connected = False

    return {
        "status": "healthy" if db_connected else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "database_connected": db_connected,
        "total_events": total_events,
        "supported_sports": list(COLLECTORS.keys())
    }


@anvil.server.callable
def get_sports():
    """Get list of supported sports with statistics."""
    sports = []

    for sport_key, collector_class in COLLECTORS.items():
        try:
            # Get event count for this sport
            events = list(app_tables.events.search(sport=sport_key))
            total_events = len(events)

            # Get last update time
            last_updated = None
            if events:
                last_updated = max(event['scraped_at']
                                   for event in events if event['scraped_at'])
                if last_updated:
                    last_updated = last_updated.isoformat()

            sport_info = {
                "name": sport_key,
                "display_name": sport_key.upper(),
                "description": f"{sport_key.title()} schedule and events",
                "total_events": total_events,
                "last_updated": last_updated
            }
            sports.append(sport_info)

        except Exception as e:
            logger.error(f"Error getting info for sport {sport_key}: {e}")
            sport_info = {
                "name": sport_key,
                "display_name": sport_key.upper(),
                "description": f"{sport_key.title()} schedule and events",
                "total_events": 0,
                "last_updated": None
            }
            sports.append(sport_info)

    return {"sports": sports, "total": len(sports)}


@anvil.server.callable
def get_events(sport=None, start_date=None, end_date=None, limit=100):
    """Get events with optional filtering."""
    try:
        if sport and sport not in COLLECTORS:
            raise ValueError(f"Unsupported sport: {sport}")

        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise ValueError("Invalid start_date format. Use YYYY-MM-DD")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise ValueError("Invalid end_date format. Use YYYY-MM-DD")

        # Build query
        query_params = {}
        if sport:
            query_params['sport'] = sport

        # Get events from Anvil Data Tables
        events_query = app_tables.events.search(**query_params)

        # Filter by date range if specified
        if start_dt or end_dt:
            filtered_events = []
            for event in events_query:
                try:
                    event_date = event['date']
                    if isinstance(event_date, str):
                        event_date = datetime.fromisoformat(
                            event_date.replace('Z', '+00:00'))
                    if start_dt and event_date < start_dt:
                        continue
                    if end_dt and event_date > end_dt:
                        continue
                    filtered_events.append(event)
                except (ValueError, TypeError):
                    # Skip events with invalid dates
                    continue
            events = filtered_events[:limit]
        else:
            events = list(events_query)[:limit]

        # Convert to response format
        event_responses = []
        for event in events:
            try:
                # Parse participants JSON if it's a string
                participants = event['participants'] or []
                if isinstance(participants, str):
                    try:
                        participants = json.loads(participants)
                    except (json.JSONDecodeError, TypeError):
                        participants = [participants] if participants else []

                # Parse leagues JSON if it's a string
                leagues = event['leagues'] or []
                if isinstance(leagues, str):
                    try:
                        leagues = json.loads(leagues)
                    except (json.JSONDecodeError, TypeError):
                        leagues = [leagues] if leagues else []

                event_response = {
                    "id": event.get_id(),
                    "sport": event['sport'],
                    "date": event['date'].isoformat() if hasattr(event['date'], 'isoformat') else event['date'],
                    "event": event['event'],
                    "participants": participants,
                    "location": event['location'],
                    "leagues": leagues,
                    "watch_link": event['watch_link'],
                    "scraped_at": event['scraped_at'].isoformat() if event['scraped_at'] and hasattr(event['scraped_at'], 'isoformat') else event['scraped_at']
                }
                event_responses.append(event_response)
            except Exception as e:
                logger.error(f"Error converting event {event.get_id()}: {e}")
                continue

        date_range = None
        if start_date and end_date:
            date_range = f"{start_date} to {end_date}"
        elif start_date:
            date_range = f"from {start_date}"
        elif end_date:
            date_range = f"until {end_date}"

        return {
            "events": event_responses,
            "total": len(event_responses),
            "sport": sport,
            "date_range": date_range
        }

    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise anvil.server.AnvilWrappedError(f"Error getting events: {str(e)}")


@anvil.server.callable
def get_event(event_id):
    """Get a specific event by ID."""
    try:
        event = app_tables.events.get_by_id(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Parse participants and leagues
        participants = event['participants'] or []
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except (json.JSONDecodeError, TypeError):
                participants = [participants] if participants else []

        leagues = event['leagues'] or []
        if isinstance(leagues, str):
            try:
                leagues = json.loads(leagues)
            except (json.JSONDecodeError, TypeError):
                leagues = [leagues] if leagues else []

        return {
            "id": event.get_id(),
            "sport": event['sport'],
            "date": event['date'].isoformat() if hasattr(event['date'], 'isoformat') else event['date'],
            "event": event['event'],
            "participants": participants,
            "location": event['location'],
            "leagues": leagues,
            "watch_link": event['watch_link'],
            "scraped_at": event['scraped_at'].isoformat() if event['scraped_at'] and hasattr(event['scraped_at'], 'isoformat') else event['scraped_at']
        }

    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise anvil.server.AnvilWrappedError(f"Error getting event: {str(e)}")


@anvil.server.callable
def collect_sport_data(sport):
    """Collect data for a specific sport."""
    try:
        if sport not in COLLECTORS:
            raise ValueError(f"Unsupported sport: {sport}")

        # Get collector instance
        collector = get_collector(sport)

        # Fetch events
        events = collector.collect_events()

        # Insert events into Anvil Data Tables
        inserted_count = 0
        for event_data in events:
            try:
                # Validate event data
                if not validate_event(event_data):
                    logger.warning(f"Invalid event data: {event_data}")
                    continue

                # Check if event already exists (basic deduplication)
                existing = app_tables.events.search(
                    sport=event_data['sport'],
                    date=q.between(
                        datetime.fromisoformat(
                            event_data['date']) - timedelta(hours=1),
                        datetime.fromisoformat(
                            event_data['date']) + timedelta(hours=1)
                    ),
                    event=event_data['event']
                )

                if list(existing):
                    continue  # Skip duplicates

                # Insert new event
                app_tables.events.add_row(
                    sport=event_data['sport'],
                    date=datetime.fromisoformat(event_data['date']),
                    event=event_data['event'],
                    participants=json.dumps(
                        event_data.get('participants', [])),
                    location=event_data.get('location'),
                    leagues=json.dumps(event_data.get('leagues', [])),
                    watch_link=event_data.get('watch_link'),
                    created_at=datetime.now(),
                    scraped_at=datetime.now(),
                    synced_to_calendar=False
                )
                inserted_count += 1

            except Exception as e:
                logger.error(f"Error inserting event: {e}")
                continue

        return {
            "sport": sport,
            "events_collected": len(events),
            "events_inserted": inserted_count,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error collecting data for {sport}: {e}")
        raise anvil.server.AnvilWrappedError(
            f"Error collecting data: {str(e)}")


@anvil.server.callable
def collect_all_sports_data():
    """Collect data for all supported sports."""
    results = {}
    total_inserted = 0

    for sport in COLLECTORS.keys():
        try:
            result = collect_sport_data(sport)
            results[sport] = result
            total_inserted += result['events_inserted']
        except Exception as e:
            logger.error(f"Error collecting data for {sport}: {e}")
            results[sport] = {
                "sport": sport,
                "events_collected": 0,
                "events_inserted": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    return {
        "results": results,
        "total_sports": len(COLLECTORS),
        "total_events_inserted": total_inserted,
        "timestamp": datetime.now().isoformat()
    }


@anvil.server.callable
def get_calendar_month(year, month):
    """Get calendar data for a specific month."""
    try:
        # Create start and end dates for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        # Get events for the month
        events = list(app_tables.events.search(
            date=q.between(start_date, end_date + timedelta(days=1))
        ))

        # Group events by day
        days = {}
        for event in events:
            event_date = event['date']
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date)

            day_key = event_date.day
            if day_key not in days:
                days[day_key] = {
                    "date": day_key,
                    "events": [],
                    "event_count": 0
                }

            # Parse participants
            participants = event['participants'] or []
            if isinstance(participants, str):
                try:
                    participants = json.loads(participants)
                except (json.JSONDecodeError, TypeError):
                    participants = [participants] if participants else []

            days[day_key]["events"].append({
                "id": event.get_id(),
                "sport": event['sport'],
                "event": event['event'],
                "participants": participants,
                "time": event_date.strftime("%H:%M") if event_date.hour or event_date.minute else None
            })
            days[day_key]["event_count"] += 1

        return {
            "year": year,
            "month": month,
            "days": list(days.values()),
            "total_events": len(events)
        }

    except Exception as e:
        logger.error(f"Error getting calendar for {year}-{month}: {e}")
        raise anvil.server.AnvilWrappedError(
            f"Error getting calendar: {str(e)}")


@anvil.server.callable
def get_calendar_day(year, month, day):
    """Get detailed events for a specific day."""
    try:
        # Create date range for the day
        start_date = datetime(year, month, day)
        end_date = start_date + timedelta(days=1)

        # Get events for the day
        events = list(app_tables.events.search(
            date=q.between(start_date, end_date)
        ))

        # Convert to response format
        event_list = []
        for event in events:
            participants = event['participants'] or []
            if isinstance(participants, str):
                try:
                    participants = json.loads(participants)
                except (json.JSONDecodeError, TypeError):
                    participants = [participants] if participants else []

            leagues = event['leagues'] or []
            if isinstance(leagues, str):
                try:
                    leagues = json.loads(leagues)
                except (json.JSONDecodeError, TypeError):
                    leagues = [leagues] if leagues else []

            event_list.append({
                "id": event.get_id(),
                "sport": event['sport'],
                "date": event['date'].isoformat() if hasattr(event['date'], 'isoformat') else event['date'],
                "event": event['event'],
                "participants": participants,
                "location": event['location'],
                "leagues": leagues,
                "watch_link": event['watch_link']
            })

        return {
            "date": f"{year}-{month:02d}-{day:02d}",
            "events": event_list,
            "total": len(event_list)
        }

    except Exception as e:
        logger.error(f"Error getting day events for {year}-{month}-{day}: {e}")
        raise anvil.server.AnvilWrappedError(
            f"Error getting day events: {str(e)}")


@anvil.server.callable
def get_betting_odds(event_id=None, sport=None):
    """Get betting odds for events."""
    try:
        query_params = {}
        if event_id:
            query_params['event_id'] = event_id
        if sport:
            # Get event IDs for the sport first
            sport_events = list(app_tables.events.search(sport=sport))
            sport_event_ids = [event.get_id() for event in sport_events]
            if sport_event_ids:
                # This would need to be adapted based on Anvil's query capabilities
                # For now, we'll get all odds and filter
                pass

        odds = list(app_tables.betting_odds.search(**query_params))

        odds_list = []
        for odd in odds:
            odds_data = odd['odds_data']
            if isinstance(odds_data, str):
                try:
                    odds_data = json.loads(odds_data)
                except (json.JSONDecodeError, TypeError):
                    odds_data = {}

            odds_list.append({
                "id": odd.get_id(),
                "event_id": odd['event_id'],
                "bookmaker": odd['bookmaker'],
                "market_type": odd['market_type'],
                "odds_data": odds_data,
                "inserted_at": odd['inserted_at'].isoformat() if odd['inserted_at'] and hasattr(odd['inserted_at'], 'isoformat') else odd['inserted_at']
            })

        return {
            "odds": odds_list,
            "total": len(odds_list)
        }

    except Exception as e:
        logger.error(f"Error getting betting odds: {e}")
        raise anvil.server.AnvilWrappedError(
            f"Error getting betting odds: {str(e)}")


@anvil.server.callable
def collect_betting_odds():
    """Collect betting odds for recent events."""
    try:
        # Get recent events (last 7 days and next 7 days)
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() + timedelta(days=7)

        recent_events = list(app_tables.events.search(
            date=q.between(start_date, end_date)
        ))

        if not recent_events:
            return {
                "message": "No recent events found",
                "odds_inserted": 0,
                "timestamp": datetime.now().isoformat()
            }

        # Initialize betting collector
        betting_collector = BettingOddsCollector()

        # Group events by sport for efficient API calls
        events_by_sport = {}
        for event in recent_events:
            sport = event['sport']
            if sport not in events_by_sport:
                events_by_sport[sport] = []
            events_by_sport[sport].append(event)

        total_odds_inserted = 0

        for sport, events in events_by_sport.items():
            try:
                # Collect odds for this sport
                odds_data = betting_collector.collect_odds_for_sport(sport)

                for odds_entry in odds_data:
                    # Find matching event
                    matching_event = None
                    for event in events:
                        # Simple matching logic - could be improved
                        if (odds_entry.get('teams') and
                                any(team.lower() in event['event'].lower() for team in odds_entry['teams'])):
                            matching_event = event
                            break

                    if matching_event:
                        # Insert odds
                        app_tables.betting_odds.add_row(
                            event_id=matching_event.get_id(),
                            bookmaker=odds_entry.get('bookmaker', 'unknown'),
                            market_type=odds_entry.get('market_type', 'h2h'),
                            odds_data=json.dumps(odds_entry),
                            inserted_at=datetime.now()
                        )
                        total_odds_inserted += 1

            except Exception as e:
                logger.error(f"Error collecting odds for {sport}: {e}")
                continue

        return {
            "message": f"Collected betting odds for {len(events_by_sport)} sports",
            "odds_inserted": total_odds_inserted,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error collecting betting odds: {e}")
        raise anvil.server.AnvilWrappedError(
            f"Error collecting betting odds: {str(e)}")
