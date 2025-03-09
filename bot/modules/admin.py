import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired, UserNotParticipant

from bot.utils import extract_user, is_admin, is_bot_admin, get_readable_time

# Module info
__MODULE__ = "Admin"
__HELP__ = """
**Admin Commands:**

/ban [user] [reason] - Ban a user from the group
/unban [user] - Unban a user from the group
/kick [user] [reason] - Kick a user from the group
/mute [user] [reason] - Mute a user in the group
/unmute [user] - Unmute a user in the group
/promote [user] - Promote a user to admin
/demote [user] - Demote an admin to regular user
/pin - Pin the replied message
/unpin - Unpin the replied message
/unpinall - Unpin all pinned messages
/purge - Purge messages from replied message to current message
"""

# Ban command handler
@Client.on_message(filters.command("ban") & filters.group)
async def ban_user(client: Client, message: Message):
    """Ban a user from the group"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to ban users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to ban users!")
        return
    
    # Extract user to ban
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Check if the user is an admin
    if await is_admin(message, user.id):
        await message.reply_text("I can't ban an admin!")
        return
    
    # Get reason if provided
    reason = ""
    if len(message.command) > 1:
        reason = " ".join(message.command[1:])
    
    # Ban the user
    try:
        await message.chat.ban_member(user.id)
        
        # Send ban message
        ban_text = f"Banned {user.mention} from the group!"
        if reason:
            ban_text += f"\nReason: {reason}"
        
        await message.reply_text(ban_text)
    except Exception as e:
        await message.reply_text(f"Failed to ban user: {str(e)}")

# Unban command handler
@Client.on_message(filters.command("unban") & filters.group)
async def unban_user(client: Client, message: Message):
    """Unban a user from the group"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to unban users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to unban users!")
        return
    
    # Extract user to unban
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Unban the user
    try:
        await message.chat.unban_member(user.id)
        await message.reply_text(f"Unbanned {user.mention} from the group!")
    except Exception as e:
        await message.reply_text(f"Failed to unban user: {str(e)}")

# Kick command handler
@Client.on_message(filters.command("kick") & filters.group)
async def kick_user(client: Client, message: Message):
    """Kick a user from the group"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to kick users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to kick users!")
        return
    
    # Extract user to kick
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Check if the user is an admin
    if await is_admin(message, user.id):
        await message.reply_text("I can't kick an admin!")
        return
    
    # Get reason if provided
    reason = ""
    if len(message.command) > 1:
        reason = " ".join(message.command[1:])
    
    # Kick the user
    try:
        await message.chat.ban_member(user.id)
        await asyncio.sleep(1)  # Wait a second
        await message.chat.unban_member(user.id)  # Unban to allow them to join again
        
        # Send kick message
        kick_text = f"Kicked {user.mention} from the group!"
        if reason:
            kick_text += f"\nReason: {reason}"
        
        await message.reply_text(kick_text)
    except Exception as e:
        await message.reply_text(f"Failed to kick user: {str(e)}")

# Mute command handler
@Client.on_message(filters.command("mute") & filters.group)
async def mute_user(client: Client, message: Message):
    """Mute a user in the group"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to mute users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to mute users!")
        return
    
    # Extract user to mute
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Check if the user is an admin
    if await is_admin(message, user.id):
        await message.reply_text("I can't mute an admin!")
        return
    
    # Get reason if provided
    reason = ""
    if len(message.command) > 1:
        reason = " ".join(message.command[1:])
    
    # Mute the user
    try:
        await message.chat.restrict_member(
            user.id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
        
        # Send mute message
        mute_text = f"Muted {user.mention} in the group!"
        if reason:
            mute_text += f"\nReason: {reason}"
        
        await message.reply_text(mute_text)
    except Exception as e:
        await message.reply_text(f"Failed to mute user: {str(e)}")

# Unmute command handler
@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_user(client: Client, message: Message):
    """Unmute a user in the group"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to unmute users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to unmute users!")
        return
    
    # Extract user to unmute
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Unmute the user
    try:
        await message.chat.restrict_member(
            user.id,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
                can_invite_users=True
            )
        )
        
        await message.reply_text(f"Unmuted {user.mention} in the group!")
    except Exception as e:
        await message.reply_text(f"Failed to unmute user: {str(e)}")

# Promote command handler
@Client.on_message(filters.command("promote") & filters.group)
async def promote_user(client: Client, message: Message):
    """Promote a user to admin"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to promote users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to promote users!")
        return
    
    # Extract user to promote
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Promote the user
    try:
        await message.chat.promote_member(
            user.id,
            can_change_info=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_voice_chats=True
        )
        
        await message.reply_text(f"Promoted {user.mention} to admin!")
    except Exception as e:
        await message.reply_text(f"Failed to promote user: {str(e)}")

# Demote command handler
@Client.on_message(filters.command("demote") & filters.group)
async def demote_user(client: Client, message: Message):
    """Demote an admin to regular user"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to demote users!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to demote users!")
        return
    
    # Extract user to demote
    user = await extract_user(message)
    if not user:
        await message.reply_text("I can't find that user.")
        return
    
    # Demote the user
    try:
        await message.chat.promote_member(
            user.id,
            can_change_info=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_voice_chats=False
        )
        
        await message.reply_text(f"Demoted {user.mention} to regular user!")
    except Exception as e:
        await message.reply_text(f"Failed to demote user: {str(e)}")

# Pin command handler
@Client.on_message(filters.command("pin") & filters.group)
async def pin_message(client: Client, message: Message):
    """Pin the replied message"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to pin messages!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to pin messages!")
        return
    
    # Check if the message is a reply
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to pin it!")
        return
    
    # Pin the message
    try:
        await message.reply_to_message.pin()
        await message.reply_text("Message pinned!")
    except Exception as e:
        await message.reply_text(f"Failed to pin message: {str(e)}")

# Unpin command handler
@Client.on_message(filters.command("unpin") & filters.group)
async def unpin_message(client: Client, message: Message):
    """Unpin the replied message"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to unpin messages!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to unpin messages!")
        return
    
    # Check if the message is a reply
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to unpin it!")
        return
    
    # Unpin the message
    try:
        await message.reply_to_message.unpin()
        await message.reply_text("Message unpinned!")
    except Exception as e:
        await message.reply_text(f"Failed to unpin message: {str(e)}")

# Unpin all command handler
@Client.on_message(filters.command("unpinall") & filters.group)
async def unpin_all_messages(client: Client, message: Message):
    """Unpin all pinned messages"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to unpin messages!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to unpin messages!")
        return
    
    # Unpin all messages
    try:
        await client.unpin_all_chat_messages(message.chat.id)
        await message.reply_text("All messages unpinned!")
    except Exception as e:
        await message.reply_text(f"Failed to unpin all messages: {str(e)}")

# Purge command handler
@Client.on_message(filters.command("purge") & filters.group)
async def purge_messages(client: Client, message: Message):
    """Purge messages from replied message to current message"""
    # Check if the bot is admin
    if not await is_bot_admin(message):
        await message.reply_text("I need to be an admin to purge messages!")
        return
    
    # Check if the user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to purge messages!")
        return
    
    # Check if the message is a reply
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to start purging from!")
        return
    
    # Get message IDs to delete
    message_ids = []
    for message_id in range(message.reply_to_message.id, message.id + 1):
        message_ids.append(message_id)
    
    # Delete messages
    try:
        await client.delete_messages(message.chat.id, message_ids)
        await message.reply_text(f"Purged {len(message_ids)} messages!")
    except Exception as e:
        await message.reply_text(f"Failed to purge messages: {str(e)}") 