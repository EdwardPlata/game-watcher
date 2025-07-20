# Sports Calendar Documentation

Welcome to the Sports Calendar application documentation. This directory contains comprehensive information about the system architecture, features, and implementation details.

## 📖 Documentation Overview

### Essential Reading (Start Here)

1. **[FEATURES_SUMMARY.md](./FEATURES_SUMMARY.md)** - Overview of all application features and capabilities
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture and component design
3. **[IMPLEMENTATION_COMPLETE.md](./IMPLEMENTATION_COMPLETE.md)** - Implementation status and completed features

### Development History

4. **[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)** - Code refactoring history and improvements

## 🚀 Quick Start Guide

### For End Users
- The application provides a web-based sports calendar interface
- Access the calendar at `http://localhost:8000` when running
- View events by sport, date, and league/competition
- Use backfill functionality to populate historical data

### For Developers
- Read **ARCHITECTURE.md** first to understand the system design
- Check **IMPLEMENTATION_COMPLETE.md** for current feature status
- Review **FEATURES_SUMMARY.md** for detailed feature descriptions

## 🏗️ System Components

The Sports Calendar application consists of:

### Core Components
- **Web API** (`/api/`) - FastAPI-based REST API and web interface
- **Data Collectors** (`/collectors/`) - Sport-specific data collection modules
- **Database** (`/utils/database.py`) - SQLite database management
- **Utilities** (`/utils/`) - Shared utilities and base classes

### Supported Sports
- ⚽ **Futbol (Soccer)** - ESPN data source with league categorization
- 🥊 **Boxing** - BoxingScene.com data source
- 🏎️ **F1** - Formula 1 race schedules
- 🥋 **MMA/UFC** - Mixed martial arts events
- 🏈 **NFL** - American football (future implementation)
- 🏀 **NBA** - Basketball (future implementation)

## 📋 Key Features

### Web Interface
- **Interactive Calendar** - Month/week/day views with event filtering
- **Admin Dashboard** - Event management and data collection controls
- **Sport Filtering** - View events by specific sports
- **League Badges** - Visual categorization of events by leagues/competitions
- **Backfill Functionality** - Populate historical event data

### Data Management
- **Automated Collection** - Scheduled data fetching from various sources
- **Duplicate Detection** - Smart duplicate event filtering
- **Database Migration** - Automatic schema updates
- **Event Standardization** - Consistent event format across all sports

### API Endpoints
- **RESTful API** - Full CRUD operations for events
- **Calendar Views** - Month, week, and day-specific event endpoints
- **Sport-specific** - Dedicated endpoints for each sport type
- **Admin Functions** - Data collection and management endpoints

## 🔧 Configuration

### Environment Setup
- Copy `config.env.example` to `config.env`
- Configure database settings and logging preferences
- Set up sport-specific API keys if required

### Database
- SQLite database with automatic migration support
- Event schema includes: sport, date, event name, participants, location, leagues
- Indexes for efficient querying by date and sport

## 🛠️ Development

### Adding New Sports
1. Create collector in `/collectors/{sport}/`
2. Implement `BaseDataCollector` interface
3. Add sport to collector registry
4. Update web interface for new sport filtering

### Extending Features
- Review existing architecture in **ARCHITECTURE.md**
- Follow established patterns for consistency
- Update documentation when adding major features

## 📊 Monitoring & Logging

- Application logs stored in `sports_calendar.log`
- Health monitoring for data collection processes
- Error tracking and recovery mechanisms
- Performance metrics for data collection efficiency

## 🤝 Contributing

1. Read the architecture documentation first
2. Follow existing code patterns and conventions
3. Update documentation for any new features
4. Test thoroughly with multiple data sources

## 📞 Support

For technical issues or questions:
1. Check the relevant documentation files
2. Review application logs for error details
3. Examine collector-specific implementations
4. Consider data source availability and rate limiting

---

*Last updated: July 2025*
