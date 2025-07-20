"""
Sports data collectors package.

This package contains individual data collectors for each supported sport.
Each collector is responsible for fetching and parsing data from its respective API.
"""

from .f1 import F1Collector
from .futbol import FutbolCollector
from .nfl import NFLCollector
from .nba import NBACollector
from .boxing import BoxingCollector
from .mma import MMACollector

# Registry of all available collectors
COLLECTORS = {
    'f1': F1Collector,
    'futbol': FutbolCollector,
    'nfl': NFLCollector,
    'nba': NBACollector,
    'boxing': BoxingCollector,
    'mma': MMACollector
}

__all__ = [
    'F1Collector',
    'FutbolCollector', 
    'NFLCollector',
    'NBACollector',
    'BoxingCollector',
    'MMACollector',
    'COLLECTORS'
]


def get_collector(sport: str):
    """
    Get a collector instance for the specified sport.
    
    Args:
        sport: Sport name (e.g., 'f1', 'nfl', 'nba')
    
    Returns:
        Collector instance
    
    Raises:
        ValueError: If sport is not supported
    """
    if sport not in COLLECTORS:
        raise ValueError(f"Unsupported sport: {sport}. Available: {list(COLLECTORS.keys())}")
    
    return COLLECTORS[sport]()
