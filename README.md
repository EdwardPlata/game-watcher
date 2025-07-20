# Game Watcher - Daily Sports Calendar App

A comprehensive sports schedule tracking application with API integration, database storage, and calendar synchronization capabilities. Enhanced with MCP (Model Context Protocol) server integration for advanced development workflows.

## Overview

Game Watcher is a Python-based application that fetches and stores daily schedules for multiple sports including Football/Soccer, NFL, NBA, F1, Boxing, and MMA/UFC. The application features automated data collection, local storage, and optional Google Calendar integration.

## Sports Supported

- 🏎️ **F1** - Formula 1 racing (via Ergast API) ✅ *Implemented*
- ⚽ **Fútbol/Soccer** - International and domestic leagues ⏳ *Planned*
- 🏈 **NFL** - National Football League ⏳ *Planned*
- 🏀 **NBA** - National Basketball Association ⏳ *Planned*
- 🥊 **Boxing** - Professional boxing events ⏳ *Planned*
- 🥋 **MMA/UFC** - Mixed martial arts events ⏳ *Planned*

## Features

### Core Functionality
- **Multi-sport data fetching** from various APIs and web sources
- **SQLite database storage** with automatic duplicate prevention
- **Scheduled daily updates** at 2:00 AM local time
- **CLI interface** for manual operations and queries
- **Modular architecture** for easy sport-specific implementations

### MCP Integration
- 🤖 **AI-powered development** with GitHub Copilot integration
- 📁 **Advanced file operations** via filesystem server
- 🔧 **Git repository management** for version control
- 🌐 **Web content fetching** for data sources
- 🧠 **Persistent memory** for development context
- ⏰ **Time zone management** for global sports scheduling

### Optional Features
- **Google Calendar sync** for personal scheduling integration
- **Event notifications** and reminders
- **Data export** capabilities

## Quick Start

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/EdwardPlata/game-watcher.git
cd game-watcher
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Test the F1 implementation:**
```bash
python test_app.py
```

### Basic Usage

```bash
# Fetch all sports data and store in database
python app.py fetch

# Show upcoming F1 events for the next 7 days
python app.py show f1

# Show all sports events for the next 30 days
python app.py show --days 30

# Start the daily scheduler (runs continuously)
python app.py schedule

# Sync new events to Google Calendar (when configured)
python app.py sync
```

## Configuration

### Environment Variables

Copy `config.env` to `.env` and configure your API keys:

```bash
cp config.env .env
# Edit .env with your actual API keys
```

### Required API Keys (Optional)
- **API-Football**: For soccer/football data
- **SportsDataIO**: For NFL, NBA data
- **RapidAPI**: For various sports APIs
- **Google Calendar**: For calendar synchronization

### MCP Servers

The project includes pre-configured MCP servers in `.vscode/mcp.json`:
- **GitHub** - Repository and issue management
- **Filesystem** - File operations
- **Git** - Version control operations
- **Fetch** - Web content retrieval
- **Memory** - Persistent knowledge storage
- **Time** - Timezone conversions

## Architecture

### Data Flow
```
APIs/Web Sources → SportsFetcher → DatabaseManager → SQLite DB
                     ↓
               CalendarSync → Google Calendar (optional)
```

### Key Components

#### `SportsFetcher` Class
- **Modular design** with sport-specific `fetch_*()` and `parse_*()` methods
- **Error handling** and retry logic
- **Rate limiting** for API compliance
- **Standardized event schema**

#### `DatabaseManager` Class  
- **SQLite operations** with automatic schema creation
- **Duplicate prevention** using composite keys
- **Efficient querying** with indexed searches
- **Data retention** management

#### Event Schema
```python
{
    "sport": "f1",
    "date": "2025-07-20T18:00:00Z",
    "event": "F1 Monaco Grand Prix",
    "participants": ["F1 Drivers"],
    "location": "Circuit de Monaco, Monaco"
}
```

## Implementation Status

### ✅ Completed
- **F1 Integration** - Full Ergast API implementation
- **Database layer** - SQLite with proper indexing
- **CLI interface** - All basic commands functional
- **Scheduler** - APScheduler integration
- **Testing framework** - Comprehensive test suite

### 🚧 In Progress
- **Error handling** improvements
- **Logging** enhancements
- **Configuration** management

### ⏳ Planned
- **NFL API** integration (SportsDataIO)
- **NBA API** integration (NBA/SportsDataIO)
- **Soccer API** integration (API-Football)
- **Boxing** web scraping (ESPN/BoxingScene)
- **MMA/UFC** API integration (RapidAPI)
- **Google Calendar** OAuth2 implementation
- **Web dashboard** interface
- **Mobile notifications**

## Development with MCP

This project is enhanced with MCP servers for development productivity:

### Using VS Code
1. Open the project in VS Code
2. MCP servers auto-load from `.vscode/mcp.json`
3. AI assistance has enhanced capabilities for:
   - File operations
   - Git management
   - API documentation lookup
   - Code generation and debugging

### Available MCP Tools
- **100+ GitHub operations** - Issues, PRs, workflows
- **13 filesystem tools** - Read, write, search files
- **12 git operations** - Status, commit, branch management
- **Web fetching** - API documentation and examples
- **Memory management** - Context preservation across sessions

## Contributing

### Adding New Sports

1. **Implement fetcher method:**
```python
def fetch_newsport(self) -> List[Dict]:
    # API calls or web scraping
    return self.parse_newsport(raw_data)
```

2. **Implement parser method:**
```python
def parse_newsport(self, raw_data) -> List[Dict]:
    # Convert to standardized event schema
    return events
```

3. **Add to supported sports list:**
```python
self.supported_sports = ['f1', 'futbol', 'nfl', 'nba', 'boxing', 'mma', 'newsport']
```

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-sport`)
3. Implement and test new functionality
4. Run test suite (`python test_app.py`)
5. Submit pull request

## Testing

```bash
# Run full test suite
python test_app.py

# Test specific components
python -c "from app import SportsFetcher; print(SportsFetcher().fetch_f1())"

# Database tests
python -c "from app import DatabaseManager; db = DatabaseManager('test.db')"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **[Ergast API](http://ergast.com/mrd/)** - F1 data source
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Development enhancement
- **APScheduler** - Task scheduling
- **Requests** - HTTP client library

## API Data Sources

| Sport | Primary Source | Backup Source | Status |
|-------|---------------|---------------|--------|
| F1 | Ergast API | ESPN Scraping | ✅ Active |
| Soccer | API-Football | ESPN Scraping | ⏳ Planned |
| NFL | SportsDataIO | ESPN API | ⏳ Planned |
| NBA | NBA API | SportsDataIO | ⏳ Planned |
| Boxing | BoxingScene | ESPN Scraping | ⏳ Planned |
| MMA/UFC | RapidAPI | UFC.com Scraping | ⏳ Planned |