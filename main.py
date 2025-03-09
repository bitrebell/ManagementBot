import os
import logging
from dotenv import load_dotenv
from pyrogram import Client, idle
from bot.modules import ALL_MODULES

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
    bot_token=BOT_TOKEN,
    plugins=dict(root="bot/plugins")
)

async def start_bot():
    """Start the bot and load all modules"""
    await app.start()
    
    # Load all modules
    for module in ALL_MODULES:
        imported_module = __import__(f"bot.modules.{module}", fromlist=["__name__"])
        if hasattr(imported_module, "__MODULE__") and hasattr(imported_module, "__HELP__"):
            logger.info(f"Successfully loaded module: {imported_module.__MODULE__}")
    
    logger.info("Bot started successfully!")
    logger.info("Bot username: @%s", (await app.get_me()).username)
    
    # Idle to keep the bot running
    await idle()

if __name__ == "__main__":
    app.run(start_bot()) 