# Game Watcher Webhook Configuration

This document describes how to configure webhooks to receive real-time notifications of new sports events.

## Overview

Game Watcher can send webhook notifications to your frontend application whenever new events are collected. This enables real-time updates without polling the API.

## Webhook Payload Format

When new events are collected, the following JSON payload is sent to configured webhook endpoints:

```json
{
  "event_type": "new_events",
  "timestamp": "2025-10-27T17:00:00.000Z",
  "total": 5,
  "events": [
    {
      "id": 123,
      "sport": "futbol",
      "date": "2025-10-28T18:00:00Z",
      "event": "Real Madrid vs Barcelona",
      "participants": ["Real Madrid", "Barcelona"],
      "location": "Santiago Bernabeu",
      "leagues": ["La Liga", "Spanish Football"],
      "watch_link": "https://www.espn.com/soccer/",
      "scraped_at": "2025-10-27T17:00:00Z"
    }
  ]
}
```

## Configuration via API

### Add a Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "frontend-webhook",
    "url": "https://your-frontend.com/api/webhooks/sports-events",
    "enabled": true
  }'
```

### List Webhooks

```bash
curl http://localhost:8000/api/v1/webhooks
```

### Test a Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/test \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-frontend.com/api/webhooks/sports-events"
  }'
```

### Manual Webhook Trigger

Manually trigger webhook delivery with recent events:

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/send?limit=10"
```

## Configuration via Database

You can also directly insert webhook configurations into the database:

```python
from utils import DatabaseManager

db = DatabaseManager()
db.add_webhook_config(
    name="frontend-webhook",
    url="https://your-frontend.com/api/webhooks/sports-events",
    enabled=True
)
```

## Automatic Webhook Delivery

Webhooks are automatically triggered when:
- New events are collected via `/api/v1/collect/{sport}`
- Backfill operations complete via `/api/v1/backfill/{year}/{month}`
- The scheduled data collection runs

## Webhook Endpoint Requirements

Your webhook endpoint should:

1. Accept POST requests with JSON payload
2. Return HTTP status 200, 201, 202, or 204 for successful delivery
3. Respond within 10 seconds (default timeout)
4. Handle duplicate events (same event may be sent multiple times)

## Example Webhook Handler (Node.js/Express)

```javascript
app.post('/api/webhooks/sports-events', async (req, res) => {
  try {
    const { event_type, timestamp, events, total } = req.body;
    
    if (event_type === 'new_events') {
      console.log(`Received ${total} new sports events`);
      
      // Process events
      for (const event of events) {
        await processEvent(event);
      }
      
      // Acknowledge receipt
      res.status(200).json({ received: total });
    } else if (event_type === 'test') {
      // Handle test webhook
      res.status(200).json({ status: 'ok', message: 'Webhook is working' });
    } else {
      res.status(400).json({ error: 'Unknown event type' });
    }
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

## Example Webhook Handler (Python/Flask)

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/webhooks/sports-events', methods=['POST'])
def handle_sports_webhook():
    try:
        data = request.json
        event_type = data.get('event_type')
        
        if event_type == 'new_events':
            events = data.get('events', [])
            print(f"Received {len(events)} new sports events")
            
            # Process events
            for event in events:
                process_event(event)
            
            return jsonify({'received': len(events)}), 200
        
        elif event_type == 'test':
            return jsonify({'status': 'ok', 'message': 'Webhook is working'}), 200
        
        else:
            return jsonify({'error': 'Unknown event type'}), 400
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
```

## Retry Logic

The webhook delivery system includes automatic retry logic:
- 3 retry attempts per webhook
- Retries occur immediately on failure
- Webhooks are marked as failed after all retries are exhausted

## Security Considerations

1. Use HTTPS URLs for webhook endpoints
2. Validate incoming webhook signatures (implement HMAC if needed)
3. Implement rate limiting on your webhook endpoint
4. Store webhook URLs securely
5. Use firewall rules to restrict webhook sources

## Monitoring

Check webhook delivery status in the logs:

```bash
tail -f sports_calendar.log | grep -i webhook
```

## Troubleshooting

### Webhook Not Receiving Events

1. Verify webhook URL is accessible: `curl -X POST https://your-webhook-url -H 'Content-Type: application/json' -d '{"test": true}'`
2. Check webhook is enabled in database
3. Review logs for delivery errors
4. Test webhook using the test endpoint

### Timeout Errors

- Ensure your endpoint responds within 10 seconds
- Process events asynchronously if needed
- Return 202 (Accepted) for async processing

### Duplicate Events

- Implement idempotency using event IDs
- Store processed event IDs to detect duplicates
- Use database constraints to prevent duplicate insertions

## Watch Links

Each event includes a `watch_link` field pointing to where you can watch the event online. These links are extracted from:

- **Futbol**: ESPN Soccer pages
- **UFC/MMA**: UFC.com, MMA Fighting, Tapology
- **Boxing**: BoxingScene schedule pages
- **F1**: Formula1.com racing calendar

Example usage in your frontend:

```javascript
events.forEach(event => {
  if (event.watch_link) {
    console.log(`Watch ${event.event} at: ${event.watch_link}`);
  }
});
```
