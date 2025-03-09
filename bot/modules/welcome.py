from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import welcome_db
from bot.utils import is_admin

# Module info
__MODULE__ = "Welcome"
__HELP__ = """
**Welcome Module:**

/welcome - Show current welcome message
/setwelcome [text] - Set a custom welcome message
/resetwelcome - Reset welcome message to default
/welcome on/off - Enable/disable welcome messages

**Variables for welcome messages:**
- `{first}` - User's first name
- `{last}` - User's last name
- `{mention}` - Mention the user
- `{username}` - User's username
- `{id}` - User's ID
- `{chat}` - Chat name
"""

# Default welcome message
DEFAULT_WELCOME = "Hello {mention}, welcome to {chat}!"

# Welcome message handler
@Client.on_message(filters.new_chat_members)
async def welcome_new_members(client: Client, message: Message):
    """Send welcome message to new members"""
    chat_id = str(message.chat.id)
    
    # Check if welcome messages are enabled
    welcome_enabled = welcome_db.get(f"{chat_id}_enabled", True)
    if not welcome_enabled:
        return
    
    # Get custom welcome message or use default
    welcome_text = welcome_db.get(f"{chat_id}_welcome", DEFAULT_WELCOME)
    
    # Send welcome message for each new member
    for new_member in message.new_chat_members:
        # Skip if the new member is a bot
        if new_member.is_bot:
            continue
        
        # Format welcome message with user info
        formatted_text = welcome_text.format(
            first=new_member.first_name,
            last=new_member.last_name or "",
            mention=new_member.mention,
            username=f"@{new_member.username}" if new_member.username else "No username",
            id=new_member.id,
            chat=message.chat.title
        )
        
        # Create welcome button
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Group Rules", callback_data=f"rules_{chat_id}")]]
        )
        
        # Send welcome message
        await message.reply_text(
            formatted_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

# Welcome command handler
@Client.on_message(filters.command("welcome") & filters.group)
async def welcome_command(client: Client, message: Message):
    """Handle welcome command"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to manage welcome messages!")
        return
    
    # Check if command has arguments
    if len(message.command) > 1:
        arg = message.command[1].lower()
        
        # Enable/disable welcome messages
        if arg in ["on", "yes", "enable"]:
            welcome_db.set(f"{chat_id}_enabled", True)
            await message.reply_text("Welcome messages are now enabled!")
            return
        elif arg in ["off", "no", "disable"]:
            welcome_db.set(f"{chat_id}_enabled", False)
            await message.reply_text("Welcome messages are now disabled!")
            return
    
    # Show current welcome message
    welcome_enabled = welcome_db.get(f"{chat_id}_enabled", True)
    welcome_text = welcome_db.get(f"{chat_id}_welcome", DEFAULT_WELCOME)
    
    status = "enabled" if welcome_enabled else "disabled"
    
    await message.reply_text(
        f"Welcome messages are currently **{status}**.\n\n"
        f"Current welcome message:\n\n{welcome_text}\n\n"
        "Use `/setwelcome [text]` to set a custom welcome message.\n"
        "Use `/resetwelcome` to reset to default welcome message.\n"
        "Use `/welcome on/off` to enable/disable welcome messages.",
        disable_web_page_preview=True
    )

# Set welcome message handler
@Client.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client: Client, message: Message):
    """Set custom welcome message"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to manage welcome messages!")
        return
    
    # Check if command has text
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "Please provide a welcome message text or reply to a message.\n\n"
            "**Variables you can use:**\n"
            "- `{first}` - User's first name\n"
            "- `{last}` - User's last name\n"
            "- `{mention}` - Mention the user\n"
            "- `{username}` - User's username\n"
            "- `{id}` - User's ID\n"
            "- `{chat}` - Chat name"
        )
        return
    
    # Get welcome text from command or reply
    if message.reply_to_message and message.reply_to_message.text:
        welcome_text = message.reply_to_message.text
    else:
        welcome_text = message.text.split(None, 1)[1]
    
    # Save welcome message
    welcome_db.set(f"{chat_id}_welcome", welcome_text)
    
    await message.reply_text("Welcome message has been set successfully!")

# Reset welcome message handler
@Client.on_message(filters.command("resetwelcome") & filters.group)
async def reset_welcome(client: Client, message: Message):
    """Reset welcome message to default"""
    chat_id = str(message.chat.id)
    
    # Check if user is admin
    if not await is_admin(message, message.from_user.id):
        await message.reply_text("You need to be an admin to manage welcome messages!")
        return
    
    # Reset welcome message
    welcome_db.delete(f"{chat_id}_welcome")
    
    await message.reply_text(f"Welcome message has been reset to default:\n\n{DEFAULT_WELCOME}")

# Rules callback handler
@Client.on_callback_query(filters.regex(r"^rules_(.+)"))
async def rules_callback(client: Client, callback_query):
    """Handle rules button callback"""
    chat_id = callback_query.data.split("_")[1]
    
    # Get rules or show default message
    rules = welcome_db.get(f"{chat_id}_rules", "No rules have been set for this group yet.")
    
    await callback_query.answer()
    await callback_query.message.reply_text(
        f"**Group Rules:**\n\n{rules}",
        disable_web_page_preview=True
    ) 