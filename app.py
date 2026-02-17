"""
Orbis - Slack Google Calendar Status Bot

A personal Slack status bot that mirrors Google Calendar integration
with full per-event control, customizable status text/emoji, 
placeholder support, and an entirely interactive interface.

Tech Stack:
- Python 3.11+
- Slack Bolt for Python (Socket Mode)
- Google Calendar API
- APScheduler for background polling

Auto-reload: Enabled - restarts on code changes
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Check if we should run with auto-reload
AUTO_RELOAD = os.getenv('AUTO_RELOAD', 'true').lower() == 'true'
WATCHED_EXTENSIONS = {'.py'}


def get_modified_times():
    """Get modification times of all Python files."""
    times = {}
    for root, dirs, files in os.walk('.'):
        # Skip hidden dirs, venv, and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', '__pycache__', 'env')]
        for file in files:
            if any(file.endswith(ext) for ext in WATCHED_EXTENSIONS):
                path = os.path.join(root, file)
                try:
                    times[path] = os.path.getmtime(path)
                except OSError:
                    pass
    return times


def run_with_reload():
    """Run the bot with auto-reload on file changes."""
    print("🔁 Auto-reload enabled. Watching for file changes...")
    print("   (Set AUTO_RELOAD=false to disable)\n")
    
    while True:
        # Start the bot process
        env = os.environ.copy()
        env['_ORBIS_MAIN'] = '1'  # Signal that this is the actual bot process
        
        process = subprocess.Popen(
            [sys.executable, __file__],
            env=env,
            cwd=os.getcwd()
        )
        
        # Watch for changes
        last_times = get_modified_times()
        
        while process.poll() is None:
            time.sleep(1)
            current_times = get_modified_times()
            
            # Check for modifications
            for path, mtime in current_times.items():
                if path not in last_times or last_times[path] != mtime:
                    print(f"\n📝 Detected change in {path}")
                    print("🔄 Restarting bot...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
            
            last_times = current_times
        
        # If process exited normally (not from reload), exit
        if process.returncode != 0 and process.returncode != -15:
            print(f"\nBot exited with code {process.returncode}")
            sys.exit(process.returncode)


def is_main_process():
    """Check if this is the main bot process (not the watcher)."""
    return os.getenv('_ORBIS_MAIN') == '1' or not AUTO_RELOAD


# Only run watcher in the parent process
if not is_main_process() and AUTO_RELOAD and __name__ == "__main__":
    run_with_reload()
    sys.exit(0)


# ========== Main Bot Code ==========

if is_main_process():
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    # Import handlers
    from handlers.commands import handle_calstatus_command
    from handlers.messages import handle_dm_message
    from handlers.actions import register_action_handlers
    import scheduler

    # Load environment variables
    load_dotenv()

    # Validate required environment variables
    def validate_env():
        """Check that all required environment variables are set."""
        required = [
            'SLACK_BOT_TOKEN',
            'SLACK_APP_TOKEN',
            'SLACK_USER_TOKEN',
            'SLACK_USER_ID'
        ]
        
        missing = []
        for var in required:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            print("ERROR: Missing required environment variables:")
            for var in missing:
                print(f"  - {var}")
            print("\nPlease set these in your .env file or environment.")
            print("\nNote: SLACK_USER_TOKEN (xoxp-*) is required for setting user status.")
            print("      You can get this from your Slack app settings under OAuth Tokens.")
            sys.exit(1)
        
        print("✓ Environment variables validated")

    # Initialize the Slack Bolt app
    app = App(token=os.getenv('SLACK_BOT_TOKEN'))

    # Register handlers
    @app.command("/calstatus")
    def calstatus_command(ack, command, client, respond):
        """Handle the /calstatus slash command."""
        handle_calstatus_command(ack, command, client, respond)

    @app.event("message")
    def dm_event(event, client, ack, logger):
        """Handle DM messages."""
        # Acknowledge immediately
        ack()
        
        # Only respond to direct messages (IM = instant message)
        channel_type = event.get('channel_type')
        if channel_type == 'im':
            logger.debug(f"Received DM from user {event.get('user')}: {event.get('text', '')[:50]}")
            try:
                handle_dm_message(event, client, lambda: None)
            except Exception as e:
                logger.error(f"Error handling DM: {e}")
                try:
                    client.chat_postMessage(
                        channel=event['channel'],
                        text=f"❌ Error processing your message: {str(e)}"
                    )
                except:
                    pass

    # Register block action handlers
    register_action_handlers(app)

    def main():
        """Main entry point for the application."""
        print("=" * 50)
        print("  Orbis - Calendar Status Bot")
        if AUTO_RELOAD:
            print("  🔁 Auto-reload enabled")
        print("=" * 50)
        
        # Validate environment
        validate_env()
        
        # Start the scheduler
        print("\nStarting scheduler...")
        scheduler.start_scheduler()
        
        # Start Socket Mode handler
        print("\nStarting Socket Mode handler...")
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        
        print("\n" + "=" * 50)
        print("✓ Bot is running! Use /calstatus in Slack to get started.")
        print("=" * 50 + "\n")
        
        try:
            handler.start()
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            scheduler.get_scheduler().shutdown(wait=False)
            print("Goodbye!")
            sys.exit(0)

    if __name__ == "__main__":
        main()
