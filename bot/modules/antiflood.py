import time
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from bot.database import settings_db
from bot.utils import is_admin, is_bot_admin

# Module info
__MODULE__ = "Anti-Flood"
__HELP__ = """
**Anti-Flood Module:**

/setflood [number] - Set the number of messages allowed in a time frame
/setfloodtime [seconds] - Set the time frame for flood detection
/flood - Show current flood settings
/flood off - Disable flood protection
/flood on - Enable flood protection

When a user sends more than the allowed number of messages in the specified time frame, they will be muted.
"""

# Default flood settings
DEFAULT_FLOOD_LIMIT = 5  # 5 messages
DEFAULT_FLOOD_TIME = 5   # 5 seconds
DEFAULT_FLOOD_MODE = "mute"  # Options: mute, kick, ban

# Store user message counts
FLOOD_USERS = defaultdict(lambda: {"count": 0, "last_msg_time": 0})

# Set flood limit handler
@Client.on_message(filters.command("setflood") & filters.group)
async def set_flood_limit(client: Client, message: Message):
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
@Client.on_message(filters.command("setfloodtime") & filters.group)
async def set_flood_time(client: Client, message: Message):
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
@Client.on_message(filters.command("flood") & filters.group)
async def flood_settings(client: Client, message: Message):
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

# Flood detection handler
@Client.on_message(filters.group & ~filters.service & ~filters.me & ~filters.bot & ~filters.edited)
async def check_flood(client: Client, message: Message):
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

# Set flood mode handler
@Client.on_message(filters.command("setfloodmode") & filters.group)
async def set_flood_mode(client: Client, message: Message):
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