from pyrogram import Client
from bot.modules import ALL_MODULES

# Load all modules
def load_modules(app: Client):
    """Load all modules"""
    for module_name in ALL_MODULES:
        try:
            imported_module = __import__(f"bot.modules.{module_name}", fromlist=["__name__"])
            if hasattr(imported_module, "__MODULE__") and hasattr(imported_module, "__HELP__"):
                app.log.info(f"Successfully loaded module: {imported_module.__MODULE__}")
        except ImportError as e:
            app.log.error(f"Failed to import module {module_name}: {str(e)}")
            
# This will be called when the plugin is loaded
def __init__(app: Client):
    app.log.info("Loading modules...")
    load_modules(app) 