import discord
from discord.ext import commands
import os
import asyncio
import sys
import traceback
from core.config import config
from core.logger import logger
from core.database import db
from core.errorHandler import error_handler, setup_crash_protection

class DiscobaseBot(commands.Bot):
    def __init__(self):
        # Define necessary intents (equivalent to GatewayIntentBits in Discord.js)
        intents = discord.Intents.default()
        intents.members = True          # GatewayIntentBits.GuildMembers
        intents.message_content = True  # GatewayIntentBits.MessageContent
        intents.guilds = True           # GatewayIntentBits.Guilds
        intents.messages = True         # GatewayIntentBits.GuildMessages
        intents.dm_messages = True      # GatewayIntentBits.DirectMessages

        super().__init__(
            command_prefix=self._get_prefix,
            intents=intents,
            help_command=None,
            owner_id=config.owner_id
        )
        
        # Cooldown storage for custom handling
        self.cooldowns = {}
        self.presence_config = {}
        self._load_discobase_config()

    def _get_prefix(self, bot, message):
        """Get the prefix for the bot."""
        return config.prefix

    def _load_discobase_config(self):
        """Load discobase configuration from bot_config."""
        from core.bot_config import config as bot_config
        self.presence_config = {
            "enabled": bot_config.presence.ENABLED,
            "status": bot_config.presence.STATUS,
            "interval": bot_config.presence.INTERVAL,
            "type": bot_config.presence.TYPE,
            "names": bot_config.presence.NAMES,
            "streamingUrl": bot_config.presence.STREAMING_URL,
            "customState": bot_config.presence.CUSTOM_STATE,
        }

    async def setup_hook(self):
        """Initial setup for the bot, loading Cogs and syncing slash commands."""
        logger.section_header("Loading Components", "⚙️", "magenta")
        
        # 1. Initialize MongoDB
        await db.connect()
        
        # 2. Load Cogs
        await self.load_extensions()
        
        # 3. Initialize Automations (Reloader & Tracker)
        from core.utils.reloader import setup_reloader
        from core.utils.tracker import init_activity_tracker
        from core.utils.function_handler import load_and_run_functions
        setup_reloader(self)
        init_activity_tracker()
        
        # 4. Load scheduled functions
        await load_and_run_functions()
        
        # 5. Synchronize Slash Commands
        logger.info("Synchronizing slash commands...")
        try:
            # Sync globally (can be server-specific for dev commands if needed)
            synced = await self.tree.sync()
            logger.success(f"Successfully synchronized {len(synced)} slash commands!")
        except Exception as e:
            logger.error(f"Failed to synchronize slash commands: {e}")

    async def load_extensions(self):
        """Dynamically load all Cogs (Slash & Prefix commands) from the cogs/ directory."""
        if not os.path.exists("./cogs"):
            os.makedirs("./cogs")
            return

        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("__"):
                cog_name = f"cogs.{filename[:-3]}"
                try:
                    # Support for 'disabled' attribute to pause Cogs
                    # We use importlib to check the module before loading
                    import importlib
                    module = importlib.import_module(cog_name)
                    if getattr(module, "disabled", False):
                        logger.warning(f"Cog {filename} is currently DISABLED. Skipping loader...")
                        continue

                    await self.load_extension(cog_name)
                    logger.success(f"Loaded Cog: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load Cog {filename}: {e}")

    async def on_error(self, event, *args, **kwargs):
        """Standard discord.py error listener for event failures."""
        error_msg = traceback.format_exc()
        logger.error(f"Error in event {event}: {error_msg}")
        error_handler.log_error_to_file(error_msg)
        await error_handler.send_webhook_notification(error_msg)

    async def on_command_error(self, ctx, error):
        """Handle command errors globally."""
        # Let the Events cog handle most errors
        # This is just a fallback
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"Unhandled command error: {error}")

async def main():
    # Setup crash protection (sys.excepthook)
    setup_crash_protection()
    
    # Print the premium banner
    logger.print_banner()
    
    # Initialize and run the bot
    bot = DiscobaseBot()
    
    try:
        async with bot:
            logger.info("Connecting to Discord...")
            await bot.start(config.token)
    except discord.LoginFailure as e:
        logger.error(f"Failed to login: Invalid token provided. Please check your config.json")
        error_handler.log_error_to_file(str(e))
    except Exception as e:
        logger.error(f"Critical error starting bot: {e}")
        error_handler.log_error_to_file(str(e))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Bot shutdown requested by user.")
    except Exception as e:
        logger.error(f"Fatal crash: {e}")
