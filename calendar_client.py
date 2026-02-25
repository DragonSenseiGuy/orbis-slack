"""
Google Calendar API wrapper for Orbis.
Handles OAuth2 flow and event fetching.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def _load_token_info() -> Optional[dict]:
    """Load Google OAuth token from env var or file."""
    token_json = os.getenv('GOOGLE_TOKEN_JSON')
    if token_json:
        return json.loads(token_json)
    
    token_file = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return json.load(f)
    return None


def _load_client_config() -> Optional[dict]:
    """Load Google OAuth client config from env var or file."""
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        return json.loads(creds_json)
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(credentials_file):
        with open(credentials_file, 'r') as f:
            return json.load(f)
    return None


def _save_token(creds: Credentials) -> None:
    """Save token to env-specified file (skipped when using env var)."""
    if os.getenv('GOOGLE_TOKEN_JSON'):
        return
    token_file = os.getenv('GOOGLE_TOKEN_FILE', 'token.json')
    with open(token_file, 'w') as f:
        json.dump(json.loads(creds.to_json()), f)


def get_credentials() -> Credentials:
    """
    Load or create credentials for Google Calendar API.
    Supports GOOGLE_TOKEN_JSON and GOOGLE_CREDENTIALS_JSON env vars,
    or falls back to token.json / credentials.json files.
    """
    creds = None

    # Load existing token if available
    token_info = _load_token_info()
    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # Refresh or create new credentials if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = _load_client_config()
            if not client_config:
                raise FileNotFoundError(
                    "Google credentials not found. Set GOOGLE_CREDENTIALS_JSON env var "
                    "or place credentials.json in the project root."
                )

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)

        _save_token(creds)

    return creds


def get_calendar_service():
    """Build and return Google Calendar API service."""
    creds = get_credentials()
    return build('calendar', 'v3', credentials=creds, cache_discovery=False)


def parse_event_time(time_str: str) -> datetime:
    """Parse Google Calendar event time string to datetime."""
    # Handle RFC3339 format (with timezone)
    if 'Z' in time_str:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    elif '+' in time_str or time_str.count('-') > 2:
        return datetime.fromisoformat(time_str)
    else:
        # Handle date-only format (all-day events)
        return datetime.fromisoformat(time_str)


def list_upcoming_events(hours_ahead: int, calendar_id: Optional[str] = None) -> List[Dict]:
    """
    Fetch upcoming events from Google Calendar.
    
    Args:
        hours_ahead: Number of hours to look ahead from now
        calendar_id: Google Calendar ID (default: from env or 'primary')
    
    Returns:
        List of event dicts with keys: id, summary, start, end, recurring_event_id, is_all_day
    """
    service = get_calendar_service()
    
    if calendar_id is None:
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
    
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(hours=hours_ahead)).isoformat() + 'Z'
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,  # Expand recurring events
            orderBy='startTime'
        ).execute()
        
        items = events_result.get('items', [])
        events = []
        
        for item in items:
            # Skip events without start time (e.g., some recurring event masters)
            if 'start' not in item:
                continue
            
            # Determine if it's an all-day event
            is_all_day = 'date' in item['start']
            
            # Get start and end times
            if is_all_day:
                start_str = item['start']['date']
                end_str = item['end']['date']
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
            else:
                start_str = item['start']['dateTime']
                end_str = item['end']['dateTime']
                start_dt = parse_event_time(start_str)
                end_dt = parse_event_time(end_str)
            
            # Build normalized event dict
            event = {
                'id': item['id'],
                'summary': item.get('summary', 'Untitled Event'),
                'start': start_dt,
                'end': end_dt,
                'start_str': start_str,
                'end_str': end_str,
                'recurring_event_id': item.get('recurringEventId'),
                'is_all_day': is_all_day,
                'description': item.get('description', ''),
                'location': item.get('location', '')
            }
            events.append(event)
        
        return events
    
    except HttpError as e:
        print(f"Google Calendar API error: {e}")
        return []


def get_currently_active_events(events: List[Dict]) -> List[Dict]:
    """
    Filter events to find those currently active (ongoing now).
    
    Returns:
        List of active events sorted by end time (soonest ending first)
    """
    now = datetime.now(timezone.utc)
    active = []
    
    for event in events:
        # For all-day events, check if today falls within the range
        if event['is_all_day']:
            # Adjust for timezone - treat as local all-day
            today = now.date()
            start_date = event['start'].date() if hasattr(event['start'], 'date') else event['start']
            end_date = event['end'].date() if hasattr(event['end'], 'date') else event['end']
            
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
            
            # All-day events end at midnight, so check if today is within range
            if start_date <= today < end_date:
                active.append(event)
        else:
            # Timed events
            start = event['start']
            end = event['end']
            
            # Handle timezone-aware comparison
            if start.tzinfo:
                # Convert now to the event's timezone for comparison
                now_aware = now.astimezone(start.tzinfo)
            else:
                # Event has no timezone, treat as UTC
                now_aware = now.replace(tzinfo=None)
                start = start.replace(tzinfo=None)
                end = end.replace(tzinfo=None)
            
            if start <= now_aware < end:
                active.append(event)
    
    # Sort by end time (soonest ending first)
    active.sort(key=lambda e: e['end'])
    return active
