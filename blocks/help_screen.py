"""
Help screen Block Kit UI for Orbis.
"""

from typing import Dict, List


def get_help_blocks() -> List[Dict]:
    """Generate the help screen Block Kit blocks."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "❓ Help & Commands",
                "emoji": True
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Commands:*\n"
                    "• `/calstatus` — Open the main menu\n"
                    "• DM: `menu` — Same as above\n"
                    "• DM: `sync` — Force a calendar sync\n"
                    "• DM: `status` — Show your current Slack status\n"
                    "• DM: `clear` — Manually clear your status\n"
                    "• DM: `help` — Show this help message"
                )
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*How it works:*\n"
                    "• The bot polls your Google Calendar every 60 seconds\n"
                    "• When an event starts, it sets your Slack status\n"
                    "• When it ends, your status is cleared automatically\n"
                    "• Use *View Upcoming Events* to control each event\n\n"
                    "*Event Modes:*\n"
                    "• 🟢 *Include* — Show the actual event name in your status\n"
                    "• 🔵 *Placeholder* — Show a generic status instead\n"
                    "• ⚫ *Skip* — Ignore this event completely"
                )
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
                        "text": "← Back to Menu",
                        "emoji": True
                    },
                    "action_id": "back_to_menu"
                }
            ]
        }
    ]
