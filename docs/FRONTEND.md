# Frontend Documentation

This document provides comprehensive documentation for the Game Watcher frontend interface.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [User Interface](#user-interface)
- [Components](#components)
- [JavaScript API Client](#javascript-api-client)
- [Customization](#customization)
- [Development Guide](#development-guide)

## Overview

The Game Watcher frontend is a web-based interface for viewing sports schedules, events, and betting odds. It provides an intuitive calendar view with filtering and administrative capabilities.

### Technology Stack

- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 5
- **JavaScript**: Vanilla JS with Fetch API
- **Icons**: Bootstrap Icons
- **Backend**: FastAPI (REST API)

### Key Features

- 📅 Interactive calendar view (month, week, day)
- 🎯 Sport-specific filtering
- 🏷️ League/competition categorization
- 💰 Betting odds display with probability analysis
- 📊 Admin dashboard for data management
- 📱 Responsive mobile-friendly design
- 🔄 Real-time data updates

## Architecture

### File Structure

```
api/
├── templates/              # HTML templates
│   ├── calendar.html      # Main calendar view
│   ├── day.html          # Single day detail view
│   ├── admin.html        # Admin dashboard
│   └── betting_odds_component.html  # Betting odds widget
├── static/               # Static assets (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── frontend.py          # Frontend route handlers
└── app.py              # Application factory

web_server.py            # Entry point
```

### Request Flow

```
User Browser → FastAPI Frontend Routes → Template Rendering → HTML Response
                     ↓
              API Backend Routes → Database → JSON Response
```

### Separation of Concerns

The frontend is separated into distinct layers:

1. **Presentation Layer**: HTML templates (Jinja2)
2. **Route Layer**: Frontend route handlers (`frontend.py`)
3. **API Layer**: Backend API endpoints (`routes.py`)
4. **Data Layer**: Database operations (`utils/database.py`)

## User Interface

### Main Calendar View

**URL**: `http://localhost:8000/`

The main calendar displays events in a monthly grid view.

#### Features:
- **Month Navigation**: Previous/Next month buttons
- **Sport Filter**: Dropdown to filter by specific sport
- **Today Button**: Quick navigation to current date
- **Event Cards**: Click on date to see event details
- **Color Coding**: Different colors for different sports

#### Query Parameters:
- `?year=2025&month=10` - View specific month
- `?sport=futbol` - Filter by sport
- `?year=2025&month=10&sport=nfl` - Combined filters

#### Navigation:
```javascript
// Navigate to specific month
window.location.href = '/?year=2025&month=10';

// Filter by sport
window.location.href = '/?sport=futbol';

// Combined navigation
window.location.href = '/?year=2025&month=10&sport=nfl';
```

---

### Day Detail View

**URL**: `http://localhost:8000/day/{YYYY-MM-DD}`

Shows all events for a specific day with detailed information.

#### Features:
- Full event details
- Betting odds (if available)
- Watch links
- Participant information
- League/competition details

#### Example:
```
http://localhost:8000/day/2025-10-28
http://localhost:8000/day/2025-10-28?sport=futbol
```

---

### Admin Dashboard

**URL**: `http://localhost:8000/admin`

Administrative interface for data collection and management.

#### Features:
- **Data Collection**: Trigger collection for specific sports
- **Backfill**: Fill historical data for past months
- **Statistics**: View collection metrics and event counts
- **Webhooks**: Configure webhook notifications
- **System Health**: Monitor application status

#### Actions:
- Collect current month data for all sports
- Collect specific sport data
- Backfill historical months
- View database statistics
- Test webhook endpoints

---

## Components

### Calendar Component

The main calendar grid component.

**Location**: `api/templates/calendar.html`

**Features**:
- Month view with 7-day weeks
- Event count indicators
- Click-through to day view
- Current date highlighting

**Usage**:
```html
<!-- Calendar is rendered server-side with Jinja2 -->
{% for week in weeks %}
  <tr>
    {% for day in week %}
      <td class="calendar-day {% if day.is_current_month %}current-month{% endif %}">
        <div class="date">{{ day.date.day }}</div>
        <div class="events">
          {% for event in day.events %}
            <div class="event-item">{{ event.event }}</div>
          {% endfor %}
        </div>
      </td>
    {% endfor %}
  </tr>
{% endfor %}
```

---

### Betting Odds Component

Displays betting odds with probability analysis.

**Location**: `api/templates/betting_odds_component.html`

**Features**:
- Multiple bookmaker odds
- Best odds highlighting
- Implied probability calculation
- Bookmaker comparison

**Integration**:
```html
<!-- Include in event detail view -->
{% if event.betting_odds %}
  {% include 'betting_odds_component.html' %}
{% endif %}
```

**Data Format**:
```javascript
{
  "event_id": "abc123",
  "bookmakers": [
    {
      "name": "DraftKings",
      "home_odds": 1.85,
      "away_odds": 2.10
    }
  ],
  "best_odds": {
    "home": 1.90,
    "away": 2.15
  }
}
```

---

### Sport Filter Component

Dropdown for filtering events by sport.

**Usage**:
```html
<select id="sportFilter" onchange="filterBySport()">
  <option value="">All Sports</option>
  <option value="futbol">⚽ Soccer</option>
  <option value="nfl">🏈 NFL</option>
  <option value="nba">🏀 NBA</option>
  <option value="f1">🏎️ F1</option>
  <option value="boxing">🥊 Boxing</option>
  <option value="mma">🥋 MMA</option>
</select>

<script>
function filterBySport() {
  const sport = document.getElementById('sportFilter').value;
  const url = new URL(window.location);
  if (sport) {
    url.searchParams.set('sport', sport);
  } else {
    url.searchParams.delete('sport');
  }
  window.location = url;
}
</script>
```

---

### Event Card Component

Displays individual event information.

**Structure**:
```html
<div class="event-card" data-sport="futbol">
  <div class="event-header">
    <span class="sport-icon">⚽</span>
    <span class="sport-name">FUTBOL</span>
  </div>
  <div class="event-body">
    <h5 class="event-title">Arsenal vs Liverpool</h5>
    <div class="event-details">
      <div class="event-time">🕐 15:00</div>
      <div class="event-location">📍 Emirates Stadium</div>
      <div class="event-league">🏆 Premier League</div>
    </div>
  </div>
  <div class="event-footer">
    <a href="/watch" class="btn btn-primary btn-sm">Watch</a>
    <a href="/odds" class="btn btn-secondary btn-sm">Odds</a>
  </div>
</div>
```

**Styling**:
```css
.event-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  margin: 10px 0;
  transition: box-shadow 0.3s;
}

.event-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.event-card[data-sport="futbol"] {
  border-left: 4px solid #28a745;
}
```

---

## JavaScript API Client

### Fetching Events

```javascript
// Get all events
async function fetchEvents() {
  const response = await fetch('/api/v1/events');
  const data = await response.json();
  return data.events;
}

// Get events for specific sport
async function fetchSportEvents(sport) {
  const response = await fetch(`/api/v1/events?sport=${sport}`);
  const data = await response.json();
  return data.events;
}

// Get events for date range
async function fetchEventsByDateRange(startDate, endDate) {
  const response = await fetch(
    `/api/v1/events?start_date=${startDate}&end_date=${endDate}`
  );
  const data = await response.json();
  return data.events;
}
```

### Triggering Data Collection

```javascript
// Collect data for specific sport
async function collectSportData(sport) {
  const response = await fetch(`/api/v1/collect/${sport}`, {
    method: 'POST'
  });
  const result = await response.json();
  console.log(`Collected ${result.events_collected} events`);
  return result;
}

// Collect data for all sports
async function collectAllData() {
  const response = await fetch('/api/v1/collect/all', {
    method: 'POST'
  });
  const result = await response.json();
  return result;
}
```

### Fetching Betting Odds

```javascript
// Get all betting odds
async function fetchBettingOdds() {
  const response = await fetch('/api/v1/betting/odds');
  const data = await response.json();
  return data.odds;
}

// Get odds for specific event
async function fetchEventOdds(eventId) {
  const response = await fetch(`/api/v1/betting/odds/${eventId}`);
  const odds = await response.json();
  return odds;
}
```

### Error Handling

```javascript
async function fetchWithErrorHandling(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    alert(`Error: ${error.message}`);
    return null;
  }
}
```

---

## Customization

### Color Scheme

Sport colors are defined in CSS:

```css
/* Sport color scheme */
.sport-futbol { color: #28a745; }
.sport-nfl { color: #dc3545; }
.sport-nba { color: #fd7e14; }
.sport-f1 { color: #e83e8c; }
.sport-boxing { color: #6f42c1; }
.sport-mma { color: #20c997; }
```

### Adding New Sport

1. **Add sport to collectors**:
```python
# collectors/__init__.py
COLLECTORS = {
    'tennis': TennisCollector,
    # ... other sports
}
```

2. **Add sport icon**:
```javascript
// In frontend template
const sportIcons = {
  'tennis': '🎾',
  // ... other sports
};
```

3. **Add sport color**:
```css
.sport-tennis { color: #ffc107; }
```

### Customizing Templates

Templates use Jinja2 syntax:

```html
<!-- Custom header -->
{% block header %}
<header class="custom-header">
  <h1>{{ title }}</h1>
</header>
{% endblock %}

<!-- Custom content -->
{% block content %}
  {% for event in events %}
    <div class="event">{{ event.event }}</div>
  {% endfor %}
{% endblock %}
```

---

## Development Guide

### Running the Frontend

```bash
# Start the development server
python web_server.py

# Access the frontend
open http://localhost:8000
```

### Hot Reload

The server uses uvicorn with `--reload` flag for automatic reloading on file changes:

```bash
uvicorn web_server:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Pages

1. **Create template**:
```html
<!-- api/templates/new_page.html -->
{% extends "base.html" %}
{% block content %}
  <h1>New Page</h1>
{% endblock %}
```

2. **Add route**:
```python
# api/frontend.py
@frontend_router.get("/new-page", response_class=HTMLResponse)
async def new_page(request: Request):
    return templates.TemplateResponse("new_page.html", {
        "request": request,
        "title": "New Page"
    })
```

3. **Add navigation link**:
```html
<nav>
  <a href="/new-page">New Page</a>
</nav>
```

### Testing Frontend

```bash
# Run integration tests
pytest tests/test_frontend.py

# Test specific page
pytest tests/test_frontend.py::test_calendar_view
```

### Browser Testing

Use browser developer tools:

1. **Console**: Check JavaScript errors
2. **Network**: Monitor API calls
3. **Elements**: Inspect DOM structure
4. **Application**: Check local storage, cookies

### Performance Optimization

```javascript
// Debounce search input
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

const searchEvents = debounce(async (query) => {
  const events = await fetchEvents(query);
  displayEvents(events);
}, 300);
```

---

## API Integration Examples

### Complete Event Display

```javascript
// Fetch and display events
async function displayEvents() {
  const events = await fetch('/api/v1/events').then(r => r.json());
  
  const container = document.getElementById('events');
  container.innerHTML = '';
  
  events.events.forEach(event => {
    const card = createEventCard(event);
    container.appendChild(card);
  });
}

function createEventCard(event) {
  const card = document.createElement('div');
  card.className = 'event-card';
  card.innerHTML = `
    <h5>${event.event}</h5>
    <p>📅 ${new Date(event.date).toLocaleString()}</p>
    <p>📍 ${event.location}</p>
    <p>🏆 ${event.league || 'N/A'}</p>
  `;
  return card;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', displayEvents);
```

### Real-time Updates

```javascript
// Poll for new events every 5 minutes
setInterval(async () => {
  const events = await fetchEvents();
  updateEventDisplay(events);
}, 5 * 60 * 1000);
```

### Progressive Web App (PWA)

To make the app installable:

1. **Create manifest.json**:
```json
{
  "name": "Game Watcher",
  "short_name": "GameWatch",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#007bff",
  "icons": [
    {
      "src": "/static/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

2. **Add service worker** (for offline support):
```javascript
// service-worker.js
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

---

## Accessibility

### ARIA Labels

```html
<button aria-label="Navigate to previous month">
  <span aria-hidden="true">←</span>
</button>

<div role="region" aria-label="Sports calendar">
  <!-- Calendar content -->
</div>
```

### Keyboard Navigation

```javascript
// Allow keyboard navigation
document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowLeft') navigateToPrevMonth();
  if (e.key === 'ArrowRight') navigateToNextMonth();
});
```

### Screen Reader Support

```html
<table aria-label="Monthly sports calendar">
  <caption class="sr-only">October 2025 Sports Events</caption>
  <!-- Calendar table -->
</table>
```

---

## Troubleshooting

### Common Issues

**Issue**: Events not displaying
**Solution**: Check browser console for API errors, verify backend is running

**Issue**: Betting odds not showing
**Solution**: Verify `THE_ODDS_API_KEY` is configured, check API rate limits

**Issue**: Calendar navigation broken
**Solution**: Check JavaScript console for errors, verify query parameters

### Debugging Tips

```javascript
// Enable debug mode
localStorage.setItem('debug', 'true');

// Check if debug mode is enabled
if (localStorage.getItem('debug') === 'true') {
  console.log('Debug mode enabled');
}

// Log all API calls
const originalFetch = window.fetch;
window.fetch = (...args) => {
  console.log('Fetch:', args[0]);
  return originalFetch(...args);
};
```

---

**Last Updated**: 2025-10-28
**Frontend Version**: 1.0.0
