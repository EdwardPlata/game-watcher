"""
Anvil-compatible Sports Data Collectors
Adapts existing collectors to work with Anvil's server environment
"""

from utils.logger import get_logger
from collectors import COLLECTORS
import anvil.server
import sys
import os

# Add parent directory to path to access existing collectors
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


logger = get_logger(__name__)


class AnvilCollectorManager:
    """
    Manager class to coordinate data collection for Anvil environment.
    Wraps existing collectors to work with Anvil's server functions.
    """

    def __init__(self):
        self.supported_sports = list(COLLECTORS.keys())

    def get_collector(self, sport):
        """Get a collector instance for a specific sport."""
        if sport not in COLLECTORS:
            raise ValueError(f"Unsupported sport: {sport}")

        collector_class = COLLECTORS[sport]
        return collector_class()

    def collect_events_for_sport(self, sport):
        """
        Collect events for a specific sport.
        Returns a list of event dictionaries.
        """
        try:
            collector = self.get_collector(sport)
            events = collector.collect_events()
            logger.info(f"Collected {len(events)} events for {sport}")
            return events
        except Exception as e:
            logger.error(f"Error collecting events for {sport}: {e}")
            return []

    def collect_all_events(self):
        """
        Collect events for all supported sports.
        Returns a dictionary with results for each sport.
        """
        results = {}
        for sport in self.supported_sports:
            try:
                events = self.collect_events_for_sport(sport)
                results[sport] = {
                    "success": True,
                    "events": events,
                    "count": len(events)
                }
            except Exception as e:
                logger.error(f"Error collecting events for {sport}: {e}")
                results[sport] = {
                    "success": False,
                    "events": [],
                    "count": 0,
                    "error": str(e)
                }
        return results


# Create a global instance for use in server functions
collector_manager = AnvilCollectorManager()


@anvil.server.callable
def get_supported_sports():
    """Get list of supported sports for data collection."""
    return collector_manager.supported_sports


@anvil.server.callable
def test_collector(sport):
    """
    Test a specific collector to ensure it works in Anvil environment.
    Returns sample data without storing it.
    """
    try:
        if sport not in collector_manager.supported_sports:
            raise ValueError(f"Unsupported sport: {sport}")

        collector = collector_manager.get_collector(sport)

        # Get just the first few events for testing
        events = collector.collect_events()
        sample_events = events[:3] if events else []

        return {
            "sport": sport,
            "status": "success",
            "total_events": len(events),
            "sample_events": sample_events,
            "collector_class": collector.__class__.__name__
        }

    except Exception as e:
        logger.error(f"Error testing collector for {sport}: {e}")
        return {
            "sport": sport,
            "status": "error",
            "error": str(e),
            "total_events": 0,
            "sample_events": []
        }


@anvil.server.callable
def test_all_collectors():
    """
    Test all collectors to ensure they work in Anvil environment.
    Returns results for each sport.
    """
    results = {}

    for sport in collector_manager.supported_sports:
        try:
            result = test_collector(sport)
            results[sport] = result
        except Exception as e:
            logger.error(f"Error testing collector for {sport}: {e}")
            results[sport] = {
                "sport": sport,
                "status": "error",
                "error": str(e),
                "total_events": 0,
                "sample_events": []
            }

    return {
        "results": results,
        "total_sports": len(collector_manager.supported_sports),
        "successful_collectors": sum(1 for r in results.values() if r["status"] == "success")
    }


@anvil.server.callable
def validate_collector_dependencies():
    """
    Check if all required dependencies for collectors are available.
    This helps diagnose environment issues in Anvil.
    """
    try:
        import requests
        import beautifulsoup4
        from datetime import datetime
        import json

        # Test basic HTTP functionality
        test_url = "https://httpbin.org/get"
        response = requests.get(test_url, timeout=10)
        http_working = response.status_code == 200

        return {
            "dependencies_available": True,
            "http_working": http_working,
            "requests_version": requests.__version__,
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "dependencies_available": False,
            "error": str(e),
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
