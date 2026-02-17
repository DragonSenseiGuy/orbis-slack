"""
Event edit modal for Orbis.
"""

from typing import Dict, List
from datetime import datetime


def format_event_datetime(event: Dict) -> str:
    """Format event datetime for display."""
    start = event['start']
    end = event['end']
    
    if event['is_all_day']:
        start_str = start.strftime('%a %d %b') if isinstance(start, datetime) else str(start)
        return f"All day • {start_str}"
    
    start_str = start.strftime('%H:%M') if isinstance(start, datetime) else str(start)
    end_str = end.strftime('%H:%M') if isinstance(end, datetime) else str(end)
    day = start.strftime('%a %d %b') if isinstance(start, datetime) else ''
    
    return f"{start_str} – {end_str}, {day}"


def get_event_edit_modal(event: Dict, event_settings: Dict, global_settings: Dict) -> Dict:
    """
    Generate the modal view for editing event settings.
    
    Args:
        event: The calendar event dict
        event_settings: Current settings for this event
        global_settings: Global default settings
    
    Returns:
        Modal view dict for views.open
    """
    mode = event_settings.get("mode", "include")
    
    # Emoji values
    include_emoji = event_settings.get("emoji") or global_settings.get("default_emoji", ":calendar:")
    include_template = event_settings.get("text_template") or global_settings.get("default_template", "{event_name}")
    
    placeholder_emoji = event_settings.get("placeholder_emoji") or global_settings.get("placeholder_emoji", ":calendar:")
    placeholder_text = event_settings.get("placeholder_text") or global_settings.get("placeholder_text", "In a meeting")
    
    use_custom_placeholder = event_settings.get("placeholder_emoji") is not None or event_settings.get("placeholder_text") is not None
    
    # Preview text
    preview_text = include_template.replace("{event_name}", event['summary'])
    
    modal = {
        "type": "modal",
        "callback_id": f"save_event:{event['id']}",
        "title": {
            "type": "plain_text",
            "text": "Edit Event Settings",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "💾 Save",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Event:* {event['summary']}\n*Time:* {format_event_datetime(event)}"
                }
            },
            {
                "type": "divider"
            },
            # Mode selection
            {
                "type": "input",
                "block_id": "mode_block",
                "element": {
                    "type": "static_select",
                    "action_id": "mode_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select mode"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🟢 Include - Show real event name",
                                "emoji": True
                            },
                            "value": "include"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🔵 Placeholder - Show generic status",
                                "emoji": True
                            },
                            "value": "placeholder"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "⚫ Skip - Ignore this event",
                                "emoji": True
                            },
                            "value": "skip"
                        }
                    ],
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "🟢 Include - Show real event name" if mode == "include" else (
                                "🔵 Placeholder - Show generic status" if mode == "placeholder" else "⚫ Skip - Ignore this event"
                            ),
                            "emoji": True
                        },
                        "value": mode
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Mode",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            },
            # Include mode settings header
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*── If INCLUDE: Status Settings ───*"
                }
            },
            # Include emoji
            {
                "type": "input",
                "block_id": "include_emoji_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "include_emoji_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": ":calendar:"
                    },
                    "initial_value": include_emoji
                },
                "label": {
                    "type": "plain_text",
                    "text": "Emoji",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Format: :emoji_code: or just emoji_code"
                }
            },
            # Include text template
            {
                "type": "input",
                "block_id": "include_text_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "include_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "{event_name}"
                    },
                    "initial_value": include_template
                },
                "label": {
                    "type": "plain_text",
                    "text": "Status Text",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Use {event_name} to include the event title"
                }
            },
            # Preview
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_Preview: {include_emoji} {preview_text}_"
                }
            },
            {
                "type": "divider"
            },
            # Placeholder mode settings header
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*── If PLACEHOLDER: Custom Override ───*"
                }
            },
            # Use custom placeholder checkbox
            {
                "type": "input",
                "block_id": "custom_placeholder_block",
                "element": {
                    "type": "checkboxes",
                    "action_id": "custom_placeholder_checkbox",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Use custom placeholder (overrides global)",
                                "emoji": True
                            },
                            "value": "use_custom"
                        }
                    ]
                },
                "label": {
                    "type": "plain_text",
                    "text": "Custom Placeholder",
                    "emoji": True
                },
                "optional": True
            },
            # Placeholder emoji
            {
                "type": "input",
                "block_id": "placeholder_emoji_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "placeholder_emoji_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": global_settings.get("placeholder_emoji", ":calendar:")
                    },
                    "initial_value": placeholder_emoji
                },
                "label": {
                    "type": "plain_text",
                    "text": "Placeholder Emoji",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Leave empty to use global default"
                },
                "optional": True
            },
            # Placeholder text
            {
                "type": "input",
                "block_id": "placeholder_text_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "placeholder_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": global_settings.get("placeholder_text", "In a meeting")
                    },
                    "initial_value": placeholder_text
                },
                "label": {
                    "type": "plain_text",
                    "text": "Placeholder Text",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Leave empty to use global default"
                },
                "optional": True
            }
        ]
    }
    
    return modal
