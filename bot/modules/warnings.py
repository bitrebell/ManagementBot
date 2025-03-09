from pyrogram import Client, filters
from pyrogram.types import Message
from bot.database import warnings_db
from bot.utils import extract_user, is_admin, is_bot_admin

# Module info
__MODULE__ = "Warnings"
__HELP__ = """
**Warnings Module:**

/warn [user] [reason] - Warn a user
/warns [user] - Check a user's warnings
/resetwarns [user] - Reset a user's warnings
/warnlimit - Show or set the warning limit
/warnmode - Show or set the warning mode (ban, kick, mute)

When a user reaches the warning limit, they will be banned, kicked, or muted based on the warning mode.
"""

# Default warning settings
DEFAULT_WARN_LIMIT = 3
DEFAULT_WARN_MODE = "ban"  # Options: ban, kick, mute

# Warn command handler
@Client.on_message(filters.command("warn") & filters.group)
async def warn_user(client: Client, message: Message):
    """Warn a user"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to warn users!")
        return
    
    # Extract user to warn
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Check if the user is an admin
    if await is_admin(message, user.id):
        await message.reply_text("I can't warn an admin!")
        return
    
    # Get reason if provided
    reason = ""
    if len(message.command) > 1:
        reason = " ".join(message.command[1:])
    
    # Get user's current warnings
    user_warns_key = f"{chat_id}_{user.id}_warns"
    user_warns = warnings_db.get(user_warns_key, 0)
    
    # Increment warnings
    user_warns += 1
    warnings_db.set(user_warns_key, user_warns)
    
    # Get warning limit and mode
    warn_limit = warnings_db.get(f"{chat_id}_warn_limit", DEFAULT_WARN_LIMIT)
    warn_mode = warnings_db.get(f"{chat_id}_warn_mode", DEFAULT_WARN_MODE)
    
    # Create warning message
    warn_text = f"⚠️ {user.mention} has been warned! ({user_warns}/{warn_limit})"
    if reason:
        warn_text += f"\nReason: {reason}"
    
    # Check if user has reached the warning limit
    if user_warns >= warn_limit:
        warn_text += f"\n\nUser has reached the warning limit and will be {warn_mode}ned!"
        
        # Reset warnings
        warnings_db.set(user_warns_key, 0)
        
        # Apply punishment based on warning mode
        if warn_mode == "ban":
            if await is_bot_admin(message):
                await message.chat.ban_member(user.id)
                warn_text += "\nUser has been banned!"
            else:
                warn_text += "\nI don't have permission to ban users!"
        
        elif warn_mode == "kick":
            if await is_bot_admin(message):
                await message.chat.ban_member(user.id)
                await message.chat.unban_member(user.id)  # Unban to allow them to join again
                warn_text += "\nUser has been kicked!"
            else:
                warn_text += "\nI don't have permission to kick users!"
        
        elif warn_mode == "mute":
            if await is_bot_admin(message):
                await message.chat.restrict_member(
                    user.id,
                    permissions=dict(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False
                    )
                )
                warn_text += "\nUser has been muted!"
            else:
                warn_text += "\nI don't have permission to mute users!"
    
    await message.reply_text(warn_text)

# Check warnings command handler
@Client.on_message(filters.command("warns") & filters.group)
async def check_warns(client: Client, message: Message):
    """Check a user's warnings"""
    chat_id = str(message.chat.id)
    
    # Extract user to check
    user = await extract_user(message)
    if not user:
        # If no user specified, check the sender's warnings
        user = message.from_user
    
    # Get user's current warnings
    user_warns_key = f"{chat_id}_{user.id}_warns"
    user_warns = warnings_db.get(user_warns_key, 0)
    
    # Get warning limit
    warn_limit = warnings_db.get(f"{chat_id}_warn_limit", DEFAULT_WARN_LIMIT)
    
    await message.reply_text(f"{user.mention} has {user_warns}/{warn_limit} warnings.")

# Reset warnings command handler
@Client.on_message(filters.command("resetwarns") & filters.group)
async def reset_warns(client: Client, message: Message):
    """Reset a user's warnings"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to reset warnings!")
        return
    
    # Extract user to reset warnings
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Reset user's warnings
    user_warns_key = f"{chat_id}_{user.id}_warns"
    warnings_db.set(user_warns_key, 0)
    
    await message.reply_text(f"Warnings for {user.mention} have been reset.")

# Warning limit command handler
@Client.on_message(filters.command("warnlimit") & filters.group)
async def warn_limit(client: Client, message: Message):
    """Show or set the warning limit"""
    chat_id = str(message.chat.id)
    
    # Check if command has arguments
    if len(message.command) > 1:
        # Check if user is admin
        if not await is_admin(message, message.from_user.id):
            await message.reply_text("You need to be an admin to set the warning limit!")
            return
        
        # Try to parse the limit
        try:
            limit = int(message.command[1])
            if limit < 1:
                await message.reply_text("Warning limit must be at least 1!")
                return
            
            # Set warning limit
            warnings_db.set(f"{chat_id}_warn_limit", limit)
            await message.reply_text(f"Warning limit has been set to {limit}.")
        except ValueError:
            await message.reply_text("Please provide a valid number for the warning limit!")
    else:
        # Show current warning limit
        warn_limit = warnings_db.get(f"{chat_id}_warn_limit", DEFAULT_WARN_LIMIT)
        await message.reply_text(
            f"Current warning limit: {warn_limit}\n\n"
            "Use `/warnlimit [number]` to set a new limit."
        )

# Warning mode command handler
@Client.on_message(filters.command("warnmode") & filters.group)
async def warn_mode(client: Client, message: Message):
    """Show or set the warning mode"""
    chat_id = str(message.chat.id)
    
    # Check if command has arguments
    if len(message.command) > 1:
        # Check if user is admin
        if not await is_admin(message, message.from_user.id):
            await message.reply_text("You need to be an admin to set the warning mode!")
            return
        
        # Get mode
        mode = message.command[1].lower()
        
        # Check if mode is valid
        if mode not in ["ban", "kick", "mute"]:
            await message.reply_text("Invalid mode! Available modes: ban, kick, mute")
            return
        
        # Set warning mode
        warnings_db.set(f"{chat_id}_warn_mode", mode)
        await message.reply_text(f"Warning mode has been set to {mode}.")
    else:
        # Show current warning mode
        warn_mode = warnings_db.get(f"{chat_id}_warn_mode", DEFAULT_WARN_MODE)
        await message.reply_text(
            f"Current warning mode: {warn_mode}\n\n"
            "Use `/warnmode [mode]` to set a new mode.\n"
            "Available modes: ban, kick, mute"
        ) 