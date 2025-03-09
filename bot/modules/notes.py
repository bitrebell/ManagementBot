from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import notes_db
from bot.utils import is_admin
import re

# Module info
__MODULE__ = "Notes"
__HELP__ = """
**Notes Module:**

/save [name] [content] - Save a note
/get [name] - Get a note
/notes - List all saved notes
/clear [name] - Delete a note
/clearall - Delete all notes (admin only)

You can also use #[name] to get a note.
"""

# Save note handler
@Client.on_message(filters.command("save") & filters.group)
async def save_note(client: Client, message: Message):
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
@Client.on_message(filters.command("get") & filters.group)
async def get_note(client: Client, message: Message):
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

# Get note by hashtag
@Client.on_message(filters.regex(r"^#([a-zA-Z0-9_]+)") & filters.group)
async def get_note_by_hashtag(client: Client, message: Message):
    """Get a note by hashtag"""
    chat_id = str(message.chat.id)
    
    # Get note name from hashtag
    match = re.match(r"^#([a-zA-Z0-9_]+)", message.text)
    if not match:
        return
    
    note_name = match.group(1).lower()
    
    # Get note content
    note_content = notes_db.get(f"{chat_id}_{note_name}")
    
    if note_content:
        await message.reply_text(note_content)

# List notes handler
@Client.on_message(filters.command("notes") & filters.group)
async def list_notes(client: Client, message: Message):
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
@Client.on_message(filters.command("clear") & filters.group)
async def clear_note(client: Client, message: Message):
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
@Client.on_message(filters.command("clearall") & filters.group)
async def clear_all_notes(client: Client, message: Message):
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
@Client.on_callback_query(filters.regex(r"^clearallnotes_(.+)_(confirm|cancel)"))
async def clear_all_notes_callback(client: Client, callback_query):
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