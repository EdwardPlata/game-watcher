# Sports Calendar - Daily Sports Schedule Tracker

Game Watcher is a Python-based sports scheduling platform that fetches event data from multiple sources, stores it in a local database, and presents it via a web interface and CLI tools.
Features include modular collectors, automated scheduling, and an interactive calendar UI.

## 🚀 Quick Start

### Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/EdwardPlata/game-watcher.git
cd game-watcher
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start the web application:**
```bash
python3 web_server.py
```

4. **Access the web interface:**
   - Open your browser to `http://localhost:8000`
   - View the interactive sports calendar
   - Use the admin dashboard for data management

## 🏆 Supported Sports

- ⚽ **Soccer/Futbol** - ESPN data with league categorization ✅
- 🥊 **Boxing** - BoxingScene.com events ✅
- 🏎️ **F1** - Formula 1 racing schedules ✅
- 🥋 **MMA/UFC** - Mixed martial arts events ✅
- 🏈 **NFL** - American football (planned)
- 🏀 **NBA** - Basketball (planned)

## ✨ Key Features

- **📅 Interactive Web Calendar** - Month, week, and day views
- **🎯 Sport Filtering** - View events by specific sports
- **🏷️ League Categorization** - Events organized by competitions/leagues
- **📊 Admin Dashboard** - Data collection and event management
- **🔄 Backfill Functionality** - Populate historical event data
- **🤖 Automated Collection** - Scheduled data fetching
- **📱 Responsive Design** - Mobile-friendly interface
- **🔗 Watch Links** - Direct links to stream/watch events online
- **🪝 Webhook Integration** - Real-time event notifications to frontend applications

## 📖 Documentation

Comprehensive documentation is available in the [`/docs`](./docs/) directory:

- **[Getting Started Guide](./docs/README.md)** - Complete setup and usage instructions
- **[Features Overview](./docs/FEATURES_SUMMARY.md)** - Detailed feature descriptions
- **[System Architecture](./docs/ARCHITECTURE.md)** - Technical architecture and design
- **[Implementation Status](./docs/IMPLEMENTATION_COMPLETE.md)** - Current development status
- **[Webhook Guide](./docs/WEBHOOK_GUIDE.md)** - Webhook configuration and integration

## � Project Structure

- **[docs/](./docs/)** - Documentation files
- **[api/](./api/)** - API modules
- **[collectors/](./collectors/)** - Data collectors for each sport
- **[utils/](./utils/)** - Utility modules
- **[tests/](./tests/)** - Test suites
- **[main.py](./main.py)** - CLI entry point
- **[web_server.py](./web_server.py)** - Web interface server
- **[config.env](./config.env)** - Environment configuration file

## �🔧 Usage

### Web Interface
```bash
# Start the web server
python3 web_server.py

# Access at http://localhost:8000
# - View calendar interface
# - Filter by sports and dates
# - Use admin dashboard for data management
```

### Command Line
```bash
# Fetch data for specific sport
python3 main.py fetch futbol --save

# Backfill historical data
python3 main.py backfill 2025-08 --sport f1

# View help
python3 main.py --help
```

## 🏗️ Architecture

- **FastAPI Web Framework** - Modern Python web API
- **SQLite Database** - Local data storage with migration support
- **Modular Collectors** - Sport-specific data collection modules
- **Bootstrap UI** - Responsive web interface
- **Automated Scheduling** - Background data collection

## 🤝 Contributing

1. Read the [documentation](./docs/README.md) first
2. Follow existing code patterns
3. Test thoroughly with multiple sports
4. Update documentation for new features

## 📄 License

This project is open source. See the repository for license details.

---

**Need help?** Check the [comprehensive documentation](./docs/README.md) for detailed setup instructions, feature guides, and development information.