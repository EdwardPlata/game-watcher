# Betting Odds Integration Guide

This document describes the betting odds integration feature for the Game Watcher application.

## Overview

The betting odds feature fetches real-time betting odds from multiple bookmakers and displays them alongside game information. This helps users gauge probabilities for game outcomes based on market consensus.

## Architecture

### 1. Data Collection

**The Odds API Integration**
- Uses [The Odds API](https://the-odds-api.com/) - a legitimate, free-tier API service
- No web scraping required - official API access
- Free tier: 500 requests per month
- Covers 40+ bookmakers across US and UK markets
- Supports multiple sports: NFL, NBA, Soccer, MMA, Boxing, F1

**IP Rotation Implementation**
- Built-in proxy rotation support for sites requiring scraping
- Configurable via `PROXY_LIST` environment variable
- Rate limiting and exponential backoff
- Random jitter to avoid detection patterns

### 2. Components

#### Backend Components

**`collectors/betting/collector.py`**
- `BettingOddsCollector`: Main collector class
- Fetches odds from The Odds API
- Implements IP rotation for sites requiring scraping
- Calculates best odds and implied probabilities
- Rate limiting and retry logic

**`utils/database.py`**
- New `betting_odds` table for storing odds data
- Methods: `insert_betting_odds()`, `get_odds_for_event()`, `get_all_betting_odds()`
- Automatic deduplication using event_id

**`utils/betting_scheduler.py`**
- `BettingOddsScheduler`: Background scheduler for automatic odds refresh
- Runs every 30 minutes by default (configurable)
- Webhook notifications on odds updates
- Graceful error handling

**`api/routes.py`**
- New endpoints:
  - `POST /api/v1/betting/collect` - Manually trigger odds collection
  - `GET /api/v1/betting/odds` - Get all betting odds
  - `GET /api/v1/betting/odds/{id}` - Get detailed odds for specific event
  - `GET /api/v1/events/{id}/odds` - Get odds for a specific game event

#### Frontend Components

**`api/templates/betting_odds_component.html`**
- Reusable betting odds display component
- Shows best odds for home/away/draw
- Displays implied probabilities
- Bookmaker information
- Auto-refresh functionality
- Integrated into day view

### 3. Data Flow

```
1. Scheduled Collection (every 30 min)
   └─> BettingOddsScheduler.collect_and_notify()
       └─> BettingOddsCollector.fetch_raw_data()
           └─> The Odds API
       └─> BettingOddsCollector.parse_events()
       └─> DatabaseManager.insert_betting_odds()
       └─> Webhook notifications

2. User Requests
   └─> Frontend loads event page
       └─> JavaScript: loadBettingOdds(eventId)
           └─> GET /api/v1/events/{id}/odds
               └─> DatabaseManager.get_odds_for_event()
                   └─> Display odds component
```

## Configuration

### Environment Variables

```bash
# Required: The Odds API key (free from https://the-odds-api.com/)
ODDS_API_KEY=your_api_key_here

# Optional: Proxy list for IP rotation (comma-separated)
PROXY_LIST=http://proxy1.com:8080,http://proxy2.com:8080

# Optional: Collection interval in minutes (default: 30)
BETTING_ODDS_INTERVAL=30
```

### Getting an API Key

1. Visit [https://the-odds-api.com/](https://the-odds-api.com/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 500 requests/month
5. Set `ODDS_API_KEY` environment variable

### Proxy Configuration

For sites requiring web scraping (not needed for The Odds API):

1. **Free Proxy Services** (use with caution):
   - [ProxyScrape](https://proxyscrape.com/)
   - [Free Proxy List](https://free-proxy-list.net/)

2. **Paid Proxy Services** (recommended for production):
   - [Bright Data](https://brightdata.com/)
   - [ScraperAPI](https://www.scraperapi.com/)
   - [Oxylabs](https://oxylabs.io/)

3. Configure in environment:
   ```bash
   export PROXY_LIST="http://proxy1:port,http://proxy2:port"
   ```

## Usage

### Manual Collection

Trigger manual odds collection via API:

```bash
curl -X POST http://localhost:8000/api/v1/betting/collect
```

### View Betting Odds

1. Navigate to any event in the calendar
2. Click on a day to see detailed event view
3. Betting odds automatically load for each event
4. Click "Refresh" to update odds

### API Endpoints

```python
# Get all betting odds
GET /api/v1/betting/odds?sport=nfl&limit=100

# Get detailed odds for specific entry
GET /api/v1/betting/odds/123

# Get odds for a specific event
GET /api/v1/events/456/odds
```

## Betting Odds Display

The frontend displays:

- **Best Odds**: Highest decimal odds from all bookmakers
- **Implied Probability**: Calculated as `(1 / decimal_odds) * 100`
- **Bookmaker**: Which bookmaker is offering the best odds
- **Last Updated**: When the odds were last refreshed
- **Bookmaker Count**: Number of bookmakers compared

Example display:
```
Home Team: Manchester United
  2.50 odds
  40.00% probability
  Best at: DraftKings

Draw:
  3.20 odds
  31.25% probability
  Best at: FanDuel

Away Team: Liverpool
  2.80 odds
  35.71% probability
  Best at: BetMGM
```

## Rate Limiting

To stay within The Odds API free tier (500 requests/month):

1. **Default Schedule**: Every 30 minutes
   - 48 requests/day × 30 days = 1,440 requests/month
   - Too high for free tier!

2. **Recommended Schedule**: Every 2 hours
   - 12 requests/day × 30 days = 360 requests/month
   - Safely within free tier

3. **Adjust in `api/app.py`**:
   ```python
   # Change interval_minutes from 30 to 120
   scheduler = get_betting_odds_scheduler(interval_minutes=120)
   ```

## Database Schema

### betting_odds Table

```sql
CREATE TABLE betting_odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    commence_time TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    participants TEXT NOT NULL,  -- JSON array
    odds_data TEXT NOT NULL,     -- JSON array of all odds
    best_odds TEXT NOT NULL,     -- JSON object with best odds
    bookmaker_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, sport, commence_time)
);
```

## Security Considerations

1. **API Key Protection**: Store in environment variables, never commit to code
2. **SSRF Prevention**: Webhook URL validation in place
3. **Rate Limiting**: Built-in throttling to respect API limits
4. **Proxy Safety**: Use trusted proxy providers
5. **Data Validation**: Pydantic models validate all API responses

## Troubleshooting

### Odds Not Loading

1. Check if `ODDS_API_KEY` is set:
   ```bash
   echo $ODDS_API_KEY
   ```

2. Check scheduler status:
   ```bash
   # Look for "Betting odds scheduler started" in logs
   tail -f /path/to/logs
   ```

3. Manually trigger collection:
   ```bash
   curl -X POST http://localhost:8000/api/v1/betting/collect
   ```

### API Rate Limit Exceeded

1. Check remaining requests in logs
2. Increase collection interval
3. Consider upgrading to paid tier
4. Reduce number of sports tracked

### Proxy Issues

1. Test proxy connectivity:
   ```python
   import requests
   proxies = {"http": "http://proxy:port"}
   requests.get("http://httpbin.org/ip", proxies=proxies)
   ```

2. Rotate to next proxy
3. Remove failed proxies from `PROXY_LIST`

## Future Enhancements

1. **Historical Odds Tracking**: Store odds changes over time
2. **Arbitrage Detection**: Identify arbitrage opportunities
3. **Custom Alerts**: Notify on favorable odds
4. **Multiple APIs**: Integrate additional odds providers
5. **Odds Comparison Charts**: Visualize odds across bookmakers
6. **Value Betting**: Calculate expected value
7. **Line Movement**: Track how odds change over time

## Resources

- [The Odds API Documentation](https://the-odds-api.com/liveapi/guides/v4/)
- [Betting Odds Explained](https://www.pinnacle.com/en/betting-articles/educational/betting-odds-explained)
- [Implied Probability Calculator](https://www.aceodds.com/bet-calculator/odds-converter.html)

## Support

For issues or questions:
1. Check logs in `/var/log/` or console output
2. Review API quota at [The Odds API Dashboard](https://the-odds-api.com/)
3. Test endpoints with `/docs` (Swagger UI)
