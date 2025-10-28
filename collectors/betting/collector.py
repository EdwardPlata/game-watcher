"""
Betting odds collector implementation.

This collector fetches betting odds from The Odds API (https://the-odds-api.com/)
which provides free tier access to betting odds from multiple bookmakers.

The Odds API is free for non-commercial use and provides:
- Sports betting odds from 40+ bookmakers
- Multiple sports coverage (NFL, NBA, MLB, Soccer, etc.)
- Free tier: 500 requests per month
- No scraping needed - official API
"""

import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import random

from utils.base_collector import BaseDataCollector
from utils.logger import get_logger

logger = get_logger(__name__)


class BettingOddsCollector(BaseDataCollector):
    """
    Collector for betting odds data using The Odds API.
    
    The Odds API provides free access to betting odds data without requiring
    web scraping. This is a legitimate API service designed for this purpose.
    """
    
    def __init__(self):
        super().__init__("betting_odds")
        
        # The Odds API configuration
        self.api_key = os.getenv('ODDS_API_KEY', '')
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Supported sports mapping
        self.sport_mapping = {
            'futbol': 'soccer_epl',  # English Premier League
            'nfl': 'americanfootball_nfl',
            'nba': 'basketball_nba',
            'mma': 'mma_mixed_martial_arts',
            'boxing': 'boxing_boxing',
            'f1': 'motorsport_racing'  # Note: F1 may not be available
        }
        
        # IP rotation configuration (for sites that require scraping)
        self.proxy_list = self._load_proxy_list()
        self.current_proxy_index = 0
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2  # seconds between requests
    
    def _load_proxy_list(self) -> List[str]:
        """
        Load proxy list from environment or configuration.
        
        For production, you would configure proxies through:
        - Environment variables (PROXY_LIST)
        - External proxy service (e.g., Bright Data, ScraperAPI)
        - Free proxy services (with caution)
        
        Returns:
            List of proxy URLs
        """
        proxy_env = os.getenv('PROXY_LIST', '')
        if proxy_env:
            return [p.strip() for p in proxy_env.split(',') if p.strip()]
        return []
    
    def _get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        Get next proxy from rotation list.
        
        Returns:
            Proxy configuration dict or None
        """
        if not self.proxy_list:
            return None
        
        proxy_url = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            # Add small random jitter to avoid patterns
            sleep_time += random.uniform(0, 0.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any] = None, 
                     use_proxy: bool = False) -> Optional[requests.Response]:
        """
        Make HTTP request with optional proxy rotation and rate limiting.
        
        Args:
            url: URL to request
            params: Query parameters
            use_proxy: Whether to use proxy rotation
        
        Returns:
            Response object or None on failure
        """
        self._rate_limit()
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        proxies = None
        if use_proxy:
            proxies = self._get_next_proxy()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=15
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f"Request failed with status {response.status_code}")
                    if attempt < max_retries - 1 and use_proxy:
                        # Try next proxy
                        proxies = self._get_next_proxy()
                        continue
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    if use_proxy:
                        proxies = self._get_next_proxy()
                    continue
                return None
        
        return None
    
    def fetch_raw_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch betting odds from The Odds API.
        
        Returns:
            Dictionary containing odds data for various sports
        """
        if not self.api_key:
            logger.warning("ODDS_API_KEY not configured. Betting odds collection disabled.")
            logger.info("To enable: Get free API key from https://the-odds-api.com/")
            return None
        
        all_odds = {}
        
        for sport_name, api_sport_key in self.sport_mapping.items():
            try:
                logger.info(f"Fetching odds for {sport_name} ({api_sport_key})")
                
                # Get upcoming events with odds
                url = f"{self.base_url}/sports/{api_sport_key}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'us,uk',  # US and UK bookmakers
                    'markets': 'h2h,spreads,totals',  # Head-to-head, spreads, totals
                    'oddsFormat': 'decimal',
                    'dateFormat': 'iso'
                }
                
                response = self._make_request(url, params=params)
                
                if response and response.status_code == 200:
                    odds_data = response.json()
                    all_odds[sport_name] = odds_data
                    logger.info(f"Retrieved odds for {len(odds_data)} {sport_name} events")
                    
                    # Check remaining quota
                    remaining = response.headers.get('x-requests-remaining')
                    if remaining:
                        logger.info(f"API requests remaining: {remaining}")
                else:
                    logger.warning(f"Failed to fetch odds for {sport_name}")
                
            except Exception as e:
                logger.error(f"Error fetching odds for {sport_name}: {e}")
                continue
        
        return all_odds if all_odds else None
    
    def parse_events(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse betting odds data into standardized format.
        
        Args:
            raw_data: Raw odds data from API
        
        Returns:
            List of parsed odds events
        """
        if not raw_data:
            return []
        
        parsed_odds = []
        
        for sport_name, sport_odds in raw_data.items():
            if not sport_odds:
                continue
            
            for event in sport_odds:
                try:
                    odds_entry = self._parse_single_event(event, sport_name)
                    if odds_entry:
                        parsed_odds.append(odds_entry)
                except Exception as e:
                    logger.error(f"Error parsing odds event: {e}")
                    continue
        
        logger.info(f"Parsed {len(parsed_odds)} betting odds entries")
        return parsed_odds
    
    def _parse_single_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single betting odds event.
        
        Args:
            event: Raw event data from API
            sport: Sport name
        
        Returns:
            Parsed odds entry
        """
        try:
            # Extract basic event info
            event_id = event.get('id', '')
            commence_time = event.get('commence_time', '')
            home_team = event.get('home_team', '')
            away_team = event.get('away_team', '')
            
            # Extract bookmaker odds
            bookmakers = event.get('bookmakers', [])
            odds_data = []
            
            for bookmaker in bookmakers:
                bookmaker_name = bookmaker.get('title', '')
                markets = bookmaker.get('markets', [])
                
                for market in markets:
                    market_key = market.get('key', '')
                    outcomes = market.get('outcomes', [])
                    
                    market_odds = {
                        'bookmaker': bookmaker_name,
                        'market': market_key,
                        'outcomes': []
                    }
                    
                    for outcome in outcomes:
                        market_odds['outcomes'].append({
                            'name': outcome.get('name', ''),
                            'price': outcome.get('price', 0),
                            'point': outcome.get('point')  # For spreads/totals
                        })
                    
                    odds_data.append(market_odds)
            
            # Calculate implied probabilities and best odds
            best_odds = self._calculate_best_odds(odds_data, home_team, away_team)
            
            return {
                'event_id': event_id,
                'sport': sport,
                'commence_time': commence_time,
                'home_team': home_team,
                'away_team': away_team,
                'participants': [home_team, away_team],
                'odds_data': odds_data,
                'best_odds': best_odds,
                'bookmaker_count': len(bookmakers),
                'scraped_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing single event: {e}")
            return None
    
    def _calculate_best_odds(self, odds_data: List[Dict[str, Any]], 
                            home_team: str, away_team: str) -> Dict[str, Any]:
        """
        Calculate best available odds and implied probabilities.
        
        Args:
            odds_data: List of odds from various bookmakers
            home_team: Home team name
            away_team: Away team name
        
        Returns:
            Dictionary with best odds and probabilities
        """
        best_odds = {
            'home': {'price': 0, 'bookmaker': None, 'probability': 0},
            'away': {'price': 0, 'bookmaker': None, 'probability': 0},
            'draw': {'price': 0, 'bookmaker': None, 'probability': 0}
        }
        
        for odds in odds_data:
            if odds['market'] != 'h2h':  # Focus on head-to-head for now
                continue
            
            bookmaker = odds['bookmaker']
            
            for outcome in odds['outcomes']:
                name = outcome['name']
                price = outcome['price']
                
                # Decimal odds to implied probability: probability = 1 / decimal_odds
                probability = (1 / price * 100) if price > 0 else 0
                
                # Determine which team/outcome
                if name == home_team:
                    if price > best_odds['home']['price']:
                        best_odds['home'] = {
                            'price': price,
                            'bookmaker': bookmaker,
                            'probability': round(probability, 2)
                        }
                elif name == away_team:
                    if price > best_odds['away']['price']:
                        best_odds['away'] = {
                            'price': price,
                            'bookmaker': bookmaker,
                            'probability': round(probability, 2)
                        }
                elif name.lower() == 'draw':
                    if price > best_odds['draw']['price']:
                        best_odds['draw'] = {
                            'price': price,
                            'bookmaker': bookmaker,
                            'probability': round(probability, 2)
                        }
        
        return best_odds
    
    def get_odds_for_event(self, event_name: str, sport: str) -> Optional[Dict[str, Any]]:
        """
        Get betting odds for a specific event.
        
        Args:
            event_name: Name of the event
            sport: Sport type
        
        Returns:
            Odds data for the event or None
        """
        raw_data = self.fetch_raw_data()
        if not raw_data or sport not in raw_data:
            return None
        
        events = self.parse_events({sport: raw_data[sport]})
        
        for event in events:
            participants = event.get('participants', [])
            if any(event_name.lower() in p.lower() for p in participants):
                return event
        
        return None
