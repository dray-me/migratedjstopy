import os
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.logger import logger

COG_TEMPLATE = '''import discord
from discord.ext import commands

class {class_name}(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="{command_name}", description="Describe your command here.")
    async def {command_name}(self, ctx):
        """Command execution logic goes here."""
        await ctx.send("Hello from your new Cog!")

async def setup(bot):
    await bot.add_cog({class_name}(bot))
'''

class CogReloader(FileSystemEventHandler):
    def __init__(self, bot):
        self.bot = bot
        self.cogs_dir = os.path.join(os.getcwd(), 'cogs')

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            filename = os.path.basename(event.src_path)
            cog_name = f"cogs.{filename[:-3]}"
            
            # Use asyncio to schedule the reload on the bot's loop
            asyncio.run_coroutine_threadsafe(self.reload_cog(cog_name), self.bot.loop)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            # If file is empty, write template
            if os.path.getsize(event.src_path) == 0:
                name = os.path.basename(event.src_path)[:-3]
                class_name = name.capitalize()
                
                content = COG_TEMPLATE.format(class_name=class_name, command_name=name)
                with open(event.src_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.success(f"Added basic Cog structure to {name}.py")

    async def reload_cog(self, cog_name):
        try:
            await self.bot.reload_extension(cog_name)
            logger.success(f"Hot-reloaded Cog: {cog_name}")
        except Exception as e:
            logger.error(f"Failed to hot-reload Cog {cog_name}: {e}")

def setup_reloader(bot):
    """Initializes the Cog reloader observer."""
    reloader = CogReloader(bot)
    observer = Observer()
    observer.schedule(reloader, reloader.cogs_dir, recursive=False)
    observer.start()
    logger.success("Cog reloader initialized (Watchfolders parity).")
    return observer
