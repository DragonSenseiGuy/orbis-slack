"""
Block actions and view submission handlers for Orbis.
"""

import os
import re
from slack_bolt import Ack
from slack_sdk import WebClient

from blocks.main_menu import get_main_menu_blocks, get_sync_confirmation
from blocks.help_screen import get_help_blocks
from blocks.event_list import get_event_blocks
from blocks.event_edit import get_event_edit_modal
from blocks.global_settings import get_global_settings_modal
from settings_store import (
    load_settings, get_event_settings, get_global_settings,
    save_event_settings, update_global_settings, get_event_base_id
)
import calendar_client
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
            pass
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


# ==================== Block Actions ====================

def handle_view_events(ack: Ack, body: dict, client: WebClient):
    """Handle 'View Upcoming Events' button."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    channel = body['channel']['id']
    message_ts = body['message']['ts']
    
    # Fetch events
    settings = load_settings()
    global_settings = settings.get("global", {})
    lookahead = global_settings.get("lookahead_hours", 24)
    max_events = global_settings.get("max_events", 10)
    
    try:
        events = calendar_client.list_upcoming_events(lookahead)
        events = events[:max_events]
        
        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=get_event_blocks(events),
            text=f"Upcoming Events (next {lookahead}h)"
        )
    except Exception as e:
        client.chat_postMessage(
            channel=channel,
            text=f"❌ Error fetching events: {str(e)}"
        )


def handle_global_settings(ack: Ack, body: dict, client: WebClient):
    """Handle 'Global Settings' button - opens modal."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    trigger_id = body['trigger_id']
    global_settings = get_global_settings()
    
    # Open the global settings modal
    client.views_open(
        trigger_id=trigger_id,
        view=get_global_settings_modal(global_settings)
    )


def handle_sync_now(ack: Ack, body: dict, client: WebClient):
    """Handle 'Sync Now' button."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    channel = body['channel']['id']
    
    success = scheduler.run_sync_now()
    
    # Show toast notification (if supported)
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


def handle_help(ack: Ack, body: dict, client: WebClient):
    """Handle 'Help' button."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    channel = body['channel']['id']
    message_ts = body['message']['ts']
    
    client.chat_update(
        channel=channel,
        ts=message_ts,
        blocks=get_help_blocks(),
        text="Help & Commands"
    )


def handle_back_to_menu(ack: Ack, body: dict, client: WebClient):
    """Handle 'Back to Menu' button - deletes current message, posts fresh menu at bottom."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    channel = body['channel']['id']
    message_ts = body['message']['ts']
    
    # Delete the current message (events/help list)
    try:
        client.chat_delete(channel=channel, ts=message_ts)
    except Exception:
        pass
    
    # Post fresh menu at the bottom
    post_fresh_menu(client, channel)


# ==================== Event Mode Toggles ====================

def handle_set_mode(ack: Ack, body: dict, client: WebClient, mode: str):
    """Generic handler for setting event mode (include/placeholder/skip)."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    action = body['actions'][0]
    event_id = action['value']
    channel = body['channel']['id']
    message_ts = body['message']['ts']
    
    # Get current settings and update mode
    settings = load_settings()
    event_settings = get_event_settings(event_id, settings)
    event_settings['mode'] = mode
    
    # Save settings (use base ID for recurring events)
    base_id = get_event_base_id(event_id)
    save_event_settings(base_id, event_settings)
    
    # Trigger immediate status sync since we changed settings
    scheduler.run_sync_now()
    
    # Refresh event list
    global_settings = settings.get("global", {})
    lookahead = global_settings.get("lookahead_hours", 24)
    max_events = global_settings.get("max_events", 10)
    
    try:
        events = calendar_client.list_upcoming_events(lookahead)
        events = events[:max_events]
        
        client.chat_update(
            channel=channel,
            ts=message_ts,
            blocks=get_event_blocks(events),
            text=f"Upcoming Events (next {lookahead}h)"
        )
        
        # Send a brief confirmation that status was updated
        client.chat_postMessage(
            channel=channel,
            text=f"✅ Status updated! Event set to *{mode.upper()}* mode."
        )
    except Exception as e:
        client.chat_postMessage(
            channel=channel,
            text=f"❌ Error refreshing events: {str(e)}"
        )


def handle_edit_event(ack: Ack, body: dict, client: WebClient):
    """Handle 'Edit' button for an event - opens modal."""
    ack()
    
    user_id = body['user']['id']
    if not is_authorized_user(user_id):
        return
    
    action = body['actions'][0]
    event_id = action['value']
    trigger_id = body['trigger_id']
    
    # Fetch event details from current events
    settings = load_settings()
    global_settings = settings.get("global", {})
    lookahead = global_settings.get("lookahead_hours", 24)
    
    events = calendar_client.list_upcoming_events(lookahead)
    event = next((e for e in events if e['id'] == event_id), None)
    
    if not event:
        # Try to find with base ID
        base_id = get_event_base_id(event_id)
        event = next((e for e in events if e['id'] == base_id), None)
    
    if not event:
        # Create a placeholder event for the modal
        event = {
            'id': event_id,
            'summary': 'Unknown Event',
            'start': None,
            'end': None,
            'is_all_day': False
        }
    
    event_settings = get_event_settings(event_id, settings)
    
    # Open the edit modal
    client.views_open(
        trigger_id=trigger_id,
        view=get_event_edit_modal(event, event_settings, global_settings)
    )


# ==================== View Submissions ====================

def handle_save_event(ack: Ack, body: dict, client: WebClient, view: dict):
    """Handle saving event settings from modal."""
    # Extract event ID from callback_id
    callback_id = view['callback_id']
    event_id = callback_id.split(':')[1]
    
    values = view['state']['values']
    
    # Get values from modal
    mode = values['mode_block']['mode_select']['selected_option']['value']
    include_emoji = values['include_emoji_block']['include_emoji_input']['value']
    include_text = values['include_text_block']['include_text_input']['value']
    
    # Placeholder settings
    placeholder_emoji_input = values.get('placeholder_emoji_block', {}).get('placeholder_emoji_input', {}).get('value', '')
    placeholder_text_input = values.get('placeholder_text_block', {}).get('placeholder_text_input', {}).get('value', '')
    custom_placeholder = values.get('custom_placeholder_block', {}).get('custom_placeholder_checkbox', {}).get('selected_options', [])
    use_custom_placeholder = len(custom_placeholder) > 0
    
    # Build event settings
    event_settings = {
        'mode': mode,
        'emoji': include_emoji,
        'text_template': include_text
    }
    
    # Only save placeholder overrides if checkbox is checked
    if use_custom_placeholder:
        if placeholder_emoji_input:
            event_settings['placeholder_emoji'] = placeholder_emoji_input
        if placeholder_text_input:
            event_settings['placeholder_text'] = placeholder_text_input
    
    # Save settings (use base ID for recurring events)
    base_id = get_event_base_id(event_id)
    save_event_settings(base_id, event_settings)
    
    # Trigger immediate status sync since we changed event settings
    scheduler.run_sync_now()
    
    # Acknowledge with no errors
    ack()


def handle_save_global_settings(ack: Ack, body: dict, client: WebClient, view: dict):
    """Handle saving global settings from modal."""
    values = view['state']['values']
    
    # Extract all values
    global_settings = {
        'default_emoji': values['default_emoji_block']['default_emoji_input']['value'],
        'default_template': values['default_template_block']['default_template_input']['value'],
        'placeholder_emoji': values['placeholder_emoji_block']['placeholder_emoji_input']['value'],
        'placeholder_text': values['placeholder_text_block']['placeholder_text_input']['value'],
        'lookahead_hours': int(values['lookahead_hours_block']['lookahead_hours_input']['value']),
        'max_events': int(values['max_events_block']['max_events_input']['value']),
        'poll_interval_seconds': int(values['poll_interval_block']['poll_interval_input']['value']),
        'auto_clear': values['auto_clear_block']['auto_clear_select']['selected_option']['value'] == 'true'
    }
    
    # Save settings
    update_global_settings(global_settings)
    
    # Restart scheduler if poll interval changed
    scheduler.restart_scheduler()
    
    # Trigger immediate status sync since settings changed
    scheduler.run_sync_now()
    
    # Acknowledge
    ack()


# ==================== Router ====================

def register_action_handlers(app):
    """Register all action handlers with the Slack app."""
    
    # Main menu buttons
    app.action("view_events")(handle_view_events)
    app.action("global_settings")(handle_global_settings)
    app.action("sync_now")(handle_sync_now)
    app.action("help")(handle_help)
    app.action("back_to_menu")(handle_back_to_menu)
    
    # Handle dynamic action IDs with regex patterns
    # Event mode toggles with event ID suffix
    @app.action(re.compile(r"^set_include:.+"))
    def handle_set_include_dynamic(ack, body, client, action, logger):
        logger.debug(f"Handling set_include for action: {action}")
        handle_set_mode(ack, body, client, "include")
    
    @app.action(re.compile(r"^set_placeholder:.+"))
    def handle_set_placeholder_dynamic(ack, body, client, action, logger):
        logger.debug(f"Handling set_placeholder for action: {action}")
        handle_set_mode(ack, body, client, "placeholder")
    
    @app.action(re.compile(r"^set_skip:.+"))
    def handle_set_skip_dynamic(ack, body, client, action, logger):
        logger.debug(f"Handling set_skip for action: {action}")
        handle_set_mode(ack, body, client, "skip")
    
    @app.action(re.compile(r"^edit_event:.+"))
    def handle_edit_event_dynamic(ack, body, client, action, logger):
        logger.debug(f"Handling edit_event for action: {action}")
        handle_edit_event(ack, body, client)
    
    # Modal submissions
    @app.view(re.compile(r"^save_event:.+"))
    def handle_save_event_dynamic(ack, body, client, view, logger):
        logger.debug(f"Handling save_event for view: {view.get('callback_id')}")
        handle_save_event(ack, body, client, view)
    
    @app.view("save_global_settings")
    def handle_save_global_settings_view(ack, body, client, view, logger):
        logger.debug("Handling save_global_settings")
        handle_save_global_settings(ack, body, client, view)
