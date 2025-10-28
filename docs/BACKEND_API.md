# Backend API Documentation

This document provides comprehensive documentation for the Game Watcher backend API.

## Table of Contents

- [Overview](#overview)
- [API Architecture](#api-architecture)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Overview

The Game Watcher backend is built with FastAPI and provides RESTful APIs for:
- Sports event data collection
- Event retrieval and filtering
- Betting odds information
- Webhook notifications
- Health monitoring

**Base URL**: `http://localhost:8000` (development)
**API Prefix**: `/api/v1`

## API Architecture

### Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: SQLite with custom ORM
- **Data Validation**: Pydantic models
- **Authentication**: Environment-based (API keys)
- **Documentation**: OpenAPI/Swagger (auto-generated)

### Application Structure

```
api/
├── app.py              # FastAPI application factory
├── routes.py           # API route handlers
├── models.py           # Pydantic models for request/response
├── frontend.py         # Frontend route handlers (to be separated)
└── templates/          # HTML templates (frontend)
```

### Design Principles

1. **Separation of Concerns**: API logic separate from data collection
2. **RESTful Design**: Standard HTTP methods and status codes
3. **Schema Validation**: All inputs/outputs validated with Pydantic
4. **Error Handling**: Consistent error response format
5. **Documentation**: Auto-generated OpenAPI documentation

## Authentication

### Environment Variables

The API uses environment variables for authentication and configuration:

```python
# Required
THE_ODDS_API_KEY=your-odds-api-key

# Optional
DATABASE_NAME=sports_calendar.db
LOG_LEVEL=INFO
```

### Accessing from Code

```python
import os
from dotenv import load_dotenv

load_dotenv('config.env')
api_key = os.getenv('THE_ODDS_API_KEY')
```

## Endpoints

### Health Check

Check API and database health status.

```http
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-28T02:00:00Z",
  "database_connected": true,
  "total_events": 1234,
  "supported_sports": ["futbol", "nfl", "nba", "f1", "boxing", "mma"]
}
```

---

### Sports

#### List All Sports

Get list of supported sports with statistics.

```http
GET /api/v1/sports
```

**Response**:
```json
{
  "sports": [
    {
      "name": "futbol",
      "display_name": "FUTBOL",
      "description": "Futbol schedule and events",
      "total_events": 156,
      "last_updated": "2025-10-28T01:30:00Z"
    }
  ],
  "total": 6
}
```

---

### Events

#### Get Events

Retrieve events with optional filtering.

```http
GET /api/v1/events?sport={sport}&start_date={date}&end_date={date}&limit={limit}
```

**Query Parameters**:
- `sport` (optional): Filter by sport (futbol, nfl, nba, f1, boxing, mma)
- `start_date` (optional): Start date (YYYY-MM-DD format)
- `end_date` (optional): End date (YYYY-MM-DD format)
- `limit` (optional): Maximum events to return (1-1000, default: 100)

**Response**:
```json
{
  "events": [
    {
      "id": 1,
      "sport": "futbol",
      "event": "Premier League: Arsenal vs Liverpool",
      "date": "2025-10-28T15:00:00Z",
      "location": "Emirates Stadium",
      "league": "Premier League",
      "participants": ["Arsenal", "Liverpool"],
      "watch_link": "https://...",
      "scraped_at": "2025-10-27T10:00:00Z"
    }
  ],
  "total": 1,
  "filters": {
    "sport": "futbol",
    "start_date": "2025-10-28",
    "end_date": "2025-10-29"
  }
}
```

#### Get Event by ID

Retrieve a specific event by ID.

```http
GET /api/v1/events/{event_id}
```

**Response**:
```json
{
  "id": 1,
  "sport": "futbol",
  "event": "Premier League: Arsenal vs Liverpool",
  "date": "2025-10-28T15:00:00Z",
  "location": "Emirates Stadium",
  "league": "Premier League",
  "participants": ["Arsenal", "Liverpool"],
  "watch_link": "https://...",
  "scraped_at": "2025-10-27T10:00:00Z"
}
```

---

### Data Collection

#### Collect Sport Data

Trigger data collection for a specific sport.

```http
POST /api/v1/collect/{sport}
```

**Path Parameters**:
- `sport`: Sport to collect (futbol, nfl, nba, f1, boxing, mma)

**Response**:
```json
{
  "sport": "futbol",
  "events_collected": 42,
  "new_events": 5,
  "updated_events": 2,
  "duration_seconds": 3.45,
  "timestamp": "2025-10-28T02:00:00Z"
}
```

#### Collect All Sports

Trigger data collection for all supported sports.

```http
POST /api/v1/collect/all
```

**Response**:
```json
{
  "results": {
    "futbol": {"events_collected": 42, "new_events": 5},
    "nfl": {"events_collected": 28, "new_events": 3},
    "nba": {"events_collected": 35, "new_events": 7}
  },
  "total_events_collected": 105,
  "total_new_events": 15,
  "duration_seconds": 12.34,
  "timestamp": "2025-10-28T02:00:00Z"
}
```

---

### Betting Odds

#### Get All Betting Odds

Retrieve all betting odds data.

```http
GET /api/v1/betting/odds
```

**Response**:
```json
{
  "odds": [
    {
      "id": 1,
      "sport_key": "americanfootball_nfl",
      "event_id": "abc123",
      "home_team": "Kansas City Chiefs",
      "away_team": "Buffalo Bills",
      "commence_time": "2025-10-28T20:00:00Z",
      "bookmakers_count": 15,
      "best_home_odds": 1.85,
      "best_away_odds": 2.10,
      "best_draw_odds": null,
      "fetched_at": "2025-10-28T01:00:00Z"
    }
  ],
  "total": 1
}
```

#### Get Odds for Event

Get betting odds for a specific event.

```http
GET /api/v1/betting/odds/{event_id}
```

**Response**:
```json
{
  "event_id": "abc123",
  "sport_key": "americanfootball_nfl",
  "home_team": "Kansas City Chiefs",
  "away_team": "Buffalo Bills",
  "commence_time": "2025-10-28T20:00:00Z",
  "bookmakers": [
    {
      "name": "DraftKings",
      "home_odds": 1.85,
      "away_odds": 2.10,
      "draw_odds": null
    }
  ],
  "best_odds": {
    "home": 1.90,
    "away": 2.15,
    "draw": null
  },
  "fetched_at": "2025-10-28T01:00:00Z"
}
```

---

### Calendar

#### Get Calendar Month

Get calendar view data for a specific month.

```http
GET /api/v1/calendar/{year}/{month}?sport={sport}
```

**Path Parameters**:
- `year`: Year (YYYY)
- `month`: Month (1-12)

**Query Parameters**:
- `sport` (optional): Filter by sport

**Response**:
```json
{
  "year": 2025,
  "month": 10,
  "month_name": "October",
  "days": [
    {
      "date": "2025-10-01",
      "events": [
        {
          "id": 1,
          "sport": "futbol",
          "event": "Arsenal vs Liverpool",
          "time": "15:00"
        }
      ],
      "event_count": 1
    }
  ]
}
```

---

### Webhooks

#### Register Webhook

Register a webhook URL for event notifications.

```http
POST /api/v1/webhooks/register
```

**Request Body**:
```json
{
  "url": "https://your-app.com/webhook",
  "sports": ["futbol", "nfl"],
  "event_types": ["new_event", "odds_update"]
}
```

**Response**:
```json
{
  "webhook_id": "wh_abc123",
  "url": "https://your-app.com/webhook",
  "sports": ["futbol", "nfl"],
  "event_types": ["new_event", "odds_update"],
  "status": "active",
  "created_at": "2025-10-28T02:00:00Z"
}
```

#### Test Webhook

Send a test notification to a webhook.

```http
POST /api/v1/webhooks/test
```

**Request Body**:
```json
{
  "url": "https://your-app.com/webhook"
}
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "response_time_ms": 145,
  "message": "Webhook test successful"
}
```

---

## Data Models

### Event Model

```python
class Event(BaseModel):
    id: int
    sport: str
    event: str
    date: str  # ISO 8601 format
    location: str
    league: Optional[str]
    participants: List[str]
    watch_link: Optional[str]
    scraped_at: str  # ISO 8601 format
```

### BettingOdds Model

```python
class BettingOdds(BaseModel):
    id: int
    sport_key: str
    event_id: str
    home_team: str
    away_team: str
    commence_time: str  # ISO 8601 format
    bookmakers_count: int
    best_home_odds: float
    best_away_odds: float
    best_draw_odds: Optional[float]
    fetched_at: str  # ISO 8601 format
```

### CollectionResult Model

```python
class CollectionResult(BaseModel):
    sport: str
    events_collected: int
    new_events: int
    updated_events: int
    duration_seconds: float
    timestamp: str  # ISO 8601 format
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "timestamp": "2025-10-28T02:00:00Z"
}
```

### Common Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: External service unavailable

### Example Error Responses

**Invalid sport parameter**:
```json
{
  "detail": "Unsupported sport: invalid_sport",
  "status_code": 400
}
```

**Event not found**:
```json
{
  "detail": "Event with id 999 not found",
  "status_code": 404
}
```

## Rate Limiting

The API implements rate limiting for external API calls:

- **Betting Odds API**: 500 requests/month (free tier)
- **Collection Interval**: Configurable (default: 120 minutes)
- **Request Delay**: 1 second between requests

### Configuration

```python
# In config.env
API_RATE_LIMIT_DELAY=1.0
BETTING_ODDS_INTERVAL=120
```

## Interactive Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- Browse all available endpoints
- View request/response schemas
- Test endpoints directly in the browser
- Download OpenAPI specification

## Code Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get all events
response = requests.get(f"{BASE_URL}/events")
events = response.json()

# Get futbol events
response = requests.get(f"{BASE_URL}/events?sport=futbol")
futbol_events = response.json()

# Trigger data collection
response = requests.post(f"{BASE_URL}/collect/futbol")
result = response.json()
print(f"Collected {result['events_collected']} events")
```

### JavaScript Client

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Get all events
fetch(`${BASE_URL}/events`)
  .then(response => response.json())
  .then(data => console.log(data.events));

// Get futbol events
fetch(`${BASE_URL}/events?sport=futbol`)
  .then(response => response.json())
  .then(data => console.log(data.events));

// Trigger data collection
fetch(`${BASE_URL}/collect/futbol`, { method: 'POST' })
  .then(response => response.json())
  .then(result => console.log(`Collected ${result.events_collected} events`));
```

### cURL Examples

```bash
# Get health status
curl http://localhost:8000/api/v1/health

# Get all sports
curl http://localhost:8000/api/v1/sports

# Get events for specific sport
curl "http://localhost:8000/api/v1/events?sport=futbol&limit=10"

# Trigger data collection
curl -X POST http://localhost:8000/api/v1/collect/futbol

# Get betting odds
curl http://localhost:8000/api/v1/betting/odds
```

## Best Practices

1. **Always validate input**: Use query parameters for filtering
2. **Handle errors gracefully**: Check status codes and handle errors
3. **Respect rate limits**: Don't exceed API rate limits
4. **Use pagination**: Use limit parameter for large datasets
5. **Cache responses**: Cache event data to reduce API calls
6. **Monitor health**: Regularly check /health endpoint
7. **Use environment variables**: Never hardcode API keys

## Development

### Running the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python web_server.py

# Or with uvicorn directly
uvicorn web_server:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

### Adding New Endpoints

1. Define Pydantic models in `api/models.py`
2. Add route handler in `api/routes.py`
3. Add tests in `tests/`
4. Update this documentation

---

**Last Updated**: 2025-10-28
**API Version**: 1.0.0
