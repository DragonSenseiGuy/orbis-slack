"""
Settings management for Orbis - stores global defaults and per-event overrides.
Uses a local JSON file for persistence.
"""

import json
import os
import re
from typing import Optional
from pathlib import Path

SETTINGS_FILE = Path("settings.json")

DEFAULT_SETTINGS = {
    "global": {
        "default_emoji": ":calendar:",
        "default_template": "{event_name}",
        "placeholder_emoji": ":calendar:",
        "placeholder_text": "In a meeting",
        "lookahead_hours": 24,
        "max_events": 10,
        "auto_clear": True,
        "poll_interval_seconds": 60
    },
    "events": {}
}


def load_settings() -> dict:
    """Load settings from JSON file or create with defaults if not exists."""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in settings[key]:
                            settings[key][sub_key] = sub_value
            return settings
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save settings to JSON file atomically."""
    temp_file = SETTINGS_FILE.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(settings, f, indent=2)
    temp_file.replace(SETTINGS_FILE)


def get_event_base_id(event_id: str) -> str:
    """
    Extract base recurring event ID by stripping the datetime suffix.
    Google Calendar recurring event IDs look like: abc123_20240216T100000Z
    """
    # Match pattern: base_id_YYYYMMDDTHHMMSSZ
    match = re.match(r'^(.+)_(\d{8}T\d{6}Z)$', event_id)
    if match:
        return match.group(1)
    return event_id


def get_event_settings(event_id: str, settings: Optional[dict] = None) -> dict:
    """
    Get settings for a specific event.
    First checks for per-instance override, then falls back to base recurring ID.
    Returns default settings if neither exists.
    """
    if settings is None:
        settings = load_settings()
    
    events = settings.get("events", {})
    
    # Check for per-instance override first
    if event_id in events:
        return events[event_id]
    
    # Fall back to base recurring ID
    base_id = get_event_base_id(event_id)
    if base_id in events:
        return events[base_id]
    
    # Return default
    return {"mode": "include"}


def save_event_settings(event_id: str, event_settings: dict) -> None:
    """Save settings for a specific event."""
    settings = load_settings()
    if "events" not in settings:
        settings["events"] = {}
    settings["events"][event_id] = event_settings
    save_settings(settings)


def delete_event_settings(event_id: str) -> None:
    """Remove per-event override, falling back to defaults."""
    settings = load_settings()
    if "events" in settings and event_id in settings["events"]:
        del settings["events"][event_id]
        save_settings(settings)


def update_global_settings(global_settings: dict) -> None:
    """Update global settings."""
    settings = load_settings()
    settings["global"] = global_settings
    save_settings(settings)


def get_global_settings() -> dict:
    """Get global settings."""
    settings = load_settings()
    return settings.get("global", DEFAULT_SETTINGS["global"])
