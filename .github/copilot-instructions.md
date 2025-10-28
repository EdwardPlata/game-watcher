# Game Watcher - AI Coding Agent Instructions

## Project Overview
Game Watcher is a multi-sport event tracking and betting odds aggregation platform built with FastAPI, SQLite, and modular sport collectors. It combines web scraping, official APIs, and real-time data collection to provide comprehensive sports schedule and betting odds data.

## Architecture Patterns

### Collector Pattern Implementation
- **Base Class**: All sport collectors inherit from `utils.base_collector.BaseDataCollector`
- **Registration**: Collectors are registered in `collectors/__init__.py` COLLECTORS dict
- **Factory**: Use `get_collector(sport)` to instantiate collectors
- **Standard Methods**: Each collector implements `fetch_raw_data()` and `parse_events()`

Example collector structure:
```python
class FutbolCollector(BaseDataCollector):
    def __init__(self):
        super().__init__("futbol")
    
    def fetch_raw_data(self) -> Any:
        # Sport-specific API/scraping logic
    
    def parse_events(self, raw_data: Any) -> List[Dict]:
        # Convert to standardized event format
```

### Database Schema & Event Format
- **Events Table**: `sport`, `date`, `event`, `participants` (JSON array), `location`, `leagues` (JSON array), `watch_link`
- **Betting Odds Table**: Linked to events via `event_id`, stores odds from multiple bookmakers
- **Event Validation**: All events pass through `utils.event_schema.validate_event()`
- **Standard Format**: Use `utils.event_schema.create_event()` for consistent event creation

### API Structure
- **Web Server**: `web_server.py` launches FastAPI app via `api.create_app()`
- **Routes**: API endpoints in `api/routes.py`, frontend routes in `api/frontend.py`  
- **Models**: Pydantic models in `api/models.py` for request/response validation
- **Templates**: Jinja2 templates in `api/templates/` for web interface

## Key Workflows

### Adding New Sports
1. Create collector directory: `collectors/{sport}/`
2. Implement collector class inheriting from `BaseDataCollector`
3. Register in `collectors/__init__.py` COLLECTORS dict
4. Add sport mapping to betting collector if odds are available
5. Test with: `python main.py fetch {sport}`

### Development Commands
```bash
# Start web server (primary interface)
python web_server.py

# CLI operations
python main.py fetch                    # Collect all sports
python main.py fetch {sport}           # Collect specific sport  
python main.py show                    # View upcoming events
python main.py health                  # Check system status

# Testing
pytest tests/                          # Run test suite
python -m pytest tests/test_{sport}.py # Test specific collector
```

### Database Operations
- **Manager**: `utils.database.DatabaseManager` handles all DB operations
- **Insert Events**: `db.insert_events(events)` auto-deduplicates
- **Retrieve**: `db.get_events_by_sport(sport)`, `db.get_events_by_date_range()`
- **Betting Odds**: `db.insert_betting_odds()`, `db.get_betting_odds_for_event()`

## Integration Points

### Betting Odds System
- **Collector**: `collectors.betting.BettingOddsCollector` uses The Odds API
- **Scheduler**: `utils.betting_scheduler.BettingOddsScheduler` runs automated collection
- **API Key**: Set `ODDS_API_KEY` in environment (500 free requests/month)
- **Sport Mapping**: Each sport maps to The Odds API sport key in betting collector

### External APIs & Scraping
- **ESPN**: Used by futbol collector (web scraping with BeautifulSoup)
- **The Odds API**: Official betting odds API (no scraping needed)
- **F1 API**: Official Formula 1 API integration
- **Rate Limiting**: Implemented in base collector with delays and error handling

### Frontend Components
- **Calendar View**: Interactive month/day calendar at `/`
- **Admin Dashboard**: Data collection controls at `/admin`
- **API Explorer**: FastAPI auto-docs at `/docs`
- **Real-time Updates**: WebSocket integration planned for live odds

## Configuration & Environment

### Required Environment Variables
```bash
# Core
DATABASE_NAME=sports_calendar.db

# Betting Odds (recommended)
ODDS_API_KEY=your_key_here

# Optional for enhanced data collection
API_FOOTBALL_KEY=your_key_here
RAPIDAPI_KEY=your_key_here
```

### Project Structure Conventions
- `collectors/{sport}/collector.py` - Sport-specific data collection
- `utils/` - Shared utilities (database, logging, base classes)
- `api/` - FastAPI application (routes, models, templates)
- `tests/test_{sport}.py` - Collector-specific tests
- `docs/` - Comprehensive documentation

## Development Guidelines

### Error Handling
- Use logger from `utils.logger.get_logger(__name__)` 
- Collectors should return empty list `[]` on failure, not raise exceptions
- Database operations use transactions and handle constraint violations gracefully

### Data Standards
- All events must pass `validate_event()` before database insertion
- Dates in ISO format: `2024-01-01T15:30:00`
- Participants as JSON array: `["Team A", "Team B"]`
- Leagues as JSON array: `["Premier League", "Soccer"]`

### Testing Patterns
- Mock external API calls in tests
- Test both successful data collection and error conditions
- Validate event format compliance
- Use `conftest.py` for shared test fixtures

## Troubleshooting

### MCP Server Issues
- **uvx not found**: Run `scripts/mcp-diagnostic.sh` to diagnose PATH issues
- **System-wide installation**: uvx/uv symlinks in `/usr/local/bin/` for VS Code extension host
- **Restart required**: VS Code reload needed after uvx installation
- **Configuration**: MCP servers configured in `.vscode/settings.json`