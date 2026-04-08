"""
Command checks utility - Python equivalent of permission/cooldown checks from prefixCreate.js and interactionCreate.js
"""
import discord
from discord.ext import commands
from core.config import config
from core.bot_config import config as bot_config
from core.logger import logger
from core.models import CommandStats
import time

# Global cooldown storage
cooldowns = {}

async def check_admin_only(ctx, is_admin_only=False):
    """Check if command is admin-only."""
    if not is_admin_only:
        return True
    if ctx.author.id in config.admins:
        return True
    
    embed = discord.Embed(
        color=discord.Color.blue(),
        description="`❌` | This command is admin-only. You cannot run this command."
    )
    await ctx.reply(embed=embed)
    return False

async def check_owner_only(ctx, is_owner_only=False):
    """Check if command is owner-only."""
    if not is_owner_only:
        return True
    if ctx.author.id == config.owner_id:
        return True
    
    embed = discord.Embed(
        color=discord.Color.blue(),
        description="`❌` | This command is owner-only. You cannot run this command."
    )
    await ctx.reply(embed=embed)
    return False

async def check_user_permissions(ctx, required_perms=None):
    """Check if user has required permissions."""
    if not required_perms:
        return True
    
    missing_perms = []
    for perm in required_perms:
        if not getattr(ctx.author.guild_permissions, perm.lower(), False):
            missing_perms.append(perm)
    
    if missing_perms:
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"`❌` | You lack the necessary permissions to execute this command: ```{', '.join(missing_perms)}```"
        )
        await ctx.reply(embed=embed)
        return False
    return True

async def check_bot_permissions(ctx, required_perms=None):
    """Check if bot has required permissions."""
    if not required_perms:
        return True
    
    missing_perms = []
    bot_member = ctx.guild.me if ctx.guild else None
    if not bot_member:
        return True
        
    for perm in required_perms:
        if not getattr(bot_member.guild_permissions, perm.lower(), False):
            missing_perms.append(perm)
    
    if missing_perms:
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"`❌` | I lack the necessary permissions to execute this command: ```{', '.join(missing_perms)}```"
        )
        await ctx.reply(embed=embed)
        return False
    return True

async def check_required_roles(ctx, required_roles=None):
    """Check if user has required roles."""
    if not required_roles:
        return True
    
    if not ctx.guild:
        embed = discord.Embed(
            color=discord.Color.blue(),
            description="`❌` | This command can only be used in a server."
        )
        await ctx.reply(embed=embed)
        return False
    
    user_roles = [role.id for role in ctx.author.roles]
    has_role = any(int(role_id) in user_roles for role_id in required_roles)
    
    if not has_role:
        embed = discord.Embed(
            color=discord.Color.blue(),
            description="`❌` | You don't have the required role(s) to use this command."
        )
        await ctx.reply(embed=embed)
        return False
    return True

async def check_cooldown(ctx, cooldown_seconds=3):
    """Check and handle command cooldown."""
    global cooldowns
    
    command_name = ctx.command.name if ctx.command else "unknown"
    user_id = ctx.author.id
    
    if command_name not in cooldowns:
        cooldowns[command_name] = {}
    
    now = time.time()
    if user_id in cooldowns[command_name]:
        expiration_time = cooldowns[command_name][user_id] + cooldown_seconds
        if now < expiration_time:
            time_left = expiration_time - now
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"`❌` | Please wait **{time_left:.1f}** more second(s) before reusing the `{command_name}` command."
            )
            await ctx.reply(embed=embed)
            return False
    
    cooldowns[command_name][user_id] = now
    return True

async def track_command_stats(ctx, command_name: str, command_type: str = "prefix"):
    """Track command usage statistics."""
    try:
        # Check if stats tracking is enabled
        if not bot_config.command_stats.ENABLED:
            return
        
        guild_id = str(ctx.guild.id) if ctx.guild else None
        guild_name = ctx.guild.name if ctx.guild else None
        user_id = str(ctx.author.id)
        username = str(ctx.author)
        
        stats = await CommandStats.find_one(command_name, command_type)
        if not stats:
            stats = CommandStats(command_name, command_type)
        
        await stats.track(guild_id, guild_name, user_id, username)
        
    except Exception as e:
        logger.warning(f"Failed to track command stats: {e}")

async def send_command_log(ctx, command_name: str, command_type: str = "prefix"):
    """Send command execution log to configured channel."""
    try:
        channel_id = config.logging.COMMAND_LOGS_CHANNEL_ID
        if not channel_id or channel_id == "COMMAND_LOGS_CHANNEL_ID":
            return
        
        channel = ctx.bot.get_channel(int(channel_id))
        if not channel:
            return
        
        embed = discord.Embed(
            title="Command Executed",
            color=discord.Color.white(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Command", value=f"{config.prefix}{command_name}" if command_type == "prefix" else f"/{command_name}", inline=False)
        embed.add_field(name="Server", value=f"{ctx.guild.name} ({ctx.guild.id})" if ctx.guild else "Direct Message", inline=False)
        
        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        else:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await channel.send(embed=embed)
        
    except Exception as e:
        logger.warning(f"Failed to send command log: {e}")
