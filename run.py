#!/usr/bin/env python3
"""
Run script for the Telegram Management Bot
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check Python version
if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 7):
    logger.error("You need Python 3.7 or higher to run this bot!")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Check if required environment variables are set
required_vars = ["API_ID", "API_HASH", "BOT_TOKEN"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set them in the .env file")
    sys.exit(1)

# Import and run the bot
try:
    from main import app
    
    logger.info("Starting the bot...")
    app.run()
except ImportError as e:
    logger.error(f"Failed to import the bot: {str(e)}")
    sys.exit(1)
except Exception as e:
    logger.error(f"An error occurred while running the bot: {str(e)}")
    sys.exit(1) 