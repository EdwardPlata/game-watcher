"""
FastAPI routes for sports calendar API.
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
import json

from utils import DatabaseManager, get_logger
from collectors import COLLECTORS, get_collector
from .models import (
    EventResponse, EventsResponse, SportInfo, SportsResponse,
    CalendarDay, CalendarMonth, HealthStatus, CollectionResult
)

logger = get_logger(__name__)
router = APIRouter()


def get_db():
    """Dependency to get database manager."""
    return DatabaseManager()


@router.get("/health", response_model=HealthStatus)
async def health_check(db: DatabaseManager = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        total_events = db.get_event_count()
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        total_events = 0
        db_connected = False
    
    return HealthStatus(
        status="healthy" if db_connected else "unhealthy",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected,
        total_events=total_events,
        supported_sports=list(COLLECTORS.keys())
    )


@router.get("/sports", response_model=SportsResponse)
async def get_sports(db: DatabaseManager = Depends(get_db)):
    """Get list of supported sports with statistics."""
    sports = []
    
    for sport_key, collector_class in COLLECTORS.items():
        try:
            # Get event count for this sport
            events = db.get_events_by_sport(sport_key)
            total_events = len(events)
            
            # Get last update time
            last_updated = None
            if events:
                last_updated = max(event.get('scraped_at', '') for event in events)
            
            sport_info = SportInfo(
                name=sport_key,
                display_name=sport_key.upper(),
                description=f"{sport_key.title()} schedule and events",
                total_events=total_events,
                last_updated=last_updated
            )
            sports.append(sport_info)
            
        except Exception as e:
            logger.error(f"Error getting info for sport {sport_key}: {e}")
            sport_info = SportInfo(
                name=sport_key,
                display_name=sport_key.upper(),
                description=f"{sport_key.title()} schedule and events",
                total_events=0,
                last_updated=None
            )
            sports.append(sport_info)
    
    return SportsResponse(sports=sports, total=len(sports))


@router.get("/events", response_model=EventsResponse)
async def get_events(
    sport: Optional[str] = Query(None, description="Filter by sport"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    db: DatabaseManager = Depends(get_db)
):
    """Get events with optional filtering."""
    try:
        if sport and sport not in COLLECTORS:
            raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        
        # Get events from database
        if sport:
            events = db.get_events_by_sport(sport, limit=limit)
        else:
            events = db.get_all_events(limit=limit)
        
        # Filter by date range if specified
        if start_dt or end_dt:
            filtered_events = []
            for event in events:
                try:
                    event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
                    if start_dt and event_date < start_dt:
                        continue
                    if end_dt and event_date > end_dt:
                        continue
                    filtered_events.append(event)
                except ValueError:
                    # Skip events with invalid dates
                    continue
            events = filtered_events
        
        # Convert to response models
        event_responses = []
        for event in events:
            try:
                # Parse participants JSON if it's a string
                participants = event.get('participants', [])
                if isinstance(participants, str):
                    try:
                        participants = json.loads(participants)
                    except (json.JSONDecodeError, TypeError):
                        participants = [participants] if participants else []
                
                # Parse leagues JSON if it's a string
                leagues = event.get('leagues', [])
                if isinstance(leagues, str):
                    try:
                        leagues = json.loads(leagues)
                    except (json.JSONDecodeError, TypeError):
                        leagues = [leagues] if leagues else []
                
                event_response = EventResponse(
                    id=event['id'],
                    sport=event['sport'],
                    date=event['date'],
                    event=event['event'],
                    participants=participants,
                    location=event['location'],
                    leagues=leagues,
                    scraped_at=event['scraped_at']
                )
                event_responses.append(event_response)
            except Exception as e:
                logger.error(f"Error converting event {event.get('id')}: {e}")
                continue
        
        date_range = None
        if start_date and end_date:
            date_range = f"{start_date} to {end_date}"
        elif start_date:
            date_range = f"from {start_date}"
        elif end_date:
            date_range = f"until {end_date}"
        
        return EventsResponse(
            events=event_responses,
            total=len(event_responses),
            sport=sport,
            date_range=date_range
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: DatabaseManager = Depends(get_db)):
    """Get a specific event by ID."""
    try:
        event = db.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Parse participants JSON if it's a string
        participants = event.get('participants', [])
        if isinstance(participants, str):
            try:
                participants = json.loads(participants)
            except (json.JSONDecodeError, TypeError):
                participants = [participants] if participants else []
        
        # Parse leagues JSON if it's a string
        leagues = event.get('leagues', [])
        if isinstance(leagues, str):
            try:
                leagues = json.loads(leagues)
            except (json.JSONDecodeError, TypeError):
                leagues = [leagues] if leagues else []
        
        return EventResponse(
            id=event['id'],
            sport=event['sport'],
            date=event['date'],
            event=event['event'],
            participants=participants,
            location=event['location'],
            leagues=leagues,
            scraped_at=event['scraped_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/calendar/{year}/{month}", response_model=CalendarMonth)
async def get_calendar_month(
    year: int, 
    month: int,
    sport: Optional[str] = Query(None, description="Filter by sport"),
    db: DatabaseManager = Depends(get_db)
):
    """Get calendar view for a specific month."""
    try:
        # Validate month/year
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        if year < 2020 or year > 2030:
            raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
        
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get events for the month
        if sport:
            if sport not in COLLECTORS:
                raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
            events = db.get_events_by_sport(sport)
        else:
            events = db.get_all_events()
        
        # Filter events by month
        month_events = []
        for event in events:
            try:
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
                if start_date <= event_date <= end_date:
                    month_events.append(event)
            except ValueError:
                continue
        
        # Group events by day
        days_dict = {}
        for event in month_events:
            try:
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
                day_str = event_date.isoformat()
                
                if day_str not in days_dict:
                    days_dict[day_str] = []
                
                # Parse participants
                participants = event.get('participants', [])
                if isinstance(participants, str):
                    try:
                        participants = json.loads(participants)
                    except (json.JSONDecodeError, TypeError):
                        participants = [participants] if participants else []
                
                # Parse leagues
                leagues = event.get('leagues', [])
                if isinstance(leagues, str):
                    try:
                        leagues = json.loads(leagues)
                    except (json.JSONDecodeError, TypeError):
                        leagues = [leagues] if leagues else []
                
                event_response = EventResponse(
                    id=event['id'],
                    sport=event['sport'],
                    date=event['date'],
                    event=event['event'],
                    participants=participants,
                    location=event['location'],
                    leagues=leagues,
                    scraped_at=event['scraped_at']
                )
                days_dict[day_str].append(event_response)
            except Exception as e:
                logger.error(f"Error processing event for calendar: {e}")
                continue
        
        # Create calendar days
        calendar_days = []
        current_date = start_date
        while current_date <= end_date:
            day_str = current_date.isoformat()
            day_events = days_dict.get(day_str, [])
            
            calendar_day = CalendarDay(
                date=day_str,
                events=day_events,
                event_count=len(day_events)
            )
            calendar_days.append(calendar_day)
            current_date += timedelta(days=1)
        
        return CalendarMonth(
            year=year,
            month=month,
            days=calendar_days,
            total_events=len(month_events)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar for {year}-{month}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/collect/{sport}", response_model=CollectionResult)
async def collect_sport_data(sport: str, db: DatabaseManager = Depends(get_db)):
    """Trigger data collection for a specific sport."""
    try:
        if sport not in COLLECTORS:
            raise HTTPException(status_code=400, detail=f"Unsupported sport: {sport}")
        
        start_time = datetime.now()
        
        # Get collector and fetch data
        collector = get_collector(sport)
        raw_data = collector.fetch_raw_data()
        
        if not raw_data:
            return CollectionResult(
                sport=sport,
                success=False,
                events_collected=0,
                events_inserted=0,
                error_message="No data available from sources",
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
        
        # Parse events
        events = collector.parse_events(raw_data)
        events_collected = len(events)
        
        # Insert into database
        events_inserted = 0
        for event in events:
            try:
                db.insert_event(event)
                events_inserted += 1
            except Exception as e:
                logger.warning(f"Failed to insert event: {e}")
                continue
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return CollectionResult(
            sport=sport,
            success=True,
            events_collected=events_collected,
            events_inserted=events_inserted,
            error_message=None,
            duration_seconds=duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting data for {sport}: {e}")
        duration = (datetime.now() - start_time).total_seconds()
        return CollectionResult(
            sport=sport,
            success=False,
            events_collected=0,
            events_inserted=0,
            error_message=str(e),
            duration_seconds=duration
        )


@router.post("/backfill/{year}/{month}", response_model=List[CollectionResult])
async def backfill_month(
    year: int, 
    month: int,
    db: DatabaseManager = Depends(get_db)
):
    """Backfill data for a specific month."""
    try:
        # Validate inputs
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        if year < 2020 or year > 2030:
            raise HTTPException(status_code=400, detail="Year must be between 2020 and 2030")
        
        from collectors import COLLECTORS, get_collector
        results = []
        
        for sport in COLLECTORS.keys():
            start_time = datetime.now()
            try:
                collector = get_collector(sport)
                raw_data = collector.fetch_raw_data()
                
                if not raw_data:
                    results.append(CollectionResult(
                        sport=sport,
                        success=False,
                        events_collected=0,
                        events_inserted=0,
                        error_message="No data available from sources",
                        duration_seconds=(datetime.now() - start_time).total_seconds()
                    ))
                    continue
                
                events = collector.parse_events(raw_data)
                events_collected = len(events)
                
                # Insert into database
                events_inserted = 0
                for event in events:
                    try:
                        db.insert_event(event)
                        events_inserted += 1
                    except Exception as e:
                        logger.warning(f"Failed to insert event: {e}")
                        continue
                
                duration = (datetime.now() - start_time).total_seconds()
                
                results.append(CollectionResult(
                    sport=sport,
                    success=True,
                    events_collected=events_collected,
                    events_inserted=events_inserted,
                    error_message=None,
                    duration_seconds=duration
                ))
                
            except Exception as e:
                logger.error(f"Error collecting data for {sport}: {e}")
                duration = (datetime.now() - start_time).total_seconds()
                results.append(CollectionResult(
                    sport=sport,
                    success=False,
                    events_collected=0,
                    events_inserted=0,
                    error_message=str(e),
                    duration_seconds=duration
                ))
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during backfill for {year}-{month}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/collect", response_model=List[CollectionResult])
async def collect_all_data(db: DatabaseManager = Depends(get_db)):
    """Trigger data collection for all sports."""
    results = []
    
    for sport in COLLECTORS.keys():
        try:
            result = await collect_sport_data(sport, db)
            results.append(result)
        except Exception as e:
            logger.error(f"Error collecting data for {sport}: {e}")
            results.append(CollectionResult(
                sport=sport,
                success=False,
                events_collected=0,
                events_inserted=0,
                error_message=str(e),
                duration_seconds=0.0
            ))
    
    return results
