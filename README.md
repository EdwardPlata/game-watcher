# Game Watcher - Sports Schedule & Betting Odds Platform

> **A comprehensive sports scheduling and betting odds platform with automated data collection, RESTful API, and interactive web interface.**

Game Watcher is a Python-based sports scheduling platform that fetches event data from multiple sources, stores it in a local database, and presents it via a web interface and CLI tools. Features include modular collectors, automated scheduling, interactive calendar UI, and live betting odds from 40+ bookmakers.

---

## 📚 Table of Contents

### Quick Start
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [First Steps](#first-steps)

### Documentation
- **[📖 Backend API Documentation](./docs/BACKEND_API.md)** - Complete API reference and usage guide
- **[🎨 Frontend Documentation](./docs/FRONTEND.md)** - UI components and customization guide
- **[🚀 Deployment Guide](./docs/DEPLOYMENT.md)** - CI/CD setup and deployment instructions
- **[🏗️ Architecture Guide](./docs/ARCHITECTURE.md)** - System design and technical details
- **[📋 Features Overview](./docs/FEATURES_SUMMARY.md)** - Comprehensive feature descriptions
- **[🪝 Webhook Integration](./docs/WEBHOOK_GUIDE.md)** - Webhook setup and usage
- **[💰 Betting Odds Guide](./docs/BETTING_ODDS_GUIDE.md)** - Betting odds integration details

### Project Information
- [Supported Sports](#-supported-sports)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Usage Examples](#-usage-examples)
- [Technology Stack](#-technology-stack)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.12+
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/EdwardPlata/game-watcher.git
cd game-watcher
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
# Copy the example config
cp config.env .env

# Edit .env and add your API keys
# THE_ODDS_API_KEY=your-api-key-here
```

4. **Start the web application:**
```bash
python3 web_server.py
```

5. **Access the web interface:**
   - Open your browser to `http://localhost:8000`
   - View the interactive sports calendar
   - Use the admin dashboard at `http://localhost:8000/admin`

### Running the Application

```bash
# Web interface (recommended)
python3 web_server.py

# Command-line interface
python3 main.py fetch          # Fetch all sports
python3 main.py fetch futbol   # Fetch specific sport
python3 main.py month          # Fetch current month
python3 main.py show           # Show upcoming events
```

### First Steps

1. **Collect Initial Data**: Visit `/admin` and click "Collect All Sports Data"
2. **View Calendar**: Navigate to `/` to see the interactive calendar
3. **Filter Events**: Use the sport filter dropdown to view specific sports
4. **Check Betting Odds**: View odds for upcoming events (requires API key)

---

## 🏆 Supported Sports

| Sport | Status | Data Source | Betting Odds |
|-------|--------|-------------|--------------|
| ⚽ **Soccer/Futbol** | ✅ Active | ESPN API | ✅ Available |
| 🥊 **Boxing** | ✅ Active | BoxingScene.com | ✅ Available |
| 🏎️ **F1** | ✅ Active | Official F1 API | ⚠️ Limited |
| 🥋 **MMA/UFC** | ✅ Active | MMA Data API | ✅ Available |
| 🏈 **NFL** | 📋 Planned | ESPN/NFL API | ✅ Available |
| 🏀 **NBA** | 📋 Planned | ESPN/NBA API | ✅ Available |

---

## ✨ Key Features

### Data Collection & Management
- 🤖 **Automated Collection** - Scheduled data fetching with configurable intervals
- 🔄 **Backfill Functionality** - Populate historical event data for any month
- 📊 **Multi-Source Aggregation** - Combines data from multiple APIs and sources
- 🎯 **Sport-Specific Collectors** - Modular architecture for each sport

### User Interface
- 📅 **Interactive Calendar** - Month, week, and day views with intuitive navigation
- 🎨 **Responsive Design** - Mobile-friendly interface that works on all devices
- 🏷️ **Smart Filtering** - Filter by sport, date range, and league
- 🔍 **Search & Discovery** - Find events quickly with advanced search

### Betting & Odds
- 💰 **Live Betting Odds** - Real-time odds from 40+ bookmakers
- 📈 **Probability Analysis** - Implied probability calculations and comparisons
- 🎲 **Best Odds Finder** - Automatic identification of best available odds
- ⏱️ **Odds History** - Track odds changes over time

### Integration & API
- 🔌 **RESTful API** - Full-featured API for programmatic access
- 🪝 **Webhook Support** - Real-time event notifications
- 📡 **WebSocket Updates** - Live data streaming (planned)
- 🔐 **Secure Authentication** - Environment-based API key management

### Administrative Tools
- 📊 **Admin Dashboard** - Centralized data collection and management
- 📈 **Analytics & Metrics** - Collection statistics and performance monitoring
- 🔍 **Health Monitoring** - System status and error tracking
- 🛠️ **Maintenance Tools** - Database management and cleanup utilities

---

## 📖 Comprehensive Documentation

### For Developers

| Document | Description | Link |
|----------|-------------|------|
| **Backend API** | Complete API reference with endpoints, models, and examples | [📖 Read](./docs/BACKEND_API.md) |
| **Frontend Guide** | UI components, JavaScript client, and customization | [🎨 Read](./docs/FRONTEND.md) |
| **Architecture** | System design, patterns, and technical decisions | [🏗️ Read](./docs/ARCHITECTURE.md) |
| **Deployment** | CI/CD setup, Anvil deployment, and cloud hosting | [🚀 Read](./docs/DEPLOYMENT.md) |

### For Users

| Document | Description | Link |
|----------|-------------|------|
| **Getting Started** | Complete setup and first-time user guide | [📋 Read](./docs/README.md) |
| **Features** | Detailed explanation of all features | [✨ Read](./docs/FEATURES_SUMMARY.md) |
| **Webhook Guide** | Setting up real-time notifications | [🪝 Read](./docs/WEBHOOK_GUIDE.md) |
| **Betting Odds** | Using betting odds features | [💰 Read](./docs/BETTING_ODDS_GUIDE.md) |

---

## 📂 Project Structure

```
game-watcher/
├── 📁 api/                      # FastAPI application
│   ├── app.py                  # Application factory
│   ├── routes.py               # API endpoint handlers
│   ├── frontend.py             # Frontend route handlers
│   ├── models.py               # Pydantic data models
│   └── templates/              # Jinja2 HTML templates
│
├── 📁 collectors/              # Sport-specific data collectors
│   ├── futbol/                # Soccer/football collector
│   ├── nfl/                   # NFL collector
│   ├── nba/                   # NBA collector
│   ├── f1/                    # Formula 1 collector
│   ├── boxing/                # Boxing collector
│   ├── mma/                   # MMA/UFC collector
│   └── betting/               # Betting odds collector
│
├── 📁 utils/                   # Shared utilities
│   ├── database.py            # Database operations
│   ├── logger.py              # Logging utilities
│   ├── base_collector.py      # Base collector class
│   ├── monitoring.py          # Health monitoring
│   └── betting_scheduler.py   # Odds collection scheduler
│
├── 📁 tests/                   # Test suite
│   ├── test_betting_odds.py   # Betting odds tests
│   └── test_futbol.py         # Sport collector tests
│
├── 📁 docs/                    # Documentation
│   ├── BACKEND_API.md         # API documentation
│   ├── FRONTEND.md            # Frontend guide
│   ├── DEPLOYMENT.md          # Deployment guide
│   └── ...                    # Additional docs
│
├── 📁 .github/                 # GitHub configurations
│   └── workflows/             # CI/CD workflows
│       └── ci-cd.yml          # Main CI/CD pipeline
│
├── main.py                     # CLI entry point
├── web_server.py              # Web server entry point
├── requirements.txt           # Python dependencies
├── config.env                 # Configuration template
└── README.md                  # This file
```

---

## 💻 Usage Examples

### Web Interface

```bash
# Start the web server
python3 web_server.py

# Access interfaces:
# - Main calendar:     http://localhost:8000/
# - Admin dashboard:   http://localhost:8000/admin
# - API docs:          http://localhost:8000/docs
# - Health check:      http://localhost:8000/api/v1/health
```

### Command Line Interface

```bash
# Fetch all sports data
python3 main.py fetch

# Fetch specific sport
python3 main.py fetch futbol

# Fetch current month for all sports
python3 main.py month

# Backfill historical data
python3 main.py backfill --year 2025 --month 10

# Show upcoming events
python3 main.py show --days 7

# Show sport-specific events
python3 main.py show futbol --days 14

# Check application health
python3 main.py health

# Start automated scheduler
python3 main.py schedule
```

### API Usage

```bash
# Get all events
curl http://localhost:8000/api/v1/events

# Get futbol events
curl "http://localhost:8000/api/v1/events?sport=futbol"

# Trigger data collection
curl -X POST http://localhost:8000/api/v1/collect/futbol

# Get betting odds
curl http://localhost:8000/api/v1/betting/odds

# Check health
curl http://localhost:8000/api/v1/health
```

### Python API Client

```python
import requests

# Initialize client
base_url = "http://localhost:8000/api/v1"

# Get events
response = requests.get(f"{base_url}/events")
events = response.json()

# Filter by sport and date
params = {
    "sport": "futbol",
    "start_date": "2025-10-28",
    "end_date": "2025-10-31"
}
response = requests.get(f"{base_url}/events", params=params)
filtered_events = response.json()

# Trigger collection
response = requests.post(f"{base_url}/collect/all")
result = response.json()
print(f"Collected {result['total_new_events']} new events")
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI 0.104+ (Modern Python web framework)
- **Database**: SQLite with custom ORM
- **Task Scheduling**: APScheduler (Background job scheduling)
- **Data Validation**: Pydantic (Type-safe data models)
- **HTTP Client**: Requests + httpx (API communication)

### Frontend
- **Template Engine**: Jinja2 (Server-side rendering)
- **CSS Framework**: Bootstrap 5 (Responsive design)
- **JavaScript**: Vanilla JS with Fetch API
- **Icons**: Bootstrap Icons

### Development & Testing
- **Testing**: pytest with coverage reporting
- **Linting**: flake8, black, isort
- **Type Checking**: mypy
- **CI/CD**: GitHub Actions

### External APIs
- **Betting Odds**: The Odds API (40+ bookmakers)
- **Sports Data**: ESPN, BoxingScene, Official APIs
- **Calendar**: Google Calendar (optional integration)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone** the repository
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Guidelines

- 📖 **Read the documentation** in `/docs` first
- 🧪 **Write tests** for new features
- 🎨 **Follow code style** (use black, flake8, isort)
- 📝 **Update documentation** for changes
- ✅ **Run tests** before submitting: `pytest tests/`
- 🔍 **Check code quality**: `flake8 . && black --check .`

### Pull Request Process

1. Update documentation for any new features
2. Add tests that prove your fix/feature works
3. Ensure all tests pass and code is properly formatted
4. Update CHANGELOG.md with your changes
5. Submit pull request with clear description

### Adding New Sports

See [Backend API Documentation](./docs/BACKEND_API.md#adding-new-collectors) for detailed instructions on adding new sport collectors.

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include clear description, steps to reproduce, and expected behavior
- Attach logs and screenshots when applicable

---

## 📄 License

This project is open source. See the repository for license details.

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| **Documentation Hub** | [📚 /docs](./docs/) |
| **API Reference** | [📖 Backend API Docs](./docs/BACKEND_API.md) |
| **Frontend Guide** | [🎨 Frontend Docs](./docs/FRONTEND.md) |
| **Deployment** | [🚀 Deployment Guide](./docs/DEPLOYMENT.md) |
| **API Explorer** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Issue Tracker** | [GitHub Issues](https://github.com/EdwardPlata/game-watcher/issues) |
| **The Odds API** | [https://the-odds-api.com/](https://the-odds-api.com/) |

---

## 📞 Support & Contact

- **Documentation Issues**: Open an issue with the "documentation" label
- **Bug Reports**: Use GitHub Issues with detailed reproduction steps
- **Feature Requests**: Submit via GitHub Issues with "enhancement" label
- **Security Issues**: See SECURITY.md for responsible disclosure

---

## 🎯 Roadmap

### Current Version (1.0.0)
- ✅ Core sports data collection (Futbol, F1, Boxing, MMA)
- ✅ Interactive web calendar
- ✅ Betting odds integration
- ✅ RESTful API
- ✅ Admin dashboard
- ✅ CI/CD with GitHub Actions

### Planned Features
- 🔄 WebSocket support for real-time updates
- 📱 Mobile app (React Native)
- 🎮 Fantasy sports integration
- 📊 Advanced analytics dashboard
- 🔔 Custom notifications and alerts
- 🌐 Multi-language support
- ☁️ Cloud deployment templates

---

## 🏆 Acknowledgments

- **The Odds API** - Betting odds data provider
- **ESPN** - Sports event data
- **FastAPI** - Modern Python web framework
- **Bootstrap** - UI framework
- All contributors and users of this project

---

<div align="center">

**[⬆ Back to Top](#game-watcher---sports-schedule--betting-odds-platform)**

Made with ❤️ by the Game Watcher team

</div>