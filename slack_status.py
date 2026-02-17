"""
Slack user status management for Orbis.
Uses user token (xoxp-*) to set/clear status.
"""

import os
from datetime import datetime
from typing import Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Track the last status we set to avoid redundant API calls
_last_set_status: Optional[Dict] = None


def get_user_client() -> WebClient:
    """Get Slack WebClient with user token for profile operations."""
    user_token = os.getenv('SLACK_USER_TOKEN')
    if not user_token:
        raise ValueError(
            "SLACK_USER_TOKEN not found in environment. "
            "A user token (xoxp-*) with users.profile:write scope is required to set status."
        )
    return WebClient(token=user_token)


def get_bot_client() -> WebClient:
    """Get Slack WebClient with bot token."""
    bot_token = os.getenv('SLACK_BOT_TOKEN')
    if not bot_token:
        raise ValueError("SLACK_BOT_TOKEN not found in environment.")
    return WebClient(token=bot_token)


def format_expiry_timestamp(expiry_dt: datetime) -> int:
    """Convert datetime to Unix timestamp for Slack status."""
    if expiry_dt.tzinfo:
        return int(expiry_dt.timestamp())
    # Assume UTC if no timezone
    return int(expiry_dt.replace(tzinfo=datetime.timezone.utc).timestamp())


def set_status(emoji: str, text: str, expiry_ts: int, force: bool = False) -> bool:
    """
    Set Slack user status.
    
    Args:
        emoji: Emoji code like ":calendar:" or plain "calendar"
        text: Status text
        expiry_ts: Unix timestamp when status should expire
        force: If True, skip the cache check and always set
    
    Returns:
        True if successful, False otherwise
    """
    global _last_set_status
    
    # Normalize emoji format
    if not emoji.startswith(':'):
        emoji = f":{emoji}:"
    
    # Check if we're setting the same status (avoid redundant calls)
    new_status = {
        'status_emoji': emoji,
        'status_text': text,
        'status_expiration': expiry_ts
    }
    
    if not force and _last_set_status == new_status:
        print(f"[Orbis] Status unchanged, skipping API call: {text}")
        return True
    
    client = get_user_client()
    user_id = os.getenv('SLACK_USER_ID')
    
    try:
        response = client.users_profile_set(
            user=user_id,
            profile={
                "status_emoji": emoji,
                "status_text": text,
                "status_expiration": expiry_ts
            }
        )
        
        if response['ok']:
            _last_set_status = new_status
            print(f"[Orbis] Status set: {emoji} {text} (expires at {expiry_ts})")
            return True
        return False
    
    except SlackApiError as e:
        print(f"[Orbis] Error setting status: {e.response['error']}")
        return False


def clear_status(force: bool = False) -> bool:
    """
    Clear Slack user status (set to empty).
    
    Args:
        force: If True, skip the cache check and always clear
    
    Returns:
        True if successful, False otherwise
    """
    global _last_set_status
    
    # Check if already cleared (unless forcing)
    if not force and _last_set_status is None:
        # Double-check by fetching current status
        current = get_current_status()
        if not current.get('status_text') and not current.get('status_emoji'):
            print("[Orbis] Status already clear, skipping API call")
            return True
        # Status exists but we don't have it cached, proceed to clear
    
    client = get_user_client()
    user_id = os.getenv('SLACK_USER_ID')
    
    try:
        response = client.users_profile_set(
            user=user_id,
            profile={
                "status_emoji": "",
                "status_text": "",
                "status_expiration": 0
            }
        )
        
        if response['ok']:
            _last_set_status = None
            print("[Orbis] Status cleared")
            return True
        return False
    
    except SlackApiError as e:
        print(f"[Orbis] Error clearing status: {e.response['error']}")
        return False


def get_current_status() -> Dict:
    """
    Get current Slack user status.
    
    Returns:
        Dict with status_emoji, status_text, status_expiration
    """
    client = get_user_client()
    user_id = os.getenv('SLACK_USER_ID')
    
    try:
        response = client.users_profile_get(user=user_id)
        profile = response['profile']
        return {
            'status_emoji': profile.get('status_emoji', ''),
            'status_text': profile.get('status_text', ''),
            'status_expiration': profile.get('status_expiration', 0)
        }
    except SlackApiError as e:
        print(f"[Orbis] Error getting status: {e.response['error']}")
        return {'status_emoji': '', 'status_text': '', 'status_expiration': 0}


def was_set_by_bot(current_status: Dict) -> bool:
    """
    Check if the current status matches what we last set.
    Used to determine if we should clear it.
    """
    if _last_set_status is None:
        return False
    
    return (
        current_status.get('status_emoji') == _last_set_status['status_emoji'] and
        current_status.get('status_text') == _last_set_status['status_text']
    )
