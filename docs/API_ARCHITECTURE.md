# API Architecture - Backend & Frontend Decoupling

This document describes the improved API architecture with clear separation between backend and frontend concerns.

## Table of Contents

- [Overview](#overview)
- [Architecture Layers](#architecture-layers)
- [Service Layer](#service-layer)
- [API Client](#api-client)
- [Data Flow](#data-flow)
- [Decoupling Benefits](#decoupling-benefits)
- [Migration Guide](#migration-guide)

## Overview

The Game Watcher API now features a clean three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  (HTML Templates, JavaScript, CSS)                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  API Service Layer                          │
│  (Business Logic, Data Transformation)                      │
│  - EventsService                                            │
│  - CollectionService                                        │
│  - BettingOddsService                                       │
│  - SportsService                                            │
│  - HealthService                                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                         │
│  (Database Operations, Data Collectors)                     │
│  - DatabaseManager                                          │
│  - Sport Collectors                                         │
└─────────────────────────────────────────────────────────────┘
```

## Architecture Layers

### 1. Presentation Layer (Frontend)

**Location**: `api/frontend.py`, `api/templates/`

**Responsibilities**:
- Render HTML templates
- Handle user interactions
- Display data to users
- Client-side validation

**Key Files**:
- `api/frontend.py` - Frontend route handlers
- `api/templates/*.html` - Jinja2 templates
- `api/static/` - CSS, JavaScript, images

### 2. API Layer (Routes)

**Location**: `api/routes.py`

**Responsibilities**:
- Define API endpoints
- Handle HTTP requests/responses
- Input validation
- Error handling
- Response formatting

**Key Endpoints**:
- `/api/v1/health` - Health check
- `/api/v1/events` - Event management
- `/api/v1/collect/{sport}` - Data collection
- `/api/v1/betting/odds` - Betting odds

### 3. Service Layer (Business Logic)

**Location**: `api/services.py`

**Responsibilities**:
- Business logic implementation
- Data transformation
- Coordination between components
- Reusable operations

**Services**:
- `EventsService` - Event operations
- `CollectionService` - Data collection
- `BettingOddsService` - Betting odds
- `SportsService` - Sports information
- `HealthService` - Health monitoring

### 4. Data Access Layer

**Location**: `utils/database.py`, `collectors/`

**Responsibilities**:
- Database operations
- External API calls
- Data persistence
- Raw data collection

## Service Layer

The service layer provides a clean abstraction between the API routes and data access:

### EventsService

Handles all event-related operations:

```python
from api.services import get_events_service

# Get service instance
events_service = get_events_service()

# Get all events
events = events_service.get_all_events()

# Get events by sport
futbol_events = events_service.get_events_by_sport('futbol')

# Get events for specific date
from datetime import date
today_events = events_service.get_events_for_day(date.today())

# Group events by date
events_by_date = events_service.group_events_by_date(events)

# Normalize event data
normalized = events_service.normalize_event(raw_event)
```

### CollectionService

Manages data collection operations:

```python
from api.services import get_collection_service

collection_service = get_collection_service()

# Collect specific sport
result = collection_service.collect_sport_data('futbol')
print(f"Collected {result['events_collected']} events")

# Collect all sports
results = collection_service.collect_all_sports()
print(f"Total new events: {results['total_new_events']}")
```

### BettingOddsService

Handles betting odds operations:

```python
from api.services import get_betting_odds_service

odds_service = get_betting_odds_service()

# Get all odds
all_odds = odds_service.get_all_odds()

# Get odds for specific event
event_odds = odds_service.get_odds_for_event('event_123')

# Collect new odds
result = odds_service.collect_betting_odds()
```

### SportsService

Provides sports information:

```python
from api.services import get_sports_service

sports_service = get_sports_service()

# Get all sports with statistics
sports = sports_service.get_all_sports()

# Get list of supported sports
sport_names = sports_service.get_supported_sports_list()
```

### HealthService

Monitors application health:

```python
from api.services import get_health_service

health_service = get_health_service()

# Get health status
status = health_service.get_health_status()

# Get database statistics
stats = health_service.get_database_statistics()
```

## API Client

The API client provides a convenient way for external applications to interact with the API:

### Basic Usage

```python
from api.client import GameWatcherClient

# Create client
client = GameWatcherClient(base_url="http://localhost:8000")

# Get events
events = client.get_events(sport="futbol")

# Trigger collection
result = client.collect_sport_data("futbol")

# Get betting odds
odds = client.get_betting_odds()
```

### Advanced Usage

```python
from api.client import GameWatcherClient, get_upcoming_events

client = GameWatcherClient()

# Get upcoming events for next 7 days
upcoming = get_upcoming_events(client, sport="nfl", days=7)

# Get calendar for specific month
calendar_data = client.get_calendar_month(2025, 10, sport="futbol")

# Register webhook
webhook = client.register_webhook(
    url="https://your-app.com/webhook",
    sports=["futbol", "nfl"],
    event_types=["new_event", "odds_update"]
)
```

### Error Handling

```python
from api.client import GameWatcherClient, APIError

client = GameWatcherClient()

try:
    events = client.get_events(sport="invalid_sport")
except APIError as e:
    print(f"API Error: {e}")
```

## Data Flow

### Example: Fetching Events

```
User Request
    │
    ▼
Frontend Route (/api/v1/events)
    │
    ▼
Route Handler (routes.py)
    │ - Validate input
    │ - Parse parameters
    │
    ▼
EventsService (services.py)
    │ - Business logic
    │ - Data transformation
    │
    ▼
DatabaseManager (database.py)
    │ - SQL queries
    │ - Data retrieval
    │
    ▼
Response to User
```

### Example: Data Collection

```
User Triggers Collection
    │
    ▼
API Route (/api/v1/collect/futbol)
    │
    ▼
CollectionService (services.py)
    │ - Get collector
    │ - Coordinate collection
    │
    ▼
Sport Collector (collectors/futbol/)
    │ - Fetch from external API
    │ - Parse data
    │
    ▼
DatabaseManager (database.py)
    │ - Insert/update events
    │
    ▼
Response with Statistics
```

## Decoupling Benefits

### 1. Independent Development

- Frontend can be developed/tested separately
- Backend changes don't affect frontend
- Easier to add new features

### 2. Reusability

- Services can be used by multiple routes
- API client can be used by external apps
- Business logic is centralized

### 3. Testability

- Each layer can be tested independently
- Mock services for testing routes
- Mock database for testing services

### 4. Scalability

- Can split into microservices
- Can deploy frontend separately
- Can scale components independently

### 5. Maintainability

- Clear separation of concerns
- Easier to understand and modify
- Better code organization

## Migration Guide

### From Direct Database Access to Services

**Before**:
```python
@router.get("/events")
async def get_events(db: DatabaseManager = Depends(get_db)):
    events = db.get_all_events()
    return {"events": events}
```

**After**:
```python
from api.services import get_events_service

@router.get("/events")
async def get_events(db: DatabaseManager = Depends(get_db)):
    events_service = get_events_service(db)
    events = events_service.get_all_events()
    normalized = [events_service.normalize_event(e) for e in events]
    return {"events": normalized}
```

### From Frontend to API Client

**Before** (Direct template rendering with database):
```python
@app.get("/calendar")
async def calendar_view(db: DatabaseManager = Depends(get_db)):
    events = db.get_all_events()
    return templates.TemplateResponse("calendar.html", {
        "events": events
    })
```

**After** (Using API client):
```javascript
// Frontend JavaScript
fetch('/api/v1/events')
    .then(response => response.json())
    .then(data => {
        displayEvents(data.events);
    });
```

### Creating a Standalone Frontend

1. **Use API Client**:
```python
from api.client import GameWatcherClient

client = GameWatcherClient(base_url="http://api.game-watcher.com")
events = client.get_events()
```

2. **Build with Frontend Framework**:
```javascript
// React, Vue, Angular, etc.
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

async function fetchEvents() {
    const response = await axios.get(`${API_BASE}/events`);
    return response.data.events;
}
```

3. **Deploy Separately**:
- Frontend: Static hosting (Netlify, Vercel, S3)
- Backend: Application hosting (Heroku, Railway, AWS)

## Best Practices

### 1. Always Use Services in Routes

```python
# Good
@router.get("/events")
async def get_events(db: DatabaseManager = Depends(get_db)):
    service = get_events_service(db)
    return service.get_all_events()

# Avoid
@router.get("/events")
async def get_events(db: DatabaseManager = Depends(get_db)):
    return db.get_all_events()  # Skip service layer
```

### 2. Keep Routes Thin

Routes should only handle HTTP concerns:
- Input validation
- Calling services
- Formatting responses
- Error handling

### 3. Centralize Business Logic

Business logic belongs in services, not routes:

```python
# Good
class EventsService:
    def get_upcoming_events(self, days: int):
        events = self.get_all_events()
        # Business logic here
        return filtered_events

# Avoid putting business logic in routes
```

### 4. Use Type Hints

```python
def get_events_by_sport(
    self,
    sport: str,
    limit: int = 1000
) -> List[Dict[str, Any]]:
    """Get events for specific sport."""
    pass
```

### 5. Handle Errors Gracefully

```python
try:
    result = service.collect_sport_data(sport)
    return result
except Exception as e:
    logger.error(f"Collection failed: {e}")
    return {"success": False, "error": str(e)}
```

## Future Enhancements

### Planned Improvements

1. **GraphQL API**: Add GraphQL endpoint for flexible queries
2. **WebSocket Support**: Real-time event updates
3. **API Versioning**: Better version management (v1, v2, etc.)
4. **Rate Limiting**: Per-client rate limits
5. **Authentication**: API key or OAuth2 authentication
6. **Caching**: Redis cache for frequently accessed data
7. **Message Queue**: Async processing with Celery/RabbitMQ

### Microservices Migration

Future architecture could split into:
- **Events Service**: Event management
- **Collection Service**: Data collection
- **Odds Service**: Betting odds
- **Notification Service**: Webhooks and alerts
- **API Gateway**: Route requests to services

---

**Last Updated**: 2025-10-28
**Version**: 2.0.0
