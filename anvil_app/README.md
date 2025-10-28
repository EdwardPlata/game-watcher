# Game Watcher - Anvil Adaptation

## Overview
This directory contains the Anvil adaptation of the Game Watcher application. The original FastAPI-based web application has been converted to run on Anvil's Python web hosting platform, maintaining all core functionality while leveraging Anvil's integrated hosting environment.

## Files in This Directory

- `server_module.py` - Main Anvil server functions (converted from FastAPI routes)
- `background_tasks.py` - Background task definitions for periodic data collection
- `collector_utils.py` - Utility functions for testing and managing collectors
- `requirements.txt` - Anvil-specific dependency list

## Key Architectural Changes

### 1. Server Architecture
**Before (FastAPI):**
- FastAPI web framework with uvicorn server
- RESTful API endpoints with HTTP methods
- Automatic API documentation with Swagger/OpenAPI

**After (Anvil):**
- Anvil server callable functions with `@anvil.server.callable`
- Direct Python function calls from client to server
- No HTTP routing - functions called by name

### 2. Database Layer
**Before (SQLite):**
- SQLite database with custom DatabaseManager class
- Raw SQL queries and cursor operations
- Manual schema management and migrations

**After (Anvil Data Tables):**
- Anvil's hosted Data Tables service
- Object-oriented table operations with `app_tables`
- Visual schema management through Anvil editor

### 3. Background Processing
**Before (APScheduler):**
- APScheduler with cron-like scheduling
- Persistent scheduler running in background
- Complex job management and persistence

**After (Anvil Background Tasks):**
- `@anvil.server.background_task` decorators
- Manual triggering or client-side timers
- Simpler task launching with `launch_background_task()`

### 4. Frontend/UI
**Before (FastAPI + Jinja2):**
- HTML templates with Jinja2 templating
- Bootstrap CSS for styling
- Static file serving for assets
- Form handling with FastAPI

**After (Anvil UI):**
- Drag-and-drop visual form designer
- Python-based client code (no HTML/CSS)
- Built-in Material Design components
- Event-driven programming model

## Deployment Guide

### Prerequisites

1. **Anvil Account**: Sign up at [anvil.works](https://anvil.works)
2. **Plan**: Free tier works for development, paid plans for production
3. **Python Knowledge**: Anvil uses Python for both client and server code

### Step 1: Create New Anvil App

1. Log in to Anvil
2. Click "Create New App"
3. Choose "Blank App" 
4. Select "Material Design" theme (recommended)
5. Name your app: "Game Watcher"

### Step 2: Set Up Data Tables

#### Create the Events Table
1. Go to the "Data Tables" section in Anvil
2. Create a new table named "events"
3. Add the following columns:

| Column Name | Type | Description |
|-------------|------|-------------|
| sport | Text | Sport name (futbol, nfl, nba, etc.) |
| date | Date and Time | Event date and time |
| event | Text | Event description |
| participants | Text | JSON array of participants/teams |
| location | Text | Event location |
| leagues | Text | JSON array of leagues/categories |
| watch_link | Text | Link to watch the event |
| created_at | Date and Time | Record creation time |
| scraped_at | Date and Time | Data collection time |
| synced_to_calendar | Simple Value | Boolean for calendar sync status |

#### Create the Betting Odds Table
1. Create a new table named "betting_odds"
2. Add the following columns:

| Column Name | Type | Description |
|-------------|------|-------------|
| event_id | Link to events table | Reference to event |
| bookmaker | Text | Bookmaker name |
| market_type | Text | Type of bet (h2h, spreads, totals) |
| odds_data | Text | JSON data with odds information |
| inserted_at | Date and Time | When odds were collected |

### Step 3: Install Dependencies

1. Go to "Settings" → "Python Package Manager"
2. Install the packages listed in `requirements.txt`:

```
requests
beautifulsoup4
lxml
python-dateutil
pytz
pydantic
jsonschema
python-dotenv
ratelimit
httpx
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

**Note**: Do NOT install FastAPI, uvicorn, APScheduler, or other web framework dependencies.

### Step 4: Upload Server Code

#### Copy Existing Collectors
1. In Anvil, go to "Server Code"
2. Create a new server module called "collectors_base"
3. Copy the contents of your existing collector files:
   - `utils/base_collector.py`
   - `utils/event_schema.py`
   - `utils/logger.py`
   - Individual collector files from `collectors/` directory

#### Upload Anvil Server Modules
1. Create a new server module called "server_functions"
2. Copy the contents of `server_module.py`
3. Create another server module called "background_tasks"
4. Copy the contents of `background_tasks.py`
5. Create a server module called "collector_utils"
6. Copy the contents of `collector_utils.py`

### Step 5: Configure Environment Variables

1. Go to "Settings" → "Secrets"
2. Add the following environment variables:

```
ODDS_API_KEY=your_odds_api_key_here
API_FOOTBALL_KEY=your_api_football_key_here (optional)
RAPIDAPI_KEY=your_rapidapi_key_here (optional)
```

Access these in your code with:
```python
import anvil.secrets
api_key = anvil.secrets.get_secret("ODDS_API_KEY")
```

### Step 6: Create the User Interface

#### Main Form (Calendar View)
1. Create a new form called "MainForm"
2. Add components:
   - **ColumnPanel** for layout
   - **Label** for title: "Sports Calendar"
   - **DatePicker** for navigation
   - **RepeatingPanel** for displaying events
   - **Button** for "Refresh Data"

#### Admin Dashboard Form
1. Create a form called "AdminForm"
2. Add components:
   - **Label** for title: "Admin Dashboard"
   - **Button** for "Collect All Sports Data"
   - **Button** for "Collect Betting Odds"
   - **RichText** for displaying results
   - **DataGrid** for viewing recent events

#### Sample Main Form Code
```python
from ._anvil_designer import MainFormTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
from datetime import datetime, timedelta

class MainForm(MainFormTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self.load_today_events()
    
    def load_today_events(self):
        """Load events for today."""
        today = datetime.now().date()
        year, month, day = today.year, today.month, today.day
        
        try:
            day_data = anvil.server.call('get_calendar_day', year, month, day)
            self.display_events(day_data['events'])
        except Exception as e:
            alert(f"Error loading events: {e}")
    
    def display_events(self, events):
        """Display events in the repeating panel."""
        self.events_panel.items = events
    
    def refresh_button_click(self, **event_args):
        """Refresh data when button is clicked."""
        try:
            result = anvil.server.call('collect_all_sports_data')
            alert(f"Data refreshed! {result['total_events_inserted']} new events added.")
            self.load_today_events()
        except Exception as e:
            alert(f"Error refreshing data: {e}")
```

### Step 7: Set Up Background Tasks

#### Option 1: Manual Triggers
Create admin functions to manually trigger data collection:

```python
def admin_collect_data_click(self, **event_args):
    """Manually trigger data collection."""
    try:
        task = anvil.server.launch_background_task('scheduled_data_collection')
        alert(f"Data collection started. Task ID: {task.get_id()}")
    except Exception as e:
        alert(f"Error starting collection: {e}")
```

#### Option 2: Client-Side Timer
Use a timer to periodically collect data:

```python
from anvil import Timer

class MainForm(MainFormTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        # Set up timer for periodic collection (every 6 hours)
        self.collection_timer = Timer(interval=6*60*60)  # 6 hours in seconds
        self.collection_timer.tick = self.auto_collect_data
        self.collection_timer.enabled = True
    
    def auto_collect_data(self, **event_args):
        """Automatically collect data periodically."""
        try:
            anvil.server.launch_background_task('scheduled_data_collection')
        except Exception as e:
            print(f"Auto-collection error: {e}")
```

### Step 8: Test the Application

#### Test Server Functions
1. Go to "Server Code" in Anvil
2. Test individual functions:

```python
# Test health check
result = health_check()
print(result)

# Test sports list
sports = get_sports()
print(sports)

# Test data collection
result = collect_sport_data('futbol')
print(result)
```

#### Test Collectors
```python
# Test collector functionality
result = test_all_collectors()
print(result)

# Validate dependencies
deps = validate_collector_dependencies()
print(deps)
```

### Step 9: Deploy the Application

1. Click "Publish this app" in the top menu
2. Choose your publishing environment:
   - **Development**: For testing
   - **Production**: For live use
3. Set up a custom domain (paid plans only)
4. Configure any additional settings

### Step 10: Post-Deployment Configuration

#### Set Up Monitoring
1. Create a monitoring dashboard form
2. Add functions to check:
   - Number of events in database
   - Last collection time
   - Background task status
   - API rate limits

#### Schedule Regular Collections
Choose one of these approaches:

**Option A: External Cron Job**
Set up a cron job to call your Anvil HTTP endpoints:
```bash
# Collect data every 6 hours
0 */6 * * * curl -X POST "https://your-app.anvil.app/_/api/collect_data"
```

**Option B: Client-Side Scheduling**
Keep a client browser tab open with automated collection.

**Option C: Uplink Script**
Run a Python script with Anvil Uplink on your server:
```python
import anvil.server
import time
import schedule

anvil.server.connect("YOUR_UPLINK_KEY")

def collect_data():
    anvil.server.call('collect_all_sports_data')

schedule.every(6).hours.do(collect_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Compatibility Information

### What Works Unchanged
- **Data Collectors**: All existing sport collectors can be used as-is
- **Business Logic**: Core event collection and processing logic unchanged
- **Data Validation**: Event schema validation works the same
- **API Integration**: External API calls (ESPN, Odds API, etc.) work normally

### What Required Adaptation
- **Database Operations**: SQLite queries → Anvil Data Tables API
- **HTTP Routing**: FastAPI routes → callable server functions
- **Scheduling**: APScheduler → Background tasks + client timers
- **Response Models**: Pydantic models → plain Python dictionaries
- **Error Handling**: HTTP exceptions → AnvilWrappedError

### What's Not Available in Anvil
- **Selenium**: Web drivers may not work in Anvil's environment
- **Complex Scheduling**: No built-in cron-like functionality
- **File System Access**: Limited compared to traditional hosting
- **Direct HTTP Endpoints**: No REST API unless specifically configured

## Limitations and Considerations

### Anvil Limitations
- **Request Timeout**: Long-running requests may timeout
- **Dependency Restrictions**: Some Python packages may not be available
- **Selenium**: Web drivers may not work in Anvil's environment
- **Background Tasks**: Limited scheduling compared to APScheduler

### Recommended Adaptations
1. **Break Large Collections**: Split data collection into smaller chunks
2. **Error Handling**: Robust error handling for network issues
3. **Rate Limiting**: Respect API limits more carefully in shared environment
4. **Caching**: Cache frequently accessed data to reduce API calls

## Benefits of Anvil Adaptation

### Advantages
- **No Server Management**: Anvil handles hosting infrastructure
- **Built-in Database**: No need to manage SQLite files
- **Rapid UI Development**: Drag-and-drop interface builder
- **Python Everywhere**: No HTML/CSS/JavaScript required
- **Integrated Environment**: Everything in one platform
- **Automatic Scaling**: Anvil handles traffic scaling

### Potential Limitations
- **Vendor Lock-in**: Application tied to Anvil platform
- **Limited Customization**: UI limited to Anvil components
- **Dependency Restrictions**: Some Python packages may not work
- **Cost**: May be more expensive than self-hosting for high traffic
- **Scheduling Limitations**: Less flexible than APScheduler

## Troubleshooting

### Common Issues

**1. Import Errors**
```
Solution: Ensure all required packages are installed in Package Manager
Check that relative imports work correctly in Anvil's structure
```

**2. Database Connection Issues**
```
Solution: Verify Data Tables are created with correct column names and types
Check that table permissions allow server code access
```

**3. Background Task Failures**
```
Solution: Add comprehensive error handling and logging
Test functions individually before running as background tasks
```

**4. API Rate Limits**
```
Solution: Implement exponential backoff
Cache results when possible
Use environment variables for API keys
```

### Testing Checklist
- [ ] All server functions callable from client
- [ ] Data Tables properly configured
- [ ] Environment variables set correctly
- [ ] Dependencies installed
- [ ] Background tasks working
- [ ] UI displays data correctly
- [ ] Error handling functional

## Migration Checklist

### From Original FastAPI App
- [ ] Server functions created and tested
- [ ] Data Tables schema matches SQLite structure
- [ ] All collectors working in Anvil environment
- [ ] Background tasks replace APScheduler
- [ ] UI created to replace web templates
- [ ] Environment variables configured
- [ ] Deployment tested
- [ ] Monitoring set up

## Testing Strategy

### Pre-Deployment Testing
1. **Function Testing**: Test each server function individually
2. **Collector Testing**: Use `test_all_collectors()` to verify data collection
3. **Database Testing**: Verify Data Table operations work correctly
4. **Dependency Testing**: Use `validate_collector_dependencies()`

### Post-Deployment Testing
1. **End-to-End Testing**: Test full data collection → storage → display flow
2. **UI Testing**: Verify all forms and components work
3. **Background Task Testing**: Test periodic data collection
4. **Error Handling**: Verify graceful error handling

## Support and Resources

- **Anvil Documentation**: https://anvil.works/docs
- **Anvil Community Forum**: https://anvil.works/forum
- **Game Watcher GitHub**: https://github.com/EdwardPlata/game-watcher

## Conclusion

The Game Watcher application has been successfully adapted for Anvil deployment. The core functionality remains intact while leveraging Anvil's strengths in hosting, database management, and UI development. The adaptation maintains the original application's sports data collection capabilities while simplifying deployment and infrastructure management.

Key benefits include easier deployment, no server management, and a more integrated development environment. The main trade-offs are some loss of flexibility in scheduling and potential vendor lock-in to the Anvil platform.

The provided code and documentation should enable a smooth transition from the original FastAPI application to a fully functional Anvil-hosted version.