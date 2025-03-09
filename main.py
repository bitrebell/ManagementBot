import os
import logging
import re
import time
from collections import defaultdict
from dotenv import load_dotenv
from pyrogram import Client, idle, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from bot.database import notes_db, filters_db, settings_db
from bot.utils import is_admin, is_bot_admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bot configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    logger.error("Please set the required environment variables in the .env file")
    exit(1)

# Initialize the bot
app = Client(
    "management_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Basic commands
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    """Handle the /start command"""
    # Get bot info
    bot_info = await client.get_me()
    
    # Create welcome message
    welcome_text = f"""
Hello {message.from_user.mention}! 👋

I'm **{bot_info.first_name}**, a powerful group management bot.

Use /help to see the list of available commands.
"""
    
    # Create keyboard with buttons
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true"),
                InlineKeyboardButton("📚 Help", callback_data="help_main")
            ],
            [
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/yourusername"),
                InlineKeyboardButton("🌐 Support", url="https://t.me/yoursupportgroup")
            ]
        ]
    )
    
    # Send welcome message with keyboard
    await message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "**Available Commands:**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/ping - Check if the bot is online\n\n"
        "**Notes Module:**\n"
        "/save [name] [content] - Save a note\n"
        "/get [name] - Get a note\n"
        "/notes - List all saved notes\n"
        "/clear [name] - Delete a note\n"
        "/clearall - Delete all notes (admin only)\n\n"
        "**Filters Module:**\n"
        "/filter [keyword] [reply message] - Add a filter\n"
        "/filters - List all filters\n"
        "/stop [keyword] - Remove a filter\n"
        "/stopall - Remove all filters\n\n"
        "**Anti-Flood Module:**\n"
        "/setflood [number] - Set the number of messages allowed in a time frame\n"
        "/setfloodtime [seconds] - Set the time frame for flood detection\n"
        "/flood - Show current flood settings\n"
        "/flood off - Disable flood protection\n"
        "/flood on - Enable flood protection\n\n"
        "You can also use #[name] to get a note."
    )

@app.on_message(filters.command("ping"))
async def ping_command(client, message: Message):
    await message.reply_text("Pong!")

@app.on_callback_query(filters.regex(r"^help_(.+)"))
async def help_callback(client, callback_query: CallbackQuery):
    """Handle help callbacks"""
    await callback_query.answer()
    
    # Show main help menu
    await callback_query.message.edit_text(
        "**Available Commands:**\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/ping - Check if the bot is online\n\n"
        "**Notes Module:**\n"
        "/save [name] [content] - Save a note\n"
        "/get [name] - Get a note\n"
        "/notes - List all saved notes\n"
        "/clear [name] - Delete a note\n"
        "/clearall - Delete all notes (admin only)\n\n"
        "**Filters Module:**\n"
        "/filter [keyword] [reply message] - Add a filter\n"
        "/filters - List all filters\n"
        "/stop [keyword] - Remove a filter\n"
        "/stopall - Remove all filters\n\n"
        "**Anti-Flood Module:**\n"
        "/setflood [number] - Set the number of messages allowed in a time frame\n"
        "/setfloodtime [seconds] - Set the time frame for flood detection\n"
        "/flood - Show current flood settings\n"
        "/flood off - Disable flood protection\n"
        "/flood on - Enable flood protection",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="help_back")]]
        )
    )

# Notes Module

# Save note handler
@app.on_message(filters.command("save") & filters.group)
async def save_note(client, message: Message):
    """Save a note"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to save notes!")
        return
    
    # Check if command has enough arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a name for the note!")
        return
    
    # Get note name
    note_name = message.command[1].lower()
    
    # Check if note has content
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply_text("Please provide content for the note or reply to a message!")
        return
    
    # Get note content
    if message.reply_to_message:
        if message.reply_to_message.text:
            note_content = message.reply_to_message.text
        elif message.reply_to_message.caption:
            note_content = message.reply_to_message.caption
        else:
            await message.reply_text("I can only save text messages as notes!")
            return
    else:
        note_content = message.text.split(None, 2)[2]
    
    # Save note
    notes_db.set(f"{chat_id}_{note_name}", note_content)
    
    await message.reply_text(f"Note '{note_name}' saved successfully!")

# Get note handler
@app.on_message(filters.command("get") & filters.group)
async def get_note(client, message: Message):
    """Get a note"""
    chat_id = str(message.chat.id)
    
    # Check if command has enough arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a name for the note!")
        return
    
    # Get note name
    note_name = message.command[1].lower()
    
    # Get note content
    note_content = notes_db.get(f"{chat_id}_{note_name}")
    
    if note_content:
        await message.reply_text(note_content)
    else:
        await message.reply_text(f"Note '{note_name}' not found!")

# List notes handler
@app.on_message(filters.command("notes") & filters.group)
async def list_notes(client, message: Message):
    """List all saved notes"""
    chat_id = str(message.chat.id)
    
    # Get all notes for this chat
    notes = []
    for key in notes_db.list_keys():
        if key.startswith(f"{chat_id}_"):
            note_name = key.replace(f"{chat_id}_", "")
            notes.append(note_name)
    
    if notes:
        notes_text = "**Saved Notes:**\n\n"
        for note in sorted(notes):
            notes_text += f"- `{note}`\n"
        
        notes_text += "\nYou can get a note by using `/get notename` or `#notename`"
        
        await message.reply_text(notes_text)
    else:
        await message.reply_text("No notes saved in this chat!")

# Clear note handler
@app.on_message(filters.command("clear") & filters.group)
async def clear_note(client, message: Message):
    """Delete a note"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to delete notes!")
        return
    
    # Check if command has enough arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a name for the note to delete!")
        return
    
    # Get note name
    note_name = message.command[1].lower()
    
    # Check if note exists
    if not notes_db.contains(f"{chat_id}_{note_name}"):
        await message.reply_text(f"Note '{note_name}' not found!")
        return
    
    # Delete note
    notes_db.delete(f"{chat_id}_{note_name}")
    
    await message.reply_text(f"Note '{note_name}' deleted successfully!")

# Clear all notes handler
@app.on_message(filters.command("clearall") & filters.group)
async def clear_all_notes(client, message: Message):
    """Delete all notes"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to delete all notes!")
        return
    
    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes", callback_data=f"clearallnotes_{chat_id}_confirm"),
                InlineKeyboardButton("No", callback_data=f"clearallnotes_{chat_id}_cancel")
            ]
        ]
    )
    
    await message.reply_text(
        "Are you sure you want to delete ALL notes in this chat? This action cannot be undone!",
        reply_markup=keyboard
    )

# Clear all notes callback handler
@app.on_callback_query(filters.regex(r"^clearallnotes_(.+)_(confirm|cancel)"))
async def clear_all_notes_callback(client, callback_query: CallbackQuery):
    """Handle clear all notes confirmation"""
    # Get chat ID and action from callback data
    data = callback_query.data.split("_")
    chat_id = data[1]
    action = data[2]
    
    # Check if user is admin
    if not await is_admin(callback_query.message, callback_query.from_user.id):
        await callback_query.answer("You need to be an admin to delete all notes!", show_alert=True)
        return
    
    # Handle cancel action
    if action == "cancel":
        await callback_query.message.edit_text("Cancelled. Notes were not deleted.")
        await callback_query.answer()
        return
    
    # Handle confirm action
    if action == "confirm":
        # Get all notes for this chat
        deleted_count = 0
        for key in notes_db.list_keys():
            if key.startswith(f"{chat_id}_"):
                notes_db.delete(key)
                deleted_count += 1
        
        await callback_query.message.edit_text(f"Deleted {deleted_count} notes from this chat!")
        await callback_query.answer()
        return

# Filters Module

# Add filter handler
@app.on_message(filters.command("filter") & filters.group)
async def add_filter(client, message: Message):
    """Add a filter"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to add filters!")
        return
    
    # Check if command has enough arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a keyword for the filter!")
        return
    
    # Get filter keyword
    keyword = message.command[1].lower()
    
    # Check if filter has content
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply_text("Please provide content for the filter or reply to a message!")
        return
    
    # Get filter content
    if message.reply_to_message:
        if message.reply_to_message.text:
            filter_content = message.reply_to_message.text
        elif message.reply_to_message.caption:
            filter_content = message.reply_to_message.caption
        else:
            await message.reply_text("I can only save text messages as filters!")
            return
    else:
        filter_content = message.text.split(None, 2)[2]
    
    # Save filter
    filters_db.set(f"{chat_id}_{keyword}", filter_content)
    
    await message.reply_text(f"Filter for '{keyword}' added successfully!")

# List filters handler
@app.on_message(filters.command("filters") & filters.group)
async def list_filters(client, message: Message):
    """List all filters"""
    chat_id = str(message.chat.id)
    
    # Get all filters for this chat
    chat_filters = []
    for key in filters_db.list_keys():
        if key.startswith(f"{chat_id}_"):
            filter_name = key.replace(f"{chat_id}_", "")
            chat_filters.append(filter_name)
    
    if chat_filters:
        filters_text = "**Active Filters:**\n\n"
        for filter_name in sorted(chat_filters):
            filters_text += f"- `{filter_name}`\n"
        
        await message.reply_text(filters_text)
    else:
        await message.reply_text("No filters active in this chat!")

# Remove filter handler
@app.on_message(filters.command("stop") & filters.group)
async def remove_filter(client, message: Message):
    """Remove a filter"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to remove filters!")
        return
    
    # Check if command has enough arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a keyword for the filter to remove!")
        return
    
    # Get filter keyword
    keyword = message.command[1].lower()
    
    # Check if filter exists
    if not filters_db.contains(f"{chat_id}_{keyword}"):
        await message.reply_text(f"Filter '{keyword}' not found!")
        return
    
    # Remove filter
    filters_db.delete(f"{chat_id}_{keyword}")
    
    await message.reply_text(f"Filter '{keyword}' removed successfully!")

# Remove all filters handler
@app.on_message(filters.command("stopall") & filters.group)
async def remove_all_filters(client, message: Message):
    """Remove all filters"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to remove all filters!")
        return
    
    # Create confirmation keyboard
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Yes", callback_data=f"stopallfilters_{chat_id}_confirm"),
                InlineKeyboardButton("No", callback_data=f"stopallfilters_{chat_id}_cancel")
            ]
        ]
    )
    
    await message.reply_text(
        "Are you sure you want to remove ALL filters in this chat? This action cannot be undone!",
        reply_markup=keyboard
    )

# Remove all filters callback handler
@app.on_callback_query(filters.regex(r"^stopallfilters_(.+)_(confirm|cancel)"))
async def remove_all_filters_callback(client, callback_query: CallbackQuery):
    """Handle remove all filters confirmation"""
    # Get chat ID and action from callback data
    data = callback_query.data.split("_")
    chat_id = data[1]
    action = data[2]
    
    # Check if user is admin
    if not await is_admin(callback_query.message, callback_query.from_user.id):
        await callback_query.answer("You need to be an admin to remove all filters!", show_alert=True)
        return
    
    # Handle cancel action
    if action == "cancel":
        await callback_query.message.edit_text("Cancelled. Filters were not removed.")
        await callback_query.answer()
        return
    
    # Handle confirm action
    if action == "confirm":
        # Get all filters for this chat
        removed_count = 0
        for key in filters_db.list_keys():
            if key.startswith(f"{chat_id}_"):
                filters_db.delete(key)
                removed_count += 1
        
        await callback_query.message.edit_text(f"Removed {removed_count} filters from this chat!")
        await callback_query.answer()
        return

# Filter message handler
@app.on_message(filters.group & filters.text, group=2)
async def handle_filters(client, message: Message):
    """Check if message contains filter keywords and reply with filter content"""
    # Skip commands
    if message.text.startswith('/'):
        return
        
    chat_id = str(message.chat.id)
    
    # Handle hashtag notes
    if message.text.startswith('#'):
        # Get note name from hashtag
        match = re.match(r"^#([a-zA-Z0-9_]+)", message.text)
        if match:
            note_name = match.group(1).lower()
            
            # Get note content
            note_content = notes_db.get(f"{chat_id}_{note_name}")
            
            if note_content:
                await message.reply_text(note_content)
        return
    
    # Get all filters for this chat
    chat_filters = {}
    for key in filters_db.list_keys():
        if key.startswith(f"{chat_id}_"):
            filter_name = key.replace(f"{chat_id}_", "")
            filter_content = filters_db.get(key)
            chat_filters[filter_name] = filter_content
    
    # Check if message contains any filter keywords
    for keyword, content in chat_filters.items():
        pattern = r'(\W|^)' + re.escape(keyword) + r'(\W|$)'
        if re.search(pattern, message.text.lower()):
            await message.reply_text(content)
            break  # Only reply with the first matching filter

# Anti-Flood Module

# Default flood settings
DEFAULT_FLOOD_LIMIT = 5  # 5 messages
DEFAULT_FLOOD_TIME = 5   # 5 seconds
DEFAULT_FLOOD_MODE = "mute"  # Options: mute, kick, ban

# Store user message counts
FLOOD_USERS = defaultdict(lambda: {"count": 0, "last_msg_time": 0})

# Flood detection handler
@app.on_message(filters.group & ~filters.service & filters.text, group=1)
async def check_flood(client, message: Message):
    """Check for message flooding"""
    chat_id = str(message.chat.id)
    user_id = message.from_user.id
    
    # Skip if user is admin
    if await is_admin(message, user_id):
        return
    
    # Check if flood protection is enabled
    flood_enabled = settings_db.get(f"{chat_id}_flood_enabled", True)
    if not flood_enabled:
        return
    
    # Get flood settings
    flood_limit = settings_db.get(f"{chat_id}_flood_limit", DEFAULT_FLOOD_LIMIT)
    flood_time = settings_db.get(f"{chat_id}_flood_time", DEFAULT_FLOOD_TIME)
    flood_mode = settings_db.get(f"{chat_id}_flood_mode", DEFAULT_FLOOD_MODE)
    
    # Get current time
    current_time = time.time()
    
    # Get user's flood data
    user_key = f"{chat_id}_{user_id}"
    user_data = FLOOD_USERS[user_key]
    
    # Reset count if time frame has passed
    if current_time - user_data["last_msg_time"] > flood_time:
        user_data["count"] = 0
    
    # Update user's flood data
    user_data["count"] += 1
    user_data["last_msg_time"] = current_time
    
    # Check if user has exceeded the flood limit
    if user_data["count"] >= flood_limit:
        # Reset count
        user_data["count"] = 0
        
        # Check if bot is admin
        if not await is_bot_admin(message):
            return
        
        # Apply punishment based on flood mode
        if flood_mode == "mute":
            try:
                await message.chat.restrict_member(
                    user_id,
                    ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False
                    )
                )
                
                await message.reply_text(
                    f"🛑 {message.from_user.mention} has been muted for flooding!"
                )
            except Exception as e:
                print(f"Failed to mute user: {str(e)}")
        
        elif flood_mode == "kick":
            try:
                await message.chat.ban_member(user_id)
                await message.chat.unban_member(user_id)  # Unban to allow them to join again
                
                await message.reply_text(
                    f"🛑 {message.from_user.mention} has been kicked for flooding!"
                )
            except Exception as e:
                print(f"Failed to kick user: {str(e)}")
        
        elif flood_mode == "ban":
            try:
                await message.chat.ban_member(user_id)
                
                await message.reply_text(
                    f"🛑 {message.from_user.mention} has been banned for flooding!"
                )
            except Exception as e:
                print(f"Failed to ban user: {str(e)}")

# Set flood limit handler
@app.on_message(filters.command("setflood") & filters.group)
async def set_flood_limit(client, message: Message):
    """Set the flood limit"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to set flood limit!")
        return
    
    # Check if command has arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a number for the flood limit!")
        return
    
    # Try to parse the limit
    try:
        limit = int(message.command[1])
        if limit < 1:
            await message.reply_text("Flood limit must be at least 1!")
            return
        
        # Set flood limit
        settings_db.set(f"{chat_id}_flood_limit", limit)
        
        # Enable flood protection if it was disabled
        if not settings_db.get(f"{chat_id}_flood_enabled", True):
            settings_db.set(f"{chat_id}_flood_enabled", True)
        
        await message.reply_text(f"Flood limit has been set to {limit} messages.")
    except ValueError:
        await message.reply_text("Please provide a valid number for the flood limit!")

# Set flood time handler
@app.on_message(filters.command("setfloodtime") & filters.group)
async def set_flood_time(client, message: Message):
    """Set the flood time frame"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to set flood time!")
        return
    
    # Check if command has arguments
    if len(message.command) < 2:
        await message.reply_text("Please provide a number of seconds for the flood time frame!")
        return
    
    # Try to parse the time
    try:
        flood_time = int(message.command[1])
        if flood_time < 1:
            await message.reply_text("Flood time must be at least 1 second!")
            return
        
        # Set flood time
        settings_db.set(f"{chat_id}_flood_time", flood_time)
        
        # Enable flood protection if it was disabled
        if not settings_db.get(f"{chat_id}_flood_enabled", True):
            settings_db.set(f"{chat_id}_flood_enabled", True)
        
        await message.reply_text(f"Flood time frame has been set to {flood_time} seconds.")
    except ValueError:
        await message.reply_text("Please provide a valid number of seconds for the flood time frame!")

# Flood settings handler
@app.on_message(filters.command("flood") & filters.group)
async def flood_settings(client, message: Message):
    """Show or toggle flood settings"""
    chat_id = str(message.chat.id)
    
    # Check if command has arguments
    if len(message.command) > 1:
        # Check if user is admin
        if not await is_admin(message, message.from_user.id):
            await message.reply_text("You need to be an admin to change flood settings!")
            return
        
        # Get argument
        arg = message.command[1].lower()
        
        # Enable/disable flood protection
        if arg in ["on", "yes", "enable"]:
            settings_db.set(f"{chat_id}_flood_enabled", True)
            await message.reply_text("Flood protection has been enabled!")
            return
        elif arg in ["off", "no", "disable"]:
            settings_db.set(f"{chat_id}_flood_enabled", False)
            await message.reply_text("Flood protection has been disabled!")
            return
    
    # Show current flood settings
    flood_enabled = settings_db.get(f"{chat_id}_flood_enabled", True)
    flood_limit = settings_db.get(f"{chat_id}_flood_limit", DEFAULT_FLOOD_LIMIT)
    flood_time = settings_db.get(f"{chat_id}_flood_time", DEFAULT_FLOOD_TIME)
    flood_mode = settings_db.get(f"{chat_id}_flood_mode", DEFAULT_FLOOD_MODE)
    
    status = "enabled" if flood_enabled else "disabled"
    
    await message.reply_text(
        f"Flood protection is currently **{status}**.\n\n"
        f"Current settings:\n"
        f"- Limit: {flood_limit} messages\n"
        f"- Time frame: {flood_time} seconds\n"
        f"- Mode: {flood_mode}\n\n"
        "Use `/setflood [number]` to set the message limit.\n"
        "Use `/setfloodtime [seconds]` to set the time frame.\n"
        "Use `/flood on/off` to enable/disable flood protection."
    )

# Set flood mode handler
@app.on_message(filters.command("setfloodmode") & filters.group)
async def set_flood_mode(client, message: Message):
    """Set the flood punishment mode"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to set flood mode!")
        return
    
    # Check if command has arguments
    if len(message.command) < 2:
        await message.reply_text(
            "Please provide a mode for flood punishment!\n\n"
            "Available modes: mute, kick, ban"
        )
        return
    
    # Get mode
    mode = message.command[1].lower()
    
    # Check if mode is valid
    if mode not in ["mute", "kick", "ban"]:
        await message.reply_text("Invalid mode! Available modes: mute, kick, ban")
        return
    
    # Set flood mode
    settings_db.set(f"{chat_id}_flood_mode", mode)
    
    await message.reply_text(f"Flood punishment mode has been set to {mode}.")

async def start_bot():
    """Start the bot"""
    await app.start()
    
    # Log successful start
    logger.info("Bot started successfully!")
    logger.info("Bot username: @%s", (await app.get_me()).username)
    
    # Idle to keep the bot running
    await idle()

if __name__ == "__main__":
    app.run(start_bot()) 