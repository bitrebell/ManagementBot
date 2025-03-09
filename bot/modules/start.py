from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Module info
__MODULE__ = "Start"
__HELP__ = """
/start - Start the bot
/help - Show help message
"""

# Start command handler
@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle the /start command"""
    # Get bot info
    bot_info = await client.get_me()
    
    # Create welcome message
    welcome_text = f"""
Hello {message.from_user.mention}! 👋

I'm **{bot_info.first_name}**, a powerful group management bot with music playing capabilities.

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