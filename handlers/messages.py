"""
DM message handlers for Orbis.
"""

import os
from slack_bolt import Ack
from slack_sdk import WebClient

from blocks.main_menu import get_main_menu_blocks, get_sync_confirmation
from blocks.help_screen import get_help_blocks
from blocks.event_list import get_event_blocks
from settings_store import load_settings
import calendar_client
import slack_status
import scheduler

# Track last menu message timestamp per channel
_last_menu_ts: dict = {}


def is_authorized_user(user_id: str) -> bool:
    """Check if the user is the authorized user for this bot."""
    return user_id == os.getenv('SLACK_USER_ID')


def delete_previous_menu(client: WebClient, channel: str):
    """Delete the previous menu message so the new one appears at the bottom."""
    global _last_menu_ts
    if channel in _last_menu_ts:
        try:
            client.chat_delete(
                channel=channel,
                ts=_last_menu_ts[channel]
            )
        except Exception:
            pass  # Message might already be deleted or expired
        del _last_menu_ts[channel]


def post_fresh_menu(client: WebClient, channel: str) -> str:
    """Post a new menu and track its timestamp."""
    global _last_menu_ts
    
    # Delete old menu first
    delete_previous_menu(client, channel)
    
    # Post new menu
    response = client.chat_postMessage(
        channel=channel,
        blocks=get_main_menu_blocks(),
        text="Orbis - Calendar Status Bot Main Menu"
    )
    
    # Track the new message timestamp
    _last_menu_ts[channel] = response['ts']
    return response['ts']


def handle_dm_message(event: dict, client: WebClient, ack: Ack):
    """Handle incoming DM messages."""
    # Note: ack() is called by the caller (app.py) to satisfy Slack's 3-second requirement
    
    user_id = event['user']
    
    # Security check: only authorized user can use the bot
    if not is_authorized_user(user_id):
        client.chat_postMessage(
            channel=event['channel'],
            text="⛔ This bot is configured for a specific user. You are not authorized to use it."
        )
        return
    
    text = event.get('text', '').lower().strip()
    channel = event['channel']
    
    # Route based on message content
    if text in ['menu', 'start', 'hi', 'hello', 'hey']:
        # Post fresh menu at the bottom (deletes old one first)
        post_fresh_menu(client, channel)
    
    elif text == 'sync':
        success = scheduler.run_sync_now()
        if success:
            client.chat_postMessage(
                channel=channel,
                blocks=get_sync_confirmation(),
                text="Sync complete!"
            )
        else:
            client.chat_postMessage(
                channel=channel,
                text="❌ Sync failed. Check logs for details."
            )
    
    elif text == 'status':
        current = slack_status.get_current_status()
        emoji = current.get('status_emoji', '')
        text_status = current.get('status_text', '')
        
        if emoji or text_status:
            status_msg = f"Your current status: {emoji} {text_status}"
        else:
            status_msg = "Your status is currently empty (no status set)."
        
        client.chat_postMessage(
            channel=channel,
            text=status_msg
        )
    
    elif text == 'clear':
        success = slack_status.clear_status(force=True)
        if success:
            client.chat_postMessage(
                channel=channel,
                text="✅ Your Slack status has been cleared."
            )
        else:
            client.chat_postMessage(
                channel=channel,
                text="❌ Failed to clear status. Check logs for details."
            )
    
    elif text in ['events', 'upcoming', 'list']:
        # Show upcoming events
        settings = load_settings()
        global_settings = settings.get("global", {})
        lookahead = global_settings.get("lookahead_hours", 24)
        max_events = global_settings.get("max_events", 10)
        
        try:
            events = calendar_client.list_upcoming_events(lookahead)
            events = events[:max_events]
            
            client.chat_postMessage(
                channel=channel,
                blocks=get_event_blocks(events),
                text=f"Upcoming Events (next {lookahead}h)"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=channel,
                text=f"❌ Error fetching events: {str(e)}"
            )
    
    elif text == 'help':
        client.chat_postMessage(
            channel=channel,
            blocks=get_help_blocks(),
            text="Help & Commands"
        )
    
    else:
        # Unknown command - show help
        client.chat_postMessage(
            channel=channel,
            text=(
                f"I didn't understand '{text}'. Try one of these:\n"
                "• `menu` — Open the main menu\n"
                "• `sync` — Force a calendar sync\n"
                "• `status` — Show your current status\n"
                "• `clear` — Clear your status\n"
                "• `events` — View upcoming events\n"
                "• `help` — Show all commands"
            )
        )
