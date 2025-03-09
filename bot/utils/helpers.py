import os
import re
import time
import asyncio
from typing import List, Dict, Union, Optional
from pyrogram.types import Message, User, ChatMember
from pyrogram.errors import FloodWait, UserNotParticipant

# Time formatter
def get_readable_time(seconds: int) -> str:
    """Convert seconds to readable time format"""
    count = 0
    time_formats = {
        60: 'minutes',
        3600: 'hours',
        86400: 'days',
        604800: 'weeks',
        2592000: 'months',
        31536000: 'years'
    }
    
    for time_unit, time_name in sorted(time_formats.items(), reverse=True):
        if seconds >= time_unit:
            n = int(seconds / time_unit)
            count += 1
            if count == 1:
                readable_time = f"{n} {time_name[:-1] if n == 1 else time_name}"
            else:
                readable_time += f", {n} {time_name[:-1] if n == 1 else time_name}"
            seconds %= time_unit
    
    return readable_time if count > 0 else "a few seconds"

# Extract user from message
async def extract_user(message: Message) -> Optional[User]:
    """Extract user from message (reply, mention, or ID)"""
    user = None
    user_id = None
    
    # If message is a reply, get the replied user
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    
    # If message has text, try to extract user ID or username
    if message.text:
        # Split message text by spaces
        entities = message.text.split()
        # Remove the command
        if entities and entities[0].startswith('/'):
            entities = entities[1:]
        
        if entities:
            # Check if the first entity is a user ID
            if entities[0].isdigit():
                user_id = int(entities[0])
            # Check if the first entity is a username
            elif entities[0].startswith('@'):
                username = entities[0][1:]
                try:
                    user = await message.chat.client.get_users(username)
                    return user
                except Exception:
                    return None
    
    # If user_id was found, get the user
    if user_id:
        try:
            user = await message.chat.client.get_users(user_id)
        except Exception:
            return None
    
    return user

# Check if user is admin
async def is_admin(message: Message, user_id: int) -> bool:
    """Check if a user is an admin in the chat"""
    try:
        chat_member = await message.chat.get_member(user_id)
        return chat_member.status in ["creator", "administrator"]
    except UserNotParticipant:
        return False
    except Exception:
        return False

# Check if bot is admin
async def is_bot_admin(message: Message) -> bool:
    """Check if the bot is an admin in the chat"""
    bot_id = (await message.chat.client.get_me()).id
    return await is_admin(message, bot_id)

# Get chat admins
async def get_chat_admins(message: Message) -> List[int]:
    """Get a list of admin IDs in the chat"""
    admins = []
    async for admin in message.chat.get_members(filter="administrators"):
        admins.append(admin.user.id)
    return admins

# Safe message deletion
async def safe_delete(message: Message, delay: int = 0) -> bool:
    """Safely delete a message with optional delay"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        await message.delete()
        return True
    except Exception:
        return False 