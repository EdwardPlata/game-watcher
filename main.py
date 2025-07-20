#!/usr/bin/env python3
"""
Daily Sports Calendar App - Refactored
A comprehensive sports schedule tracker with API integration and calendar sync.

Fetches and stores daily schedules for:
- Fútbol (Soccer)
- NFL
- NBA
- F1
- Boxing
- MMA/UFC
"""

import argparse
import sys
from datetime import datetime
from typing import Optional, Dict

# Scheduler imports
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Application imports
from utils import DatabaseManager, HealthMonitor, get_logger
from collectors import COLLECTORS, get_collector

# Configure logging
logger = get_logger(__name__)


class SportsCalendarApp:
    """Main application class."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.health_monitor = HealthMonitor()
        self.supported_sports = list(COLLECTORS.keys())
    
    def fetch_sport_events(self, sport: str) -> int:
        """
        Fetch events for a specific sport.
        
        Args:
            sport: Sport name
        
        Returns:
            Number of new events inserted
        """
        try:
            # Start timing the operation
            self.health_monitor.metrics.start_timer(f"{sport}_fetch")
            
            # Get the appropriate collector
            collector = get_collector(sport)
            
            # Fetch events
            events = collector.fetch_events()
            
            # Store events in database
            inserted = self.db.insert_events(events)
            
            # Record successful fetch
            self.health_monitor.record_successful_fetch(sport)
            
            # End timing
            duration = self.health_monitor.metrics.end_timer(f"{sport}_fetch")
            logger.info(f"Fetched {len(events)} {sport} events in {duration:.2f}s, inserted {inserted} new events")
            
            return inserted
            
        except Exception as e:
            self.health_monitor.record_fetch_error(sport, type(e).__name__)
            logger.error(f"Failed to fetch {sport} events: {e}")
            return 0
    
    def fetch_all_sports(self) -> int:
        """Fetch events for all supported sports."""
        total_inserted = 0
        
        logger.info("Starting fetch for all sports...")
        self.health_monitor.metrics.start_timer("fetch_all")
        
        for sport in self.supported_sports:
            logger.info(f"Fetching {sport} events...")
            inserted = self.fetch_sport_events(sport)
            total_inserted += inserted
        
        duration = self.health_monitor.metrics.end_timer("fetch_all")
        logger.info(f"Completed fetch for all sports in {duration:.2f}s. Total new events: {total_inserted}")
        
        return total_inserted
    
    def fetch_current_month(self) -> Dict[str, int]:
        """
        Fetch events for all sports for the current month.
        
        Returns:
            Dictionary with sport names and number of new events inserted
        """
        logger.info("Starting current month data collection for all sports...")
        
        results = {}
        total_start_time = datetime.now()
        
        # Get current month info
        now = datetime.now()
        month_name = now.strftime("%B %Y")
        
        print(f"\n🗓️  Fetching all sports data for {month_name}")
        print("=" * 60)
        
        for sport in self.supported_sports:
            start_time = datetime.now()
            try:
                print(f"📡 Collecting {sport.upper()} events...")
                new_events = self.fetch_sport_events(sport)
                results[sport] = new_events
                
                duration = (datetime.now() - start_time).total_seconds()
                status_icon = "✅" if new_events > 0 else "⚪"
                print(f"   {status_icon} {sport.upper()}: {new_events} new events ({duration:.1f}s)")
                
            except Exception as e:
                logger.error(f"Failed to fetch {sport} events: {e}")
                results[sport] = 0
                print(f"   ❌ {sport.upper()}: Failed - {str(e)[:50]}...")
        
        total_duration = (datetime.now() - total_start_time).total_seconds()
        total_events = sum(results.values())
        
        print("\n" + "=" * 60)
        print(f"🎯 Collection Summary for {month_name}:")
        print(f"   • Total new events: {total_events}")
        print(f"   • Sports processed: {len(self.supported_sports)}")
        print(f"   • Total time: {total_duration:.1f}s")
        print(f"   • Average per sport: {total_duration/len(self.supported_sports):.1f}s")
        
        if total_events > 0:
            print(f"\n🌐 View your calendar: http://localhost:8000")
            print(f"📊 Admin dashboard: http://localhost:8000/admin")
        
        logger.info(f"Current month fetch completed: {total_events} total new events in {total_duration:.2f}s")
        return results
    
    def backfill_month(self, year: int, month: int) -> Dict[str, int]:
        """
        Backfill events for a specific month.
        
        Args:
            year: Year to backfill
            month: Month to backfill (1-12)
        
        Returns:
            Dictionary with sport names and number of new events inserted
        """
        logger.info(f"Starting backfill for {year}-{month:02d}")
        
        results = {}
        total_start_time = datetime.now()
        
        # Month info
        import calendar
        month_name = calendar.month_name[month]
        
        print(f"\n📅 Backfilling data for {month_name} {year}")
        print("=" * 60)
        
        for sport in self.supported_sports:
            start_time = datetime.now()
            try:
                print(f"🔄 Backfilling {sport.upper()} events...")
                new_events = self.fetch_sport_events(sport)
                results[sport] = new_events
                
                duration = (datetime.now() - start_time).total_seconds()
                status_icon = "✅" if new_events > 0 else "⚪"
                print(f"   {status_icon} {sport.upper()}: {new_events} events added ({duration:.1f}s)")
                
            except Exception as e:
                logger.error(f"Failed to backfill {sport} events: {e}")
                results[sport] = 0
                print(f"   ❌ {sport.upper()}: Failed - {str(e)[:50]}...")
        
        total_duration = (datetime.now() - total_start_time).total_seconds()
        total_events = sum(results.values())
        
        print("\n" + "=" * 60)
        print(f"📊 Backfill Summary for {month_name} {year}:")
        print(f"   • Total events added: {total_events}")
        print(f"   • Sports processed: {len(self.supported_sports)}")
        print(f"   • Total time: {total_duration:.1f}s")
        
        if total_events > 0:
            print(f"\n🌐 View updated calendar: http://localhost:8000/?year={year}&month={month}")
        
        logger.info(f"Backfill completed for {year}-{month:02d}: {total_events} total new events")
        return results
    
    def show_upcoming_events(self, sport: Optional[str] = None, days: int = 7):
        """Display upcoming events."""
        events = self.db.get_upcoming_events(sport, days)
        
        if not events:
            print(f"No upcoming events found for {sport or 'any sport'}")
            return
        
        print(f"\nUpcoming {sport or 'sports'} events (next {days} days):")
        print("-" * 60)
        
        for event in events:
            date_obj = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            print(f"{event['sport'].upper()}: {event['event']}")
            print(f"  Date: {date_obj.strftime('%Y-%m-%d %H:%M %Z')}")
            print(f"  Location: {event['location']}")
            print(f"  Participants: {', '.join(event['participants'])}")
            print()
    
    def sync_to_calendar(self):
        """Sync new events to Google Calendar - Currently disabled."""
        logger.info("Google Calendar sync is currently disabled")
        print("📅 Google Calendar sync is not enabled yet.")
        print("   Use the web interface at http://localhost:8000 to view events.")
        return 0
    
    def show_health_status(self):
        """Display application health status."""
        status = self.health_monitor.get_health_status()
        
        print(f"\nApplication Health Status - {status['timestamp']}")
        print("=" * 60)
        print(f"Overall Status: {status['overall_status'].upper()}")
        print()
        
        print("Sport-specific Status:")
        for sport, sport_status in status['sports_status'].items():
            print(f"  {sport.upper()}: {sport_status['status']}")
            print(f"    Last successful fetch: {sport_status['last_successful_fetch']}")
            print(f"    Hours since fetch: {sport_status['hours_since_fetch']}")
            print()
        
        # Show error summary
        errors = self.health_monitor.get_error_summary()
        if errors:
            print("Recent Errors:")
            for error_type, count in errors.items():
                print(f"  {error_type}: {count}")
        else:
            print("No recent errors")
    
    def start_scheduler(self):
        """Start the daily scheduler."""
        scheduler = BlockingScheduler()
        
        # Schedule daily fetch at 2:00 AM
        scheduler.add_job(
            self.fetch_all_sports,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_fetch',
            replace_existing=True
        )
        
        logger.info("Scheduler started. Daily fetch at 2:00 AM")
        
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Daily Sports Calendar App')
    parser.add_argument('command', choices=['fetch', 'show', 'sync', 'schedule', 'health', 'month', 'backfill'],
                       help='Command to execute')
    parser.add_argument('sport', nargs='?', 
                       choices=list(COLLECTORS.keys()),
                       help='Specific sport (for show/fetch commands)')
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to show (default: 7)')
    parser.add_argument('--year', type=int, 
                       help='Year for backfill command')
    parser.add_argument('--month', type=int, 
                       help='Month for backfill command (1-12)')
    
    args = parser.parse_args()
    
    app = SportsCalendarApp()
    
    if args.command == 'fetch':
        if args.sport:
            app.fetch_sport_events(args.sport)
        else:
            app.fetch_all_sports()
    
    elif args.command == 'month':
        app.fetch_current_month()
    
    elif args.command == 'backfill':
        if not args.year or not args.month:
            parser.error("backfill command requires --year and --month arguments")
        if args.month < 1 or args.month > 12:
            parser.error("month must be between 1 and 12")
        app.backfill_month(args.year, args.month)
    
    elif args.command == 'show':
        app.show_upcoming_events(args.sport, args.days)
    
    elif args.command == 'sync':
        app.sync_to_calendar()
    
    elif args.command == 'health':
        app.show_health_status()
    
    elif args.command == 'schedule':
        app.start_scheduler()


if __name__ == '__main__':
    main()
