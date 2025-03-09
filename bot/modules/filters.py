import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import filters_db
from bot.utils import is_admin

# Module info
__MODULE__ = "Filters"
__HELP__ = """
**Filters Module:**

/filter [keyword] [reply message] - Add a filter
/filters - List all filters
/stop [keyword] - Remove a filter
/stopall - Remove all filters

When a user sends a message containing the keyword, the bot will reply with the filter message.
"""

# Add filter handler
@Client.on_message(filters.command("filter") & filters.group)
async def add_filter(client: Client, message: Message):
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
@Client.on_message(filters.command("filters") & filters.group)
async def list_filters(client: Client, message: Message):
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
@Client.on_message(filters.command("stop") & filters.group)
async def remove_filter(client: Client, message: Message):
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
@Client.on_message(filters.command("stopall") & filters.group)
async def remove_all_filters(client: Client, message: Message):
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
@Client.on_callback_query(filters.regex(r"^stopallfilters_(.+)_(confirm|cancel)"))
async def remove_all_filters_callback(client: Client, callback_query):
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
@Client.on_message(filters.group & filters.text & ~filters.command)
async def handle_filters(client: Client, message: Message):
    """Check if message contains filter keywords and reply with filter content"""
    chat_id = str(message.chat.id)
    
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