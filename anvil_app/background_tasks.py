"""
Anvil Background Tasks Module for Game Watcher
Replaces APScheduler with Anvil's background task system
"""

import anvil.server
from datetime import datetime, timedelta
import time

# Import server functions
from .server_module import collect_all_sports_data, collect_betting_odds


@anvil.server.background_task
def scheduled_data_collection():
    """
    Background task to collect sports data periodically.
    This replaces the APScheduler functionality.

    In Anvil, this would be scheduled to run via the admin dashboard
    or called periodically by the client.
    """
    try:
        result = collect_all_sports_data()
        print(
            f"Scheduled data collection completed: {result['total_events_inserted']} events inserted")
        return result
    except Exception as e:
        print(f"Error in scheduled data collection: {e}")
        raise


@anvil.server.background_task
def scheduled_betting_odds_collection():
    """
    Background task to collect betting odds periodically.
    This should run less frequently to respect API limits.
    """
    try:
        result = collect_betting_odds()
        print(
            f"Scheduled betting odds collection completed: {result['odds_inserted']} odds inserted")
        return result
    except Exception as e:
        print(f"Error in scheduled betting odds collection: {e}")
        raise


@anvil.server.callable
def start_periodic_data_collection(interval_hours=6):
    """
    Start periodic data collection.

    Note: Anvil doesn't have built-in cron-like scheduling like APScheduler.
    This function would need to be called periodically by:
    1. A client-side timer
    2. External cron job calling via HTTP API
    3. Manual trigger from admin interface
    """
    try:
        # Launch background task for sports data
        task = anvil.server.launch_background_task('scheduled_data_collection')

        return {
            "status": "started",
            "task_id": task.get_id(),
            "timestamp": datetime.now().isoformat(),
            "message": f"Data collection task started (interval: {interval_hours} hours)"
        }
    except Exception as e:
        raise anvil.server.AnvilWrappedError(
            f"Error starting periodic collection: {str(e)}")


@anvil.server.callable
def start_periodic_betting_odds_collection(interval_hours=1):
    """
    Start periodic betting odds collection.
    """
    try:
        # Launch background task for betting odds
        task = anvil.server.launch_background_task(
            'scheduled_betting_odds_collection')

        return {
            "status": "started",
            "task_id": task.get_id(),
            "timestamp": datetime.now().isoformat(),
            "message": f"Betting odds collection task started (interval: {interval_hours} hours)"
        }
    except Exception as e:
        raise anvil.server.AnvilWrappedError(
            f"Error starting betting odds collection: {str(e)}")


@anvil.server.callable
def get_background_task_status(task_id):
    """Get status of a background task."""
    try:
        task = anvil.server.get_background_task(task_id)
        if task:
            return {
                "task_id": task_id,
                "status": task.get_state(),
                "is_running": task.is_running(),
                "is_completed": task.is_completed(),
                "progress": task.get_progress()
            }
        else:
            return {"error": "Task not found"}
    except Exception as e:
        raise anvil.server.AnvilWrappedError(
            f"Error getting task status: {str(e)}")


@anvil.server.callable
def list_running_tasks():
    """List all running background tasks."""
    try:
        # Note: Anvil might not have a direct way to list all tasks
        # This would depend on how Anvil implements task management
        return {
            "message": "Task listing not implemented - depends on Anvil's task management API",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise anvil.server.AnvilWrappedError(f"Error listing tasks: {str(e)}")
