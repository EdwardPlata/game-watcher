"""
Webhook delivery utilities.
Handles sending events to configured webhook endpoints.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import requests
from .logger import get_logger

logger = get_logger(__name__)


class WebhookDelivery:
    """Handles webhook delivery to configured endpoints."""
    
    def __init__(self, db_manager=None):
        """Initialize webhook delivery with database manager."""
        self.db = db_manager
        self.timeout = 10  # seconds
        self.retry_count = 3
    
    def send_new_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send new events to all configured webhooks.
        
        Args:
            events: List of event dictionaries
        
        Returns:
            Dictionary with delivery status
        """
        if not events:
            logger.info("No events to send via webhook")
            return {"success": True, "events_sent": 0, "webhooks_notified": 0}
        
        # Get webhook configurations from database
        webhook_configs = []
        if self.db:
            webhook_configs = self.db.get_webhook_configs()
        
        if not webhook_configs:
            logger.warning("No webhook endpoints configured")
            return {"success": False, "error": "No webhook endpoints configured", "events_sent": 0}
        
        # Prepare payload
        payload = {
            "event_type": "new_events",
            "timestamp": datetime.now().isoformat(),
            "events": events,
            "total": len(events)
        }
        
        results = []
        successful_deliveries = 0
        
        for config in webhook_configs:
            webhook_url = config['url']
            webhook_name = config['name']
            
            try:
                result = self._deliver_to_webhook(webhook_url, payload, webhook_name)
                results.append(result)
                if result['success']:
                    successful_deliveries += 1
            except Exception as e:
                logger.error(f"Failed to deliver to webhook {webhook_name}: {e}")
                results.append({
                    "webhook": webhook_name,
                    "url": webhook_url,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": successful_deliveries > 0,
            "events_sent": len(events),
            "webhooks_notified": successful_deliveries,
            "total_webhooks": len(webhook_configs),
            "results": results
        }
    
    def _deliver_to_webhook(self, url: str, payload: Dict[str, Any], name: str = "webhook") -> Dict[str, Any]:
        """
        Deliver payload to a specific webhook URL.
        
        Args:
            url: Webhook URL
            payload: Data to send
            name: Webhook name for logging
        
        Returns:
            Dictionary with delivery result
        """
        # Validate URL to prevent SSRF
        if not self._is_safe_webhook_url(url):
            return {
                "webhook": name,
                "url": url,
                "success": False,
                "error": "Invalid or unsafe webhook URL",
                "attempts": 0
            }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "game-watcher/1.0"
        }
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Delivering to webhook {name} (attempt {attempt + 1}/{self.retry_count})")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Successfully delivered to webhook {name}")
                    return {
                        "webhook": name,
                        "url": url,
                        "success": True,
                        "status_code": response.status_code,
                        "attempt": attempt + 1
                    }
                else:
                    logger.warning(f"Webhook {name} returned status {response.status_code}")
                    if attempt < self.retry_count - 1:
                        continue
                    return {
                        "webhook": name,
                        "url": url,
                        "success": False,
                        "status_code": response.status_code,
                        "error": f"HTTP {response.status_code}",
                        "attempts": attempt + 1
                    }
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout delivering to webhook {name} (attempt {attempt + 1})")
                if attempt < self.retry_count - 1:
                    continue
                return {
                    "webhook": name,
                    "url": url,
                    "success": False,
                    "error": "Timeout",
                    "attempts": attempt + 1
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error delivering to webhook {name}: {e}")
                if attempt < self.retry_count - 1:
                    continue
                return {
                    "webhook": name,
                    "url": url,
                    "success": False,
                    "error": str(e),
                    "attempts": attempt + 1
                }
        
        return {
            "webhook": name,
            "url": url,
            "success": False,
            "error": "Max retries exceeded",
            "attempts": self.retry_count
        }
    
    def test_webhook(self, url: str) -> bool:
        """
        Test a webhook URL with a simple ping.
        
        Args:
            url: Webhook URL to test
        
        Returns:
            True if webhook is reachable
        """
        # Validate URL to prevent SSRF attacks
        if not self._is_safe_webhook_url(url):
            logger.error(f"Unsafe webhook URL rejected: {url}")
            return False
        
        test_payload = {
            "event_type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Webhook connectivity test from game-watcher"
        }
        
        try:
            response = requests.post(
                url,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            return response.status_code in [200, 201, 202, 204]
        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False
    
    def _is_safe_webhook_url(self, url: str) -> bool:
        """
        Validate webhook URL to prevent SSRF attacks.
        
        Args:
            url: URL to validate
        
        Returns:
            True if URL is safe to use
        """
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            
            # Must be HTTP or HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Must have a hostname
            if not parsed.hostname:
                return False
            
            # Block localhost and private IP ranges
            hostname = parsed.hostname.lower()
            
            # Block localhost variants
            if hostname in ['localhost', '127.0.0.1', '0.0.0.0', '::1']:
                logger.warning(f"Blocked localhost webhook URL: {url}")
                return False
            
            # Block private IP ranges (simplified check)
            if (hostname.startswith('10.') or 
                hostname.startswith('192.168.') or
                hostname.startswith('172.16.') or
                hostname.startswith('172.17.') or
                hostname.startswith('172.18.') or
                hostname.startswith('172.19.') or
                hostname.startswith('172.20.') or
                hostname.startswith('172.21.') or
                hostname.startswith('172.22.') or
                hostname.startswith('172.23.') or
                hostname.startswith('172.24.') or
                hostname.startswith('172.25.') or
                hostname.startswith('172.26.') or
                hostname.startswith('172.27.') or
                hostname.startswith('172.28.') or
                hostname.startswith('172.29.') or
                hostname.startswith('172.30.') or
                hostname.startswith('172.31.')):
                logger.warning(f"Blocked private IP webhook URL: {url}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating webhook URL: {e}")
            return False
