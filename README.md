# Telegram Management Bot

A powerful Telegram bot built with Pyrogram that provides group management features and music playing capabilities.

## Features

### Group Management
- User administration (ban, kick, mute, unmute)
- Welcome messages for new members
- Anti-spam protection
- Message filtering and auto-moderation
- Group settings management
- User notes and warnings

### Music Player
- Play music from YouTube links
- Search and play songs by name
- Queue management
- Volume control
- Skip, pause, resume functionality

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   BOT_TOKEN=your_bot_token
   ```
   Get your API credentials from [my.telegram.org](https://my.telegram.org)
   
4. Run the bot:
   ```
   python main.py
   ```

## Commands

### Group Management
- `/ban` - Ban a user
- `/unban` - Unban a user
- `/kick` - Kick a user
- `/mute` - Mute a user
- `/unmute` - Unmute a user
- `/warn` - Warn a user
- `/notes` - List saved notes
- `/save` - Save a note
- `/filter` - Add a filter
- `/filters` - List all filters
- `/welcome` - Set welcome message

### Music Player
- `/play` - Play a song by name or URL
- `/skip` - Skip the current song
- `/pause` - Pause the current song
- `/resume` - Resume playback
- `/stop` - Stop playback
- `/queue` - Show the current queue
- `/now` - Show the currently playing song

## License

MIT 