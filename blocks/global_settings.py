"""
Global settings modal for Orbis.
"""

from typing import Dict


def get_global_settings_modal(global_settings: Dict) -> Dict:
    """
    Generate the modal view for editing global settings.
    
    Args:
        global_settings: Current global settings dict
    
    Returns:
        Modal view dict for views.open
    """
    return {
        "type": "modal",
        "callback_id": "save_global_settings",
        "title": {
            "type": "plain_text",
            "text": "⚙️ Global Settings",
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
            # Section: Status Defaults (Include mode)
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*── Status Defaults (Include mode) ───*"
                }
            },
            {
                "type": "input",
                "block_id": "default_emoji_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "default_emoji_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": ":calendar:"
                    },
                    "initial_value": global_settings.get("default_emoji", ":calendar:")
                },
                "label": {
                    "type": "plain_text",
                    "text": "Default Emoji",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "default_template_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "default_template_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "{event_name}"
                    },
                    "initial_value": global_settings.get("default_template", "{event_name}")
                },
                "label": {
                    "type": "plain_text",
                    "text": "Default Text Template",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Use {event_name} to include the event title"
                }
            },
            {
                "type": "divider"
            },
            # Section: Placeholder Defaults
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*── Placeholder Defaults ───*"
                }
            },
            {
                "type": "input",
                "block_id": "placeholder_emoji_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "placeholder_emoji_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": ":calendar:"
                    },
                    "initial_value": global_settings.get("placeholder_emoji", ":calendar:")
                },
                "label": {
                    "type": "plain_text",
                    "text": "Placeholder Emoji",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "placeholder_text_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "placeholder_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "In a meeting"
                    },
                    "initial_value": global_settings.get("placeholder_text", "In a meeting")
                },
                "label": {
                    "type": "plain_text",
                    "text": "Placeholder Text",
                    "emoji": True
                }
            },
            {
                "type": "divider"
            },
            # Section: Behaviour
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*── Behaviour ───*"
                }
            },
            {
                "type": "input",
                "block_id": "lookahead_hours_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "lookahead_hours_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "24"
                    },
                    "initial_value": str(global_settings.get("lookahead_hours", 24))
                },
                "label": {
                    "type": "plain_text",
                    "text": "Look-ahead window (hours)",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "max_events_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "max_events_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "10"
                    },
                    "initial_value": str(global_settings.get("max_events", 10))
                },
                "label": {
                    "type": "plain_text",
                    "text": "Max events shown",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "block_id": "poll_interval_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "poll_interval_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "60"
                    },
                    "initial_value": str(global_settings.get("poll_interval_seconds", 60))
                },
                "label": {
                    "type": "plain_text",
                    "text": "Poll interval (seconds)",
                    "emoji": True
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Changes will restart the scheduler"
                }
            },
            {
                "type": "input",
                "block_id": "auto_clear_block",
                "element": {
                    "type": "static_select",
                    "action_id": "auto_clear_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select"
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Yes - Clear when no events active",
                                "emoji": True
                            },
                            "value": "true"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "❌ No - Leave status unchanged",
                                "emoji": True
                            },
                            "value": "false"
                        }
                    ],
                    "initial_option": {
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Yes - Clear when no events active" if global_settings.get("auto_clear", True) else "❌ No - Leave status unchanged",
                            "emoji": True
                        },
                        "value": "true" if global_settings.get("auto_clear", True) else "false"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Auto-clear status",
                    "emoji": True
                }
            }
        ]
    }
