import discord
from discord.ext import commands, tasks
import os
import traceback
import pendulum
from core.logger import logger
from core.config import config
from core.models import CommandStats
from core.utils.similarity import get_similar_commands
from core.utils.intents import check_missing_intents
from core.utils.command_checks import (
    check_admin_only, check_owner_only, check_user_permissions,
    check_bot_permissions, check_required_roles, check_cooldown,
    track_command_stats, send_command_log
)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_index = 0
        self.cooldowns = {}
        self._load_presence_config()
        self._load_discobase_config()

    def _load_presence_config(self):
        """Loads presence configuration from bot_config."""
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

    def _load_discobase_config(self):
        """Loads full discobase configuration."""
        from core.bot_config import config as bot_config
        self.discobase_config = {
            "errorLogging": {"enabled": bot_config.error_logging.ENABLED},
            "presence": self.presence_config,
            "commandStats": {
                "enabled": bot_config.command_stats.ENABLED,
                "trackUsage": bot_config.command_stats.TRACK_USAGE,
                "trackServers": bot_config.command_stats.TRACK_SERVERS,
                "trackUsers": bot_config.command_stats.TRACK_USERS,
            },
            "activityTracker": {
                "enabled": bot_config.activity_tracker.ENABLED,
                "ignoredPaths": bot_config.activity_tracker.IGNORED_PATHS,
            },
        }

    @commands.Cog.listener()
    async def on_ready(self):
        """Triggered when the bot is fully ready and connected."""
        logger.section_header("Bot Ready", "🚀", "green")
        logger.success(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info(f"Connected to {len(self.bot.guilds)} guilds.")
        
        # Check for missing intents
        check_missing_intents(self.bot)
        
        # Start presence rotation if enabled
        if self.presence_config.get("enabled", False):
            interval_ms = self.presence_config.get("interval", 10000)
            self.rotate_presence.change_interval(seconds=interval_ms / 1000)
            if not self.rotate_presence.is_running():
                self.rotate_presence.start()
                logger.info(f"Presence rotation started (Interval: {interval_ms/1000}s)")
        else:
            await self.bot.change_presence(
                activity=discord.CustomActivity(name="🚀 Made with discobase-py!"),
                status=discord.Status.online
            )

    @tasks.loop(seconds=10)
    async def rotate_presence(self):
        """Background task to rotate bot presence names."""
        names = self.presence_config.get("names", ["Discobase"])
        if not names:
            return

        activity_type_str = self.presence_config.get("type", "PLAYING").upper()
        status_str = self.presence_config.get("status", "online").lower()
        
        activity_map = {
            "PLAYING": discord.ActivityType.playing,
            "STREAMING": discord.ActivityType.streaming,
            "LISTENING": discord.ActivityType.listening,
            "WATCHING": discord.ActivityType.watching,
            "COMPETING": discord.ActivityType.competing,
            "CUSTOM": discord.ActivityType.custom
        }
        
        activity_type = activity_map.get(activity_type_str, discord.ActivityType.playing)
        status = getattr(discord.Status, status_str, discord.Status.online)
        
        current_name = names[self.presence_index]
        
        if activity_type == discord.ActivityType.streaming:
            stream_url = self.presence_config.get("streamingUrl")
            activity = discord.Streaming(name=current_name, url=stream_url)
        elif activity_type == discord.ActivityType.custom:
            custom_state = self.presence_config.get("customState", "🚀 discobase!")
            activity = discord.CustomActivity(name=custom_state)
        else:
            activity = discord.Activity(type=activity_type, name=current_name)
            
        await self.bot.change_presence(activity=activity, status=status)
        self.presence_index = (self.presence_index + 1) % len(names)

    @rotate_presence.before_loop
    async def before_rotate_presence(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Logs when the bot joins a new server (guildJoinLogs.js)."""
        channel_id = config.logging.GUILD_JOIN_LOGS_ID
        if not channel_id or channel_id == 'GUILD_JOIN_LOGS_CHANNEL_ID':
            return

        channel = self.bot.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title=f"Joined New Guild: {guild.name}",
                color=discord.Color.blue(),
                timestamp=pendulum.now()
            )
            embed.add_field(name="Total Members", value=f"{guild.member_count}", inline=True)
            embed.add_field(name="Guild ID", value=f"{guild.id}", inline=True)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.set_footer(text="Bot joined at")
            
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Logs when the bot leaves a server (guildLeaveLogs.js)."""
        channel_id = config.logging.GUILD_LEAVE_LOGS_ID
        if not channel_id or channel_id == 'GUILD_LEAVE_LOGS_CHANNEL_ID':
            return

        channel = self.bot.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(
                title=f"Left Guild: {guild.name}",
                color=discord.Color.red(),
                timestamp=pendulum.now()
            )
            embed.add_field(name="Total Members", value=f"{guild.member_count}", inline=True)
            embed.add_field(name="Guild ID", value=f"{guild.id}", inline=True)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            embed.set_footer(text="Bot left at")
            
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Called when a prefix command is invoked successfully."""
        # Track command stats
        await track_command_stats(ctx, ctx.command.name, "prefix")
        # Send command log
        await send_command_log(ctx, ctx.command.name, "prefix")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global error handler for commands (CommandNotFound, Permissions, Cooldowns, etc.)."""
        if isinstance(error, commands.CommandNotFound):
            # Fuzzy match for typos
            command_name = ctx.invoked_with
            all_commands = [cmd.name for cmd in self.bot.commands if not cmd.hidden]
            similar = get_similar_commands(command_name, all_commands)
            
            if similar:
                embed = discord.Embed(
                    color=discord.Color.blue(),
                    description=f"`🤔` | Command not found. Did you mean: **{', '.join(similar[:3])}**?"
                )
                await ctx.reply(embed=embed)
            return

        elif isinstance(error, commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"`❌` | You lack the necessary permissions to execute this command: ```{missing}```"
            )
            await ctx.reply(embed=embed)
            return

        elif isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"`❌` | I lack the necessary permissions to execute this command: ```{missing}```"
            )
            await ctx.reply(embed=embed)
            return

        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"`❌` | Please wait **{error.retry_after:.1f}** more second(s) before reusing this command."
            )
            await ctx.reply(embed=embed)
            return

        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                color=discord.Color.blue(),
                description="`❌` | This command is owner-only. You cannot run this command."
            )
            await ctx.reply(embed=embed)
            return

        elif isinstance(error, commands.CheckFailure):
            # Generic check failure (admin, roles, etc.)
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                color=discord.Color.orange(),
                description=f"`⚠️` | Missing required argument: `{error.param.name}`"
            )
            await ctx.reply(embed=embed)
            return

        # Log other errors
        error_msg = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logger.error(f"Error in command {ctx.command}: {error}")
        
        # Send generic error message
        embed = discord.Embed(
            color=discord.Color.red(),
            description="`❌` | There was an error while executing this command!"
        )
        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction, command):
        """Called when a slash command is invoked successfully."""
        # Track command stats
        await track_command_stats(interaction, command.name, "slash")
        # Send command log
        await send_command_log(interaction, command.name, "slash")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle slash command interactions for custom checks."""
        if not interaction.type == discord.InteractionType.application_command:
            return
            
        # Get command
        command = self.bot.tree.get_command(interaction.data.get("name", ""))
        if not command:
            return

async def setup(bot):
    await bot.add_cog(Events(bot))
