import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.modules import ALL_MODULES

# Module info
__MODULE__ = "Help"
__HELP__ = """
/help - Show this help message
/help [module] - Show help for a specific module
"""

# Dictionary to store module help texts
HELP_TEXTS = {}

# Load help texts from modules
def load_help():
    """Load help texts from all modules"""
    for module_name in ALL_MODULES:
        try:
            imported_module = __import__(f"bot.modules.{module_name}", fromlist=["__HELP__"])
            if hasattr(imported_module, "__HELP__"):
                HELP_TEXTS[module_name] = imported_module.__HELP__
        except ImportError:
            pass

# Help command handler
@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle the /help command"""
    # Load help texts if not loaded
    if not HELP_TEXTS:
        load_help()
    
    # Check if a specific module is requested
    if len(message.command) > 1:
        module_name = message.command[1].lower()
        if module_name in HELP_TEXTS:
            await message.reply_text(
                f"Help for **{module_name.capitalize()}** module:\n\n{HELP_TEXTS[module_name]}",
                parse_mode="markdown"
            )
        else:
            await message.reply_text(
                f"Module **{module_name}** not found. Use /help to see all available modules.",
                parse_mode="markdown"
            )
        return
    
    # Create main help message
    help_text = "Here are the available modules:\n\n"
    
    # Create keyboard with module buttons
    keyboard = []
    row = []
    
    # Add buttons for each module
    for i, module_name in enumerate(sorted(HELP_TEXTS.keys())):
        # Add 3 buttons per row
        if i % 3 == 0 and i > 0:
            keyboard.append(row)
            row = []
        
        # Add button for module
        row.append(
            InlineKeyboardButton(
                module_name.capitalize(),
                callback_data=f"help_{module_name}"
            )
        )
    
    # Add last row if not empty
    if row:
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("Back", callback_data="help_back")])
    
    # Send help message with keyboard
    await message.reply_text(
        "Here are all the available modules. Click on a module to see its commands:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Help callback handler
@Client.on_callback_query(filters.regex(r"^help_(.+)"))
async def help_callback(client: Client, callback_query: CallbackQuery):
    """Handle help callbacks"""
    # Load help texts if not loaded
    if not HELP_TEXTS:
        load_help()
    
    # Get module name from callback data
    match = re.match(r"^help_(.+)", callback_query.data)
    if not match:
        await callback_query.answer("Invalid callback data", show_alert=True)
        return
    
    module_name = match.group(1)
    
    # Handle main help menu
    if module_name == "main":
        # Create keyboard with module buttons
        keyboard = []
        row = []
        
        # Add buttons for each module
        for i, mod_name in enumerate(sorted(HELP_TEXTS.keys())):
            # Add 3 buttons per row
            if i % 3 == 0 and i > 0:
                keyboard.append(row)
                row = []
            
            # Add button for module
            row.append(
                InlineKeyboardButton(
                    mod_name.capitalize(),
                    callback_data=f"help_{mod_name}"
                )
            )
        
        # Add last row if not empty
        if row:
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("Back", callback_data="help_back")])
        
        # Edit message with keyboard
        await callback_query.edit_message_text(
            "Here are all the available modules. Click on a module to see its commands:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
        return
    
    # Handle back button
    if module_name == "back":
        # Get bot info
        bot_info = await client.get_me()
        
        # Create welcome message
        welcome_text = f"""
Hello {callback_query.from_user.mention}! 👋

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
        
        # Edit message with keyboard
        await callback_query.edit_message_text(
            welcome_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        await callback_query.answer()
        return
    
    # Handle specific module help
    if module_name in HELP_TEXTS:
        # Create keyboard with back button
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="help_main")]]
        )
        
        # Edit message with module help
        await callback_query.edit_message_text(
            f"Help for **{module_name.capitalize()}** module:\n\n{HELP_TEXTS[module_name]}",
            reply_markup=keyboard,
            parse_mode="markdown"
        )
        await callback_query.answer()
    else:
        await callback_query.answer(f"Module {module_name} not found", show_alert=True) 