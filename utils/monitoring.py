"""
Monitoring and metrics collection utilities.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .logger import LoggerMixin


class MetricsCollector(LoggerMixin):
    """Collects and tracks metrics for the application."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.timers = {}
    
    def record_metric(self, name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a metric value."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics[name].append({
            'value': value,
            'timestamp': timestamp
        })
    
    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter metric."""
        self.counters[name] += amount
    
    def start_timer(self, name: str):
        """Start timing an operation."""
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timing an operation and record the duration."""
        if name not in self.timers:
            self.logger.warning(f"Timer '{name}' was not started")
            return 0.0
        
        duration = time.time() - self.timers[name]
        del self.timers[name]
        
        self.record_metric(f"{name}_duration", duration)
        return duration
    
    def get_metric_summary(self, name: str, hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_values = [
            m['value'] for m in self.metrics[name] 
            if m['timestamp'] >= cutoff
        ]
        
        if not recent_values:
            return {'count': 0}
        
        return {
            'count': len(recent_values),
            'sum': sum(recent_values),
            'avg': sum(recent_values) / len(recent_values),
            'min': min(recent_values),
            'max': max(recent_values)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            'metrics': dict(self.metrics),
            'counters': dict(self.counters),
            'active_timers': list(self.timers.keys())
        }


class HealthMonitor(LoggerMixin):
    """Monitors application health and performance."""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.last_successful_fetch = {}
        self.error_counts = defaultdict(int)
    
    def record_successful_fetch(self, sport: str):
        """Record a successful data fetch for a sport."""
        self.last_successful_fetch[sport] = datetime.now()
        self.metrics.increment_counter(f"{sport}_successful_fetches")
        self.logger.debug(f"Recorded successful fetch for {sport}")
    
    def record_fetch_error(self, sport: str, error_type: str):
        """Record a fetch error for a sport."""
        error_key = f"{sport}_{error_type}"
        self.error_counts[error_key] += 1
        self.metrics.increment_counter(f"{sport}_fetch_errors")
        self.logger.warning(f"Recorded fetch error for {sport}: {error_type}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the application."""
        now = datetime.now()
        status = {
            'timestamp': now.isoformat(),
            'overall_status': 'healthy',
            'sports_status': {}
        }
        
        # Check each sport's health
        for sport, last_fetch in self.last_successful_fetch.items():
            hours_since_fetch = (now - last_fetch).total_seconds() / 3600
            
            if hours_since_fetch > 48:  # More than 2 days
                sport_status = 'unhealthy'
                status['overall_status'] = 'degraded'
            elif hours_since_fetch > 24:  # More than 1 day
                sport_status = 'warning'
                if status['overall_status'] == 'healthy':
                    status['overall_status'] = 'warning'
            else:
                sport_status = 'healthy'
            
            status['sports_status'][sport] = {
                'status': sport_status,
                'last_successful_fetch': last_fetch.isoformat(),
                'hours_since_fetch': round(hours_since_fetch, 2)
            }
        
        return status
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of all errors."""
        return dict(self.error_counts)
