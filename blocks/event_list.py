"""
Event list Block Kit UI for Orbis.
"""

from typing import Dict, List, Optional
from datetime import datetime

from settings_store import get_event_settings, load_settings


def format_event_time(event: Dict) -> str:
    """Format event time for display."""
    start = event['start']
    end = event['end']
    
    if event['is_all_day']:
        # All-day event
        start_str = start.strftime('%a %d %b') if isinstance(start, datetime) else str(start)
        return f"All day • {start_str}"
    
    # Timed event
    start_time = start.strftime('%H:%M') if isinstance(start, datetime) else str(start)
    end_time = end.strftime('%H:%M') if isinstance(end, datetime) else str(end)
    day = start.strftime('%a %d %b') if isinstance(start, datetime) else ''
    
    return f"{start_time}–{end_time} • {day}"


def get_mode_badge(mode: str) -> str:
    """Get emoji badge for event mode."""
    badges = {
        "include": "🟢 INCLUDE",
        "placeholder": "🔵 PLACEHOLDER",
        "skip": "⚫ SKIP"
    }
    return badges.get(mode, "⚪ UNKNOWN")


def get_event_blocks(events: List[Dict]) -> List[Dict]:
    """Generate Block Kit blocks for the event list."""
    settings = load_settings()
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📋  Upcoming Events",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Showing next {len(events)} events"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]
    
    if not events:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "_No upcoming events found in the configured time window._"
            }
        })
    else:
        for event in events:
            event_settings = get_event_settings(event['id'], settings)
            mode = event_settings.get("mode", "include")
            
            badge = get_mode_badge(mode)
            time_str = format_event_time(event)
            summary = event['summary']
            
            # Build the event row
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{badge}*  |  {time_str}\n*{summary}*"
                }
            })
            
            # Action buttons
            action_elements = [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✏️ Edit",
                        "emoji": True
                    },
                    "action_id": f"edit_event:{event['id']}",
                    "value": event['id']
                }
            ]
            
            # Mode toggle buttons (show options that aren't current)
            if mode == "include":
                action_elements.extend([
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👻 Placeholder",
                            "emoji": True
                        },
                        "action_id": f"set_placeholder:{event['id']}",
                        "value": event['id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚫 Skip",
                            "emoji": True
                        },
                        "action_id": f"set_skip:{event['id']}",
                        "value": event['id']
                    }
                ])
            elif mode == "placeholder":
                action_elements.extend([
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Include",
                            "emoji": True
                        },
                        "action_id": f"set_include:{event['id']}",
                        "value": event['id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚫 Skip",
                            "emoji": True
                        },
                        "action_id": f"set_skip:{event['id']}",
                        "value": event['id']
                    }
                ])
            elif mode == "skip":
                action_elements.extend([
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Include",
                            "emoji": True
                        },
                        "action_id": f"set_include:{event['id']}",
                        "value": event['id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👻 Placeholder",
                            "emoji": True
                        },
                        "action_id": f"set_placeholder:{event['id']}",
                        "value": event['id']
                    }
                ])
            
            blocks.append({
                "type": "actions",
                "elements": action_elements
            })
            
            blocks.append({
                "type": "divider"
            })
    
    # Back button
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "← Back to Menu",
                    "emoji": True
                },
                "action_id": "back_to_menu"
            }
        ]
    })
    
    return blocks
