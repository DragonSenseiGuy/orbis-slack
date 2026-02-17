"""
Main menu Block Kit UI for Orbis.
"""

from typing import Dict, List


def get_main_menu_blocks() -> List[Dict]:
    """Generate the main menu Block Kit blocks."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📅  Orbis - Calendar Status Bot",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "What would you like to do?"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 View Upcoming Events",
                        "emoji": True
                    },
                    "action_id": "view_events",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "⚙️ Global Settings",
                        "emoji": True
                    },
                    "action_id": "global_settings"
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔄 Sync Now",
                        "emoji": True
                    },
                    "action_id": "sync_now"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❓ Help",
                        "emoji": True
                    },
                    "action_id": "help"
                }
            ]
        }
    ]


def get_sync_confirmation() -> List[Dict]:
    """Confirmation message after sync."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "✅ *Sync complete!* Calendar checked and status updated if needed."
            }
        }
    ]
