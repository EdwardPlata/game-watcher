"""
Tests for betting odds collector functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from collectors.betting import BettingOddsCollector
from utils import DatabaseManager


class TestBettingOddsCollector:
    """Test betting odds collector."""
    
    def test_collector_initialization(self):
        """Test that collector initializes correctly."""
        collector = BettingOddsCollector()
        assert collector.sport_name == "betting_odds"
        assert collector.base_url == "https://api.the-odds-api.com/v4"
        assert isinstance(collector.sport_mapping, dict)
    
    def test_proxy_list_loading_empty(self):
        """Test proxy list loading when no proxies configured."""
        with patch.dict('os.environ', {}, clear=True):
            collector = BettingOddsCollector()
            assert collector.proxy_list == []
    
    def test_proxy_list_loading_with_proxies(self):
        """Test proxy list loading with proxies configured."""
        test_proxies = "http://proxy1:8080,http://proxy2:8080"
        with patch.dict('os.environ', {'PROXY_LIST': test_proxies}):
            collector = BettingOddsCollector()
            assert len(collector.proxy_list) == 2
            assert collector.proxy_list[0] == "http://proxy1:8080"
    
    def test_get_next_proxy_rotation(self):
        """Test proxy rotation mechanism."""
        with patch.dict('os.environ', {'PROXY_LIST': "http://proxy1:8080,http://proxy2:8080"}):
            collector = BettingOddsCollector()
            
            # Get first proxy
            proxy1 = collector._get_next_proxy()
            assert proxy1['http'] == "http://proxy1:8080"
            
            # Get second proxy (should rotate)
            proxy2 = collector._get_next_proxy()
            assert proxy2['http'] == "http://proxy2:8080"
            
            # Get third proxy (should wrap back to first)
            proxy3 = collector._get_next_proxy()
            assert proxy3['http'] == "http://proxy1:8080"
    
    def test_rate_limiting(self):
        """Test that rate limiting works."""
        import time
        collector = BettingOddsCollector()
        collector.min_request_interval = 0.1
        
        start_time = time.time()
        collector._rate_limit()
        collector._rate_limit()
        end_time = time.time()
        
        # Second call should have been delayed
        assert end_time - start_time >= 0.1
    
    def test_fetch_raw_data_without_api_key(self):
        """Test that fetch returns None when API key not configured."""
        with patch.dict('os.environ', {}, clear=True):
            collector = BettingOddsCollector()
            result = collector.fetch_raw_data()
            assert result is None
    
    @patch('collectors.betting.collector.requests.get')
    def test_make_request_success(self, mock_get):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response
        
        collector = BettingOddsCollector()
        response = collector._make_request("http://test.com")
        
        assert response is not None
        assert response.status_code == 200
    
    @patch('collectors.betting.collector.requests.get')
    def test_make_request_rate_limit_retry(self, mock_get):
        """Test retry on rate limit (429)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        collector = BettingOddsCollector()
        collector.min_request_interval = 0.01  # Speed up test
        
        response = collector._make_request("http://test.com")
        
        # Should have retried multiple times
        assert mock_get.call_count > 1
    
    def test_parse_events_empty_data(self):
        """Test parsing with empty data."""
        collector = BettingOddsCollector()
        result = collector.parse_events({})
        assert result == []
    
    def test_parse_single_event(self):
        """Test parsing a single event."""
        collector = BettingOddsCollector()
        
        mock_event = {
            'id': 'test_event_123',
            'commence_time': '2025-11-01T19:00:00Z',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'bookmakers': [
                {
                    'title': 'DraftKings',
                    'markets': [
                        {
                            'key': 'h2h',
                            'outcomes': [
                                {'name': 'Team A', 'price': 2.5},
                                {'name': 'Team B', 'price': 2.8}
                            ]
                        }
                    ]
                }
            ]
        }
        
        result = collector._parse_single_event(mock_event, 'nfl')
        
        assert result is not None
        assert result['event_id'] == 'test_event_123'
        assert result['sport'] == 'nfl'
        assert result['home_team'] == 'Team A'
        assert result['away_team'] == 'Team B'
        assert result['bookmaker_count'] == 1
        assert 'best_odds' in result
    
    def test_calculate_best_odds(self):
        """Test best odds calculation."""
        collector = BettingOddsCollector()
        
        odds_data = [
            {
                'bookmaker': 'Bookmaker1',
                'market': 'h2h',
                'outcomes': [
                    {'name': 'Team A', 'price': 2.5},
                    {'name': 'Team B', 'price': 2.8}
                ]
            },
            {
                'bookmaker': 'Bookmaker2',
                'market': 'h2h',
                'outcomes': [
                    {'name': 'Team A', 'price': 2.7},  # Better odds for Team A
                    {'name': 'Team B', 'price': 2.6}
                ]
            }
        ]
        
        best_odds = collector._calculate_best_odds(odds_data, 'Team A', 'Team B')
        
        assert best_odds['home']['price'] == 2.7
        assert best_odds['home']['bookmaker'] == 'Bookmaker2'
        assert best_odds['away']['price'] == 2.8
        assert best_odds['away']['bookmaker'] == 'Bookmaker1'
        
        # Check implied probabilities
        assert best_odds['home']['probability'] > 0
        assert best_odds['away']['probability'] > 0


class TestDatabaseBettingOdds:
    """Test database operations for betting odds."""
    
    def test_insert_betting_odds(self):
        """Test inserting betting odds into database."""
        import tempfile
        import os
        
        # Create temporary database file
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            db = DatabaseManager(db_path)
            
            test_odds = [
                {
                    'event_id': 'test_123',
                    'sport': 'nfl',
                    'commence_time': '2025-11-01T19:00:00Z',
                    'home_team': 'Team A',
                    'away_team': 'Team B',
                    'participants': ['Team A', 'Team B'],
                    'odds_data': [{'bookmaker': 'Test', 'market': 'h2h', 'outcomes': []}],
                    'best_odds': {'home': {'price': 2.5}, 'away': {'price': 2.8}},
                    'bookmaker_count': 1
                }
            ]
            
            count = db.insert_betting_odds(test_odds)
            assert count == 1
            
            # Try inserting same odds again (should update, not duplicate)
            count = db.insert_betting_odds(test_odds)
            assert count == 1
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.remove(db_path)
    
    def test_get_all_betting_odds(self):
        """Test retrieving all betting odds."""
        import tempfile
        import os
        
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            db = DatabaseManager(db_path)
            
            test_odds = [
                {
                    'event_id': 'test_123',
                    'sport': 'nfl',
                    'commence_time': '2025-11-01T19:00:00Z',
                    'home_team': 'Team A',
                    'away_team': 'Team B',
                    'participants': ['Team A', 'Team B'],
                    'odds_data': [],
                    'best_odds': {},
                    'bookmaker_count': 1
                }
            ]
            
            db.insert_betting_odds(test_odds)
            
            odds = db.get_all_betting_odds(sport='nfl')
            assert len(odds) == 1
            assert odds[0]['sport'] == 'nfl'
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
    
    def test_get_odds_for_event(self):
        """Test retrieving odds for specific event."""
        import tempfile
        import os
        from datetime import datetime, timedelta
        
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            db = DatabaseManager(db_path)
            
            # Use future date
            future_date = (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            
            test_odds = [
                {
                    'event_id': 'test_123',
                    'sport': 'nfl',
                    'commence_time': future_date,
                    'home_team': 'Kansas City Chiefs',
                    'away_team': 'Buffalo Bills',
                    'participants': ['Kansas City Chiefs', 'Buffalo Bills'],
                    'odds_data': [],
                    'best_odds': {},
                    'bookmaker_count': 1
                }
            ]
            
            db.insert_betting_odds(test_odds)
            
            # Search by participant name
            odds = db.get_odds_for_event('nfl', ['Kansas City'])
            assert odds is not None
            assert odds['home_team'] == 'Kansas City Chiefs'
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)



def test_betting_scheduler_initialization():
    """Test betting odds scheduler initialization."""
    from utils import get_betting_odds_scheduler
    
    scheduler = get_betting_odds_scheduler(interval_minutes=60)
    assert scheduler is not None
    assert scheduler.interval_minutes == 60
    assert not scheduler.is_running


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
