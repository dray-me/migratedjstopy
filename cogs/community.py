import discord
from discord import app_commands
from discord.ext import commands
import time
from core.config import config

class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping", 
        description="Check the bot's response time.",
        aliases=['p', 'latency']
    )
    @commands.cooldown(1, 3, commands.BucketType.user)  # 1 use per 3 seconds per user
    async def ping(self, ctx: commands.Context):
        """
        Standard ping command to check bot latency.
        Supports both Prefix ('!ping') and Slash ('/ping') invocations.
        """
        # Calculate heartbeat latency in ms
        latency = round(self.bot.latency * 1000)
        emoji = "⏱️"
        
        await ctx.reply(
            content=f"{emoji} Pong! Latency is {latency}ms!",
            ephemeral=False
        )

    @commands.hybrid_command(
        name="stats",
        description="Show bot statistics."
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stats(self, ctx: commands.Context):
        """Display bot statistics."""
        embed = discord.Embed(
            title="Bot Statistics",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count for g in self.bot.guilds)}", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Commands", value=f"{len(self.bot.commands)}", inline=True)
        
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="help",
        description="Show help information."
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def help_command(self, ctx: commands.Context):
        """Display help information."""
        embed = discord.Embed(
            title="Help - Available Commands",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        
        commands_list = []
        for cmd in self.bot.commands:
            if not cmd.hidden:
                aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
                commands_list.append(f"`{cmd.name}`{aliases} - {cmd.description or 'No description'}")
        
        embed.add_field(name="Commands", value="\n".join(commands_list) or "No commands available", inline=False)
        embed.set_footer(text=f"Use {config.prefix}command for prefix commands or /command for slash commands")
        
        await ctx.reply(embed=embed)

    # Admin-only command example
    @commands.hybrid_command(
        name="admincheck",
        description="Check if you have admin access."
    )
    @commands.check(lambda ctx: ctx.author.id in config.admins)
    async def admin_check(self, ctx: commands.Context):
        """Admin-only command to verify access."""
        await ctx.reply("✅ You have admin access!")

    @admin_check.error
    async def admin_check_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                color=discord.Color.blue(),
                description="`❌` | This command is admin-only. You cannot run this command."
            )
            await ctx.reply(embed=embed)

    # Owner-only command example
    @commands.hybrid_command(
        name="ownercheck",
        description="Check if you are the bot owner."
    )
    @commands.is_owner()
    async def owner_check(self, ctx: commands.Context):
        """Owner-only command to verify ownership."""
        await ctx.reply("✅ You are the bot owner!")

    @owner_check.error
    async def owner_check_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                color=discord.Color.blue(),
                description="`❌` | This command is owner-only. You cannot run this command."
            )
            await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Community(bot))
