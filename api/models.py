"""
Pydantic models for API request/response validation.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    """Model for creating a new event."""
    sport: str = Field(..., description="Sport name")
    date: str = Field(..., description="Event date in ISO format")
    event: str = Field(..., description="Event name or description")
    participants: List[str] = Field(default_factory=list, description="List of participants")
    location: str = Field(..., description="Event location")
    leagues: List[str] = Field(default_factory=list, description="List of leagues/tags")
    watch_link: Optional[str] = Field(None, description="Link to watch event online")


class EventResponse(BaseModel):
    """Model for event response."""
    id: int
    sport: str
    date: str
    event: str
    participants: List[str]
    location: str
    leagues: List[str]
    watch_link: Optional[str] = None
    scraped_at: str
    
    class Config:
        from_attributes = True


class EventsResponse(BaseModel):
    """Model for multiple events response."""
    events: List[EventResponse]
    total: int
    sport: Optional[str] = None
    date_range: Optional[str] = None


class SportInfo(BaseModel):
    """Model for sport information."""
    name: str
    display_name: str
    description: str
    total_events: int
    last_updated: Optional[str] = None


class SportsResponse(BaseModel):
    """Model for sports list response."""
    sports: List[SportInfo]
    total: int


class CalendarDay(BaseModel):
    """Model for calendar day view."""
    date: str
    events: List[EventResponse]
    event_count: int


class CalendarMonth(BaseModel):
    """Model for calendar month view."""
    year: int
    month: int
    days: List[CalendarDay]
    total_events: int


class HealthStatus(BaseModel):
    """Model for health check response."""
    status: str
    timestamp: str
    database_connected: bool
    total_events: int
    supported_sports: List[str]


class CollectionResult(BaseModel):
    """Model for data collection result."""
    sport: str
    success: bool
    events_collected: int
    events_inserted: int
    error_message: Optional[str] = None
    duration_seconds: float


class WebhookConfig(BaseModel):
    """Model for webhook configuration."""
    id: Optional[int] = None
    name: str
    url: str
    enabled: bool = True


class WebhookPayload(BaseModel):
    """Model for webhook payload sent to frontend."""
    event_type: str = Field(..., description="Type of event: 'new_events'")
    timestamp: str = Field(..., description="ISO timestamp of webhook")
    events: List[EventResponse] = Field(..., description="List of new events")
    total: int = Field(..., description="Total number of events in payload")


class BettingOddsOutcome(BaseModel):
    """Model for betting odds outcome."""
    name: str = Field(..., description="Outcome name (team name or 'Draw')")
    price: float = Field(..., description="Decimal odds")
    point: Optional[float] = Field(None, description="Point spread or total (if applicable)")


class BettingOddsMarket(BaseModel):
    """Model for betting market odds."""
    bookmaker: str = Field(..., description="Bookmaker name")
    market: str = Field(..., description="Market type (h2h, spreads, totals)")
    outcomes: List[BettingOddsOutcome] = Field(..., description="List of outcomes with odds")


class BestOdds(BaseModel):
    """Model for best available odds."""
    price: float = Field(0, description="Best decimal odds")
    bookmaker: Optional[str] = Field(None, description="Bookmaker offering best odds")
    probability: float = Field(0, description="Implied probability percentage")


class BettingOddsResponse(BaseModel):
    """Model for betting odds response."""
    id: Optional[int] = None
    event_id: str
    sport: str
    commence_time: str
    home_team: str
    away_team: str
    participants: List[str]
    best_odds: dict = Field(..., description="Best available odds for each outcome")
    bookmaker_count: int = Field(..., description="Number of bookmakers offering odds")
    scraped_at: str
    
    class Config:
        from_attributes = True


class BettingOddsDetailResponse(BaseModel):
    """Model for detailed betting odds response."""
    id: Optional[int] = None
    event_id: str
    sport: str
    commence_time: str
    home_team: str
    away_team: str
    participants: List[str]
    odds_data: List[dict] = Field(..., description="Complete odds data from all bookmakers")
    best_odds: dict = Field(..., description="Best available odds for each outcome")
    bookmaker_count: int = Field(..., description="Number of bookmakers offering odds")
    scraped_at: str
    
    class Config:
        from_attributes = True

