"""
Frontend routes for serving HTML pages.
"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import calendar
import os

from utils import DatabaseManager
from .routes import get_db

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(template_dir):
    os.makedirs(template_dir)

templates = Jinja2Templates(directory=template_dir)
frontend_router = APIRouter()


@frontend_router.get("/", response_class=HTMLResponse)
async def calendar_view(
    request: Request,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    sport: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db)
):
    """Main calendar view."""
    # Default to current month if not specified
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    # Validate inputs
    if month < 1 or month > 12:
        month = datetime.now().month
    if year < 2020 or year > 2030:
        year = datetime.now().year
    
    try:
        # Get calendar data
        cal = calendar.Calendar(firstweekday=6)  # Start week on Sunday
        month_days = list(cal.itermonthdates(year, month))
        
        # Get events for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Fetch events from database
        if sport:
            events = db.get_events_by_sport(sport)
        else:
            events = db.get_all_events()
        
        # Group events by date
        events_by_date = {}
        for event in events:
            try:
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
                if start_date <= event_date < end_date:
                    date_str = event_date.isoformat()
                    if date_str not in events_by_date:
                        events_by_date[date_str] = []
                    events_by_date[date_str].append(event)
            except ValueError:
                continue
        
        # Create calendar weeks
        weeks = []
        week = []
        for day in month_days:
            day_events = events_by_date.get(day.isoformat(), [])
            week.append({
                'date': day,
                'is_current_month': day.month == month,
                'events': day_events,
                'event_count': len(day_events)
            })
            
            if len(week) == 7:
                weeks.append(week)
                week = []
        
        # Navigation
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        # Sports list for filter
        from collectors import COLLECTORS
        sports_list = list(COLLECTORS.keys())
        
        return templates.TemplateResponse("calendar.html", {
            "request": request,
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "weeks": weeks,
            "events_by_date": events_by_date,
            "current_sport": sport,
            "sports_list": sports_list,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "current_date": datetime.now().date()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading calendar: {e}")


@frontend_router.get("/day/{date_str}", response_class=HTMLResponse)
async def day_view(
    request: Request,
    date_str: str,
    sport: Optional[str] = Query(None),
    db: DatabaseManager = Depends(get_db)
):
    """Detailed view for a specific day."""
    try:
        # Parse date
        try:
            view_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
        
        # Get events for the day
        if sport:
            events = db.get_events_by_sport(sport)
        else:
            events = db.get_all_events()
        
        # Filter events for the specific day
        day_events = []
        for event in events:
            try:
                event_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00')).date()
                if event_date == view_date:
                    day_events.append(event)
            except ValueError:
                continue
        
        # Sort events by time
        day_events.sort(key=lambda x: x.get('date', ''))
        
        # Sports list for filter
        from collectors import COLLECTORS
        sports_list = list(COLLECTORS.keys())
        
        return templates.TemplateResponse("day.html", {
            "request": request,
            "view_date": view_date,
            "date_str": date_str,
            "events": day_events,
            "current_sport": sport,
            "sports_list": sports_list,
            "formatted_date": view_date.strftime("%A, %B %d, %Y")
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading day view: {e}")


@frontend_router.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request, db: DatabaseManager = Depends(get_db)):
    """Admin dashboard for data collection."""
    try:
        # Get statistics
        total_events = db.get_event_count()
        
        # Get events by sport
        from collectors import COLLECTORS
        sport_stats = []
        for sport in COLLECTORS.keys():
            events = db.get_events_by_sport(sport)
            sport_stats.append({
                'name': sport,
                'display_name': sport.upper(),
                'event_count': len(events),
                'last_updated': max([e.get('scraped_at', '') for e in events]) if events else None
            })
        
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "total_events": total_events,
            "sport_stats": sport_stats,
            "sports_list": list(COLLECTORS.keys())
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading admin dashboard: {e}")
