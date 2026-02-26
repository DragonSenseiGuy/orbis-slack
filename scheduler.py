"""
APScheduler-based background polling for Orbis.
Polls Google Calendar and updates Slack status.
"""

import os
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import calendar_client
import slack_status
from settings_store import load_settings, get_event_settings, get_global_settings

_scheduler: Optional[BackgroundScheduler] = None
_current_poll_interval: Optional[int] = None


def get_scheduler() -> BackgroundScheduler:
    """Get or create the background scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def poll_and_update():
    """
    Main polling function - fetches calendar events and updates Slack status.
    Called automatically by the scheduler.
    """
    print(f"[Orbis] Polling calendar at {datetime.now().isoformat()}")
    
    settings = load_settings()
    global_settings = settings.get("global", {})
    
    lookahead_hours = global_settings.get("lookahead_hours", 24)
    auto_clear = global_settings.get("auto_clear", True)
    
    # Fetch events from Google Calendar
    try:
        events = calendar_client.list_upcoming_events(lookahead_hours)
    except Exception as e:
        print(f"[Orbis] Error fetching calendar events: {e}")
        return
    
    if not events:
        print("[Orbis] No upcoming events found")
    
    # Find currently active events
    active_events = calendar_client.get_currently_active_events(events)
    
    # Find the active event to use for status (soonest ending, respecting mode)
    selected_event = None
    selected_settings = None
    
    for event in active_events:
        event_settings = get_event_settings(event['id'], settings)
        mode = event_settings.get("mode", "include")
        
        if mode == "skip":
            print(f"[Orbis] Skipping event: {event['summary']}")
            continue
        
        # This is our selected event
        selected_event = event
        selected_settings = event_settings
        break  # Use the first non-skipped event (soonest ending)
    
    # Update status based on selected event
    if selected_event:
        mode = selected_settings.get("mode", "include")
        global_defaults = global_settings
        
        if mode == "include":
            # Use real event status
            emoji = selected_settings.get("emoji") or global_defaults.get("default_emoji", ":calendar:")
            template = selected_settings.get("text_template") or global_defaults.get("default_template", "{event_name}")
            text = template.replace("{event_name}", selected_event['summary'])
        
        elif mode == "placeholder":
            # Use placeholder status
            # Check for per-event placeholder override
            custom_placeholder = selected_settings.get("placeholder_emoji") is not None
            if custom_placeholder:
                emoji = selected_settings.get("placeholder_emoji", ":calendar:")
                text = selected_settings.get("placeholder_text", "In a meeting")
            else:
                emoji = global_defaults.get("placeholder_emoji", ":calendar:")
                text = global_defaults.get("placeholder_text", "In a meeting")
        
        # Set expiry to event end time
        expiry = selected_event['end']
        if not expiry.tzinfo:
            expiry = expiry.replace(tzinfo=datetime.timezone.utc)
        expiry_ts = int(expiry.timestamp())
        
        # Set the status
        success = slack_status.set_status(emoji, text, expiry_ts)
        if success:
            print(f"[Orbis] Status updated for event: {selected_event['summary']} (mode: {mode})")
        else:
            print(f"[Orbis] Failed to update status for event: {selected_event['summary']}")
    
    else:
        # No active events - clear status if auto_clear is enabled
        if auto_clear:
            current_status = slack_status.get_current_status()
            # Only clear if we set it (or if it's set and we should clear)
            if slack_status.was_set_by_bot(current_status) or current_status.get('status_text'):
                success = slack_status.clear_status()
                if success:
                    print("[Orbis] Status cleared (no active events)")
        else:
            print("[Orbis] Auto-clear disabled, leaving status unchanged")


def start_scheduler():
    """Start the background scheduler with current settings."""
    global _current_poll_interval
    
    scheduler = get_scheduler()
    
    # Get poll interval from settings
    settings = load_settings()
    poll_interval = settings.get("global", {}).get("poll_interval_seconds", 60)
    _current_poll_interval = poll_interval
    
    # Add job (allow coalesce so missed runs don't pile up)
    scheduler.add_job(
        poll_and_update,
        trigger=IntervalTrigger(seconds=poll_interval),
        id='calendar_poll',
        replace_existing=True,
        misfire_grace_time=30,
        coalesce=True,
    )
    
    scheduler.start()
    print(f"[Orbis] Scheduler started with {poll_interval}s interval")


def restart_scheduler():
    """Restart the scheduler with updated settings."""
    global _scheduler, _current_poll_interval
    
    # Get new interval
    settings = load_settings()
    new_interval = settings.get("global", {}).get("poll_interval_seconds", 60)
    
    if _current_poll_interval != new_interval or _scheduler is None:
        # Interval changed or scheduler not running - restart
        if _scheduler:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            print("[Orbis] Scheduler shutdown for restart")
        
        start_scheduler()
    else:
        print(f"[Orbis] Scheduler interval unchanged ({new_interval}s), no restart needed")


def run_sync_now() -> bool:
    """
    Manually trigger a sync.
    Called when user clicks 'Sync Now' button.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        poll_and_update()
        return True
    except Exception as e:
        print(f"[Orbis] Manual sync failed: {e}")
        return False
