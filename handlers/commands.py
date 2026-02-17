"""
Slash command handlers for Orbis.
"""

import os
from slack_bolt import Ack, Respond
from slack_sdk import WebClient

from blocks.main_menu import get_main_menu_blocks
from slack_status import get_bot_client

# Cached DM channel ID
_dm_channel_id: str = None

# Track last menu message timestamp per channel
_last_menu_ts: dict = {}


def get_dm_channel_id(client: WebClient, user_id: str) -> str:
    """Get or open the DM channel ID for the user."""
    global _dm_channel_id
    if _dm_channel_id:
        return _dm_channel_id
    
    response = client.conversations_open(users=[user_id])
    _dm_channel_id = response['channel']['id']
    return _dm_channel_id


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


def handle_calstatus_command(ack: Ack, command: dict, client: WebClient, respond: Respond):
    """Handle the /calstatus slash command."""
    ack()
    
    user_id = command['user_id']
    
    # Security check: only authorized user can use the bot
    if not is_authorized_user(user_id):
        respond(
            text="⛔ This bot is configured for a specific user. You are not authorized to use it.",
            response_type="ephemeral"
        )
        return
    
    # Send the main menu to the user's DM (deletes old one, posts at bottom)
    dm_channel = get_dm_channel_id(client, user_id)
    post_fresh_menu(client, dm_channel)
    
    # Confirm in the channel where command was used
    respond(
        text="📅 Check your DMs with @Cal Status Bot for the menu!",
        response_type="ephemeral"
    )
