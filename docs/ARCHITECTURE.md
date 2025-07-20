# Sports Calendar App - Refactored Architecture

This document describes the refactored architecture of the Daily Sports Calendar App.

## Directory Structure

```
game-watcher/
├── collectors/                 # Sport-specific data collectors
│   ├── __init__.py            # Collector registry and factory
│   ├── f1/                    # Formula 1 collector
│   │   ├── __init__.py
│   │   └── collector.py       # F1-specific implementation
│   ├── futbol/                # Soccer/Football collector
│   │   ├── __init__.py
│   │   └── collector.py       # Soccer-specific implementation
│   ├── nfl/                   # NFL collector
│   │   ├── __init__.py
│   │   └── collector.py       # NFL-specific implementation
│   ├── nba/                   # NBA collector
│   │   ├── __init__.py
│   │   └── collector.py       # NBA-specific implementation
│   ├── boxing/                # Boxing collector
│   │   ├── __init__.py
│   │   └── collector.py       # Boxing-specific implementation
│   └── mma/                   # MMA/UFC collector
│       ├── __init__.py
│       └── collector.py       # MMA-specific implementation
├── utils/                     # Shared utilities and base classes
│   ├── __init__.py           # Utils package exports
│   ├── base_collector.py     # Base class for all collectors
│   ├── database.py           # Database management
│   ├── logger.py             # Logging utilities
│   ├── event_schema.py       # Event validation and schema
│   ├── calendar_sync.py      # Google Calendar integration
│   └── monitoring.py         # Health monitoring and metrics
├── main.py                   # New main application (replaces app.py)
├── app.py                    # Original monolithic app (can be removed)
└── requirements.txt          # Python dependencies
```

## Architecture Overview

### 1. Base Collector Pattern

All sport-specific collectors inherit from `BaseDataCollector` which provides:
- Common HTTP request handling
- Standardized error handling and logging
- Event validation
- Consistent interface across all sports

### 2. Modular Sport Collectors

Each sport has its own directory containing:
- `__init__.py`: Package exports
- `collector.py`: Sport-specific implementation

Benefits:
- Clear separation of concerns
- Easy to add new sports
- Independent development and testing
- Specific API handling per sport

### 3. Shared Utilities

The `utils` package contains:
- **Database Management**: Centralized database operations
- **Logging**: Consistent logging across the application
- **Monitoring**: Health checks and metrics collection
- **Event Schema**: Validation and standardization
- **Calendar Sync**: Google Calendar integration

### 4. Monitoring and Health Checks

The new architecture includes comprehensive monitoring:
- Fetch success/failure tracking
- Performance metrics
- Health status per sport
- Error categorization and counting

## Usage

### Run with the new architecture:

```bash
# Fetch all sports
python main.py fetch

# Fetch specific sport
python main.py fetch f1

# Show upcoming events
python main.py show

# Show F1 events for next 14 days
python main.py show f1 --days 14

# Check application health
python main.py health

# Sync to Google Calendar
python main.py sync

# Start scheduler
python main.py schedule
```

## Adding a New Sport

To add a new sport collector:

1. Create a new directory under `collectors/`
2. Implement the collector class inheriting from `BaseDataCollector`
3. Implement `fetch_raw_data()` and `parse_events()` methods
4. Add the collector to the registry in `collectors/__init__.py`

Example:

```python
# collectors/tennis/collector.py
from utils.base_collector import BaseDataCollector
from utils.event_schema import create_event

class TennisCollector(BaseDataCollector):
    def __init__(self):
        super().__init__("tennis")
    
    def fetch_raw_data(self):
        # Implement API call
        pass
    
    def parse_events(self, raw_data):
        # Parse and return standardized events
        pass
```

## Benefits of the Refactored Architecture

1. **Modularity**: Each sport is independent
2. **Maintainability**: Clear separation of concerns
3. **Extensibility**: Easy to add new sports
4. **Monitoring**: Built-in health checks and metrics
5. **Reliability**: Better error handling and logging
6. **Testing**: Each component can be tested independently
7. **Best Practices**: Follows Python packaging conventions

## Migration Notes

- The original `app.py` can be removed after testing
- All functionality is preserved in the new structure
- The CLI interface remains the same (use `main.py` instead of `app.py`)
- Database schema and data remain unchanged
