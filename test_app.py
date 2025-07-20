#!/usr/bin/env python3
"""
Test script for the Daily Sports Calendar App
Tests the F1 implementation and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import SportsCalendarApp, SportsFetcher, DatabaseManager
import logging

# Set up logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_f1_fetcher():
    """Test the F1 data fetching functionality."""
    print("Testing F1 data fetcher...")
    
    fetcher = SportsFetcher()
    events = fetcher.fetch_f1()
    
    if events:
        print(f"✅ Successfully fetched {len(events)} F1 events")
        print("\nSample F1 event:")
        print("-" * 40)
        for key, value in events[0].items():
            print(f"{key}: {value}")
        print("-" * 40)
        return events
    else:
        print("❌ No F1 events fetched")
        return []

def test_database():
    """Test database operations."""
    print("\nTesting database functionality...")
    
    # Create test event
    test_events = [{
        "sport": "test",
        "date": "2025-07-20T18:00:00Z",
        "event": "Test Event",
        "participants": ["Team A", "Team B"],
        "location": "Test Stadium"
    }]
    
    db = DatabaseManager(db_name='test_sports_calendar.db')
    
    # Insert test event
    inserted = db.insert_events(test_events)
    print(f"✅ Inserted {inserted} test events")
    
    # Retrieve events
    upcoming = db.get_upcoming_events(days=30)
    print(f"✅ Retrieved {len(upcoming)} upcoming events")
    
    # Clean up test database
    import os
    if os.path.exists('test_sports_calendar.db'):
        os.remove('test_sports_calendar.db')
        print("✅ Cleaned up test database")

def test_full_app():
    """Test the full application workflow."""
    print("\nTesting full application...")
    
    # Use test database
    original_db = DatabaseManager.DB_NAME
    app = SportsCalendarApp()
    app.db = DatabaseManager(db_name='test_full_app.db')
    
    try:
        # Test fetching F1 events only
        events = app.fetcher.fetch_f1()
        if events:
            inserted = app.db.insert_events(events)
            print(f"✅ Full app test: Inserted {inserted} F1 events")
            
            # Show upcoming events
            print("\nUpcoming F1 events:")
            app.show_upcoming_events('f1', days=90)
        else:
            print("❌ No events to insert in full app test")
    
    finally:
        # Clean up
        import os
        if os.path.exists('test_full_app.db'):
            os.remove('test_full_app.db')
            print("✅ Cleaned up test database")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Daily Sports Calendar App - Test Suite")
    print("=" * 50)
    
    try:
        # Test F1 fetcher
        f1_events = test_f1_fetcher()
        
        # Test database
        test_database()
        
        # Test full app if F1 data is available
        if f1_events:
            test_full_app()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("=" * 50)
        
        # Show usage examples
        print("\nUsage Examples:")
        print("python app.py fetch          # Fetch all sports")
        print("python app.py show f1        # Show F1 events")
        print("python app.py show --days 30 # Show all events for 30 days")
        print("python app.py schedule       # Start daily scheduler")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()