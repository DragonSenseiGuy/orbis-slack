# Orbis - Slack Google Calendar Status Bot

A personal Slack status bot that mirrors the Google Calendar integration for Slack — but with full per-event control, customizable status text/emoji, placeholder support, and an entirely interactive interface via bot DM or slash command.

**Single-user only.** All configuration and interaction happens through Slack itself (no web UI needed).

## Features

- 🔗 **Google Calendar Integration** - Automatically syncs with your Google Calendar
- 🎛️ **Per-Event Control** - Configure each event individually (Include / Placeholder / Skip)
- 📝 **Custom Status Templates** - Use `{event_name}` placeholders in status text
- 🔵 **Placeholder Mode** - Hide sensitive event names with generic status messages
- ⚡ **Real-time Sync** - Background polling every 60 seconds (configurable)
- 💬 **Interactive UI** - Full Block Kit interface with modals and buttons
- 🔒 **Single-User Security** - Only authorized user can access the bot

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: [Slack Bolt for Python](https://slack.dev/bolt-python/) (Socket Mode)
- **Calendar**: Google Calendar API
- **Scheduler**: APScheduler (background polling)
- **Persistence**: Local JSON file (`settings.json`)
- **Config**: `.env` file with `python-dotenv`

## Quick Start

### 1. Clone and Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Slack Tokens (from https://api.slack.com/apps)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...          # For Socket Mode
SLACK_USER_TOKEN=xoxp-...         # Required for setting user status
SLACK_USER_ID=U0123456789         # Your Slack user ID

# Google Calendar API
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GOOGLE_CALENDAR_ID=primary

# Bot Settings
POLL_INTERVAL_SECONDS=60
```

### 3. Setup Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google Calendar API
4. Go to Credentials → Create Credentials → OAuth client ID
5. Download the JSON and save as `credentials.json` in the project root

**Important**: When first running the bot, it will open a browser for OAuth authentication. After that, tokens are stored in `token.json`.

### 4. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "Orbis" (or whatever you prefer)
4. Use the manifest below or configure manually:

```yaml
display_information:
  name: Orbis
  description: Personal calendar-based Slack status
  background_color: "#4A154B"

features:
  bot_user:
    display_name: Orbis
    always_online: false
  slash_commands:
    - command: /calstatus
      url: https://unused.com  # Socket Mode ignores this
      description: Manage your calendar-based Slack status
      should_escape: false

oauth_config:
  scopes:
    bot:
      - chat:write
      - commands
      - im:history
      - im:write
    user:
      - users.profile:write

settings:
  socket_mode_enabled: true
  event_subscriptions:
    bot_events:
      - message.im
```

5. Install the app to your workspace
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`) → `SLACK_BOT_TOKEN`
7. Copy the **App-Level Token** (starts with `xapp-`) → `SLACK_APP_TOKEN`
8. Go to OAuth & Permissions, scroll to **User Token Scopes**, add `users.profile:write`
9. Reinstall the app, then copy the **User OAuth Token** (starts with `xoxp-`) → `SLACK_USER_TOKEN`

### 5. Find Your Slack User ID

1. In Slack, click your profile picture → Profile
2. Click the "..." menu → Copy member ID
3. Paste into `SLACK_USER_ID` in `.env`

### 6. Run the Bot

```bash
python app.py
```

The bot will start in Socket Mode and begin polling your calendar.

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `/calstatus` | Open the main menu |
| DM: `menu` | Same as above |
| DM: `sync` | Force a calendar sync |
| DM: `status` | Show your current Slack status |
| DM: `clear` | Manually clear your status |
| DM: `help` | Show all commands |

### Event Modes

Each calendar event can be configured in three ways:

| Mode | Badge | Description |
|------|-------|-------------|
| **Include** | 🟢 | Show the actual event name in your status |
| **Placeholder** | 🔵 | Show a generic status instead (e.g., "In a meeting") |
| **Skip** | ⚫ | Ignore this event completely |

### Default Settings

On first encounter of an event, the bot defaults to **Include** mode with these defaults:

- **Default Emoji**: `:calendar:`
- **Default Template**: `{event_name}`
- **Placeholder Emoji**: `:calendar:`
- **Placeholder Text**: `In a meeting`

These are fully configurable in Global Settings.

### Status Template Variables

Use `{event_name}` in your status templates:

| Template | Result |
|----------|--------|
| `{event_name}` | "Design Review" |
| `In a meeting: {event_name}` | "In a meeting: Design Review" |
| `Busy` | "Busy" |

## Project Structure

```
slack-gcal-bot/
├── .env                      # Environment variables (gitignored)
├── .env.example              # Example environment file
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── credentials.json          # Google OAuth client secrets (gitignored)
├── token.json                # Google OAuth token (auto-created, gitignored)
├── settings.json             # Bot settings (auto-created, gitignored)
├── app.py                    # Entry point - starts Bolt app + scheduler
├── calendar_client.py        # Google Calendar API wrapper
├── slack_status.py           # Slack profile/status API calls
├── scheduler.py              # APScheduler job: poll + update status
├── settings_store.py         # Read/write settings.json
├── blocks/                   # Block Kit UI components
│   ├── __init__.py
│   ├── main_menu.py          # Main menu screen
│   ├── event_list.py         # Upcoming events list
│   ├── event_edit.py         # Event edit modal
│   ├── global_settings.py    # Global settings modal
│   └── help_screen.py        # Help screen
└── handlers/                 # Slack event handlers
    ├── __init__.py
    ├── commands.py           # Slash command handler
    ├── messages.py             # DM message handler
    └── actions.py              # Block actions + view submissions
```

## settings.json Schema

```json
{
  "global": {
    "default_emoji": ":calendar:",
    "default_template": "{event_name}",
    "placeholder_emoji": ":calendar:",
    "placeholder_text": "In a meeting",
    "lookahead_hours": 24,
    "max_events": 10,
    "auto_clear": true,
    "poll_interval_seconds": 60
  },
  "events": {
    "<google_event_id>": {
      "mode": "include",
      "emoji": ":calendar:",
      "text_template": "In a meeting: {event_name}",
      "placeholder_emoji": null,
      "placeholder_text": null
    }
  }
}
```

**Note on Recurring Events**: For recurring events, the base ID (without the datetime suffix) is used so settings apply to all instances. Per-instance overrides are supported.

## Scheduler Logic

Every `POLL_INTERVAL_SECONDS`:

1. Fetch events from Google Calendar for `now → now+lookahead_hours`
2. Find currently active events
3. Select the soonest-ending active event (respecting `skip` mode)
4. If `include` mode: Set status with event name from template
5. If `placeholder` mode: Set status with placeholder text/emoji
6. If `skip` mode or no active events: Clear status (if `auto_clear` enabled)

## Security & Guard Rails

- **Single-user enforcement**: All handlers check `user_id == SLACK_USER_ID`
- **Token scopes**: Bot token for messaging, User token for status updates
- **Gitignored files**: `.env`, `credentials.json`, `token.json`, `settings.json`
- **No public URL**: Uses Socket Mode for local/self-hosted operation

## Troubleshooting

### Bot responds but doesn't set status

Make sure you have:
1. `SLACK_USER_TOKEN` set (the `xoxp-*` user token, not bot token)
2. `users.profile:write` scope added to User Token Scopes
3. The app reinstalled after adding user scopes

### Google Calendar authentication fails

1. Delete `token.json`
2. Run the bot again - it will prompt for browser authentication

### Events not showing up

- Check `GOOGLE_CALENDAR_ID` - use `primary` for your main calendar or a specific ID
- Verify Google Calendar API is enabled in Cloud Console
- Check that `credentials.json` is present

### Schedule changes not taking effect

- Run `sync` command to force immediate sync
- Check `settings.json` to verify your event overrides

## License

MIT License - Feel free to use and modify for personal use.

## Contributing

This is a personal bot project. Feel free to fork and customize for your needs!
