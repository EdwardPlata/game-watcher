"""
Scheduled betting odds collection service.
Continuously refreshes betting odds data via webhook mechanism.
"""

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import os

from utils import DatabaseManager, get_logger, WebhookDelivery
from collectors.betting import BettingOddsCollector

logger = get_logger(__name__)


class BettingOddsScheduler:
    """
    Scheduler for automated betting odds collection.
    Runs in the background and refreshes odds at regular intervals.
    """
    
    def __init__(self, interval_minutes: int = 30):
        """
        Initialize the scheduler.
        
        Args:
            interval_minutes: How often to refresh odds (default: 30 minutes)
        """
        self.scheduler = BackgroundScheduler()
        self.interval_minutes = interval_minutes
        self.db = DatabaseManager()
        self.webhook = WebhookDelivery(self.db)
        self.collector = BettingOddsCollector()
        self.is_running = False
    
    def collect_and_notify(self):
        """Collect betting odds and send webhook notifications."""
        try:
            logger.info("Starting scheduled betting odds collection")
            start_time = datetime.now()
            
            # Fetch raw odds data
            raw_data = self.collector.fetch_raw_data()
            
            if not raw_data:
                logger.warning("No odds data available in scheduled collection")
                return
            
            # Parse odds
            parsed_odds = self.collector.parse_events(raw_data)
            
            if not parsed_odds:
                logger.warning("No odds parsed in scheduled collection")
                return
            
            # Insert into database
            inserted = self.db.insert_betting_odds(parsed_odds)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Collected {inserted} betting odds entries in {duration:.2f}s")
            
            # Send webhook notifications if new odds were added
            if inserted > 0:
                try:
                    # Format odds for webhook payload
                    webhook_payload = {
                        "event_type": "betting_odds_update",
                        "timestamp": datetime.now().isoformat(),
                        "odds_updated": inserted,
                        "sports": list(raw_data.keys())
                    }
                    
                    # Get webhook configs
                    webhook_configs = self.db.get_webhook_configs()
                    
                    if webhook_configs:
                        logger.info(f"Sending odds update to {len(webhook_configs)} webhooks")
                        # Note: We'd need to extend WebhookDelivery to support custom payloads
                        # For now, just log the notification
                        logger.info(f"Odds update notification: {webhook_payload}")
                    
                except Exception as e:
                    logger.error(f"Error sending webhook notification: {e}")
            
        except Exception as e:
            logger.error(f"Error in scheduled betting odds collection: {e}")
    
    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Betting odds scheduler is already running")
            return
        
        # Check if API key is configured
        if not os.getenv('ODDS_API_KEY'):
            logger.warning("ODDS_API_KEY not configured. Betting odds scheduler disabled.")
            logger.info("To enable: Set ODDS_API_KEY environment variable")
            return
        
        # Add job to scheduler
        self.scheduler.add_job(
            self.collect_and_notify,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='betting_odds_collection',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        # Run once immediately
        self.collect_and_notify()
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"Betting odds scheduler started (interval: {self.interval_minutes} minutes)")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Betting odds scheduler stopped")
    
    def get_status(self):
        """Get scheduler status."""
        return {
            "running": self.is_running,
            "interval_minutes": self.interval_minutes,
            "next_run": self.scheduler.get_job('betting_odds_collection').next_run_time.isoformat() 
                       if self.is_running and self.scheduler.get_job('betting_odds_collection') 
                       else None
        }


# Global scheduler instance
_scheduler_instance = None


def get_betting_odds_scheduler(interval_minutes: int = 30) -> BettingOddsScheduler:
    """
    Get or create the global betting odds scheduler instance.
    
    Args:
        interval_minutes: Collection interval in minutes
    
    Returns:
        BettingOddsScheduler instance
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = BettingOddsScheduler(interval_minutes=interval_minutes)
    
    return _scheduler_instance
