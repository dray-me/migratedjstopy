from datetime import datetime
from core.database import db
from core.logger import logger
from core.bot_config import config

class CommandStats:
    """
    Command Statistics Model - Python equivalent of Mongoose CommandStats Schema
    Matches the schema from prefixCreate.js and interactionCreate.js
    """
    COLLECTION_NAME = "command_stats"

    def __init__(self, command_name: str, command_type: str):
        self.command_name = command_name
        self.command_type = command_type  # 'slash' or 'prefix'
        self.total_uses = 0
        self.servers = []  # List of {serverId, serverName, uses}
        self.users = []    # List of {userId, username, uses}
        self.last_used = datetime.utcnow()

    @classmethod
    async def find_one(cls, command_name: str, command_type: str):
        """Finds a stats record in MongoDB."""
        if not db.db:
            return None
            
        data = await db.db[cls.COLLECTION_NAME].find_one({
            "commandName": command_name,
            "commandType": command_type
        })
        
        if not data:
            return None
            
        stats = cls(command_name, command_type)
        stats.total_uses = data.get("totalUses", 0)
        stats.servers = data.get("servers", [])
        stats.users = data.get("users", [])
        stats.last_used = data.get("lastUsed", datetime.utcnow())
        return stats

    async def save(self):
        """Saves or updates the stats record in MongoDB."""
        if not db.db:
            return

        data = {
            "commandName": self.command_name,
            "commandType": self.command_type,
            "totalUses": self.total_uses,
            "servers": self.servers,
            "users": self.users,
            "lastUsed": self.last_used
        }
        
        await db.db[self.COLLECTION_NAME].update_one(
            {"commandName": self.command_name, "commandType": self.command_type},
            {"$set": data},
            upsert=True
        )

    async def track(self, guild_id: str, guild_name: str, user_id: str, username: str):
        """
        Increments usage statistics for a command.
        Matches the tracking logic from prefixCreate.js and interactionCreate.js
        """
        # Check if tracking is enabled
        if not self._is_tracking_enabled():
            return
            
        self.total_uses += 1
        self.last_used = datetime.utcnow()
        
        # Track server (if not DM and tracking enabled)
        if guild_id and self._is_server_tracking_enabled():
            server_index = next((i for i, s in enumerate(self.servers) if s["serverId"] == guild_id), -1)
            if server_index >= 0:
                self.servers[server_index]["uses"] += 1
                self.servers[server_index]["serverName"] = guild_name
            else:
                self.servers.append({"serverId": guild_id, "serverName": guild_name, "uses": 1})
            
            # Sort servers by uses descending (matching JS behavior)
            self.servers.sort(key=lambda x: x["uses"], reverse=True)
            
        # Track user (if tracking enabled)
        if self._is_user_tracking_enabled():
            user_index = next((i for i, u in enumerate(self.users) if u["userId"] == user_id), -1)
            if user_index >= 0:
                self.users[user_index]["uses"] += 1
                self.users[user_index]["username"] = username
            else:
                self.users.append({"userId": user_id, "username": username, "uses": 1})
            
            # Sort users by uses descending (matching JS behavior)
            self.users.sort(key=lambda x: x["uses"], reverse=True)
        
        await self.save()

    def _is_tracking_enabled(self):
        """Check if command stats tracking is enabled."""
        return config.command_stats.ENABLED

    def _is_server_tracking_enabled(self):
        """Check if server tracking is enabled."""
        return config.command_stats.TRACK_SERVERS

    def _is_user_tracking_enabled(self):
        """Check if user tracking is enabled."""
        return config.command_stats.TRACK_USERS


class GuildSettings:
    """
    Guild Settings Model - For per-server configuration
    Equivalent to guild settings in MongoDB
    """
    COLLECTION_NAME = "guild_settings"

    def __init__(self, guild_id: str):
        self.guild_id = guild_id
        self.prefix = None  # Custom prefix (None = use global)
        self.disabled_commands = []
        self.log_channel = None
        self.welcome_channel = None
        self.auto_role = None

    @classmethod
    async def find_one(cls, guild_id: str):
        """Find guild settings by ID."""
        if not db.db:
            return None
            
        data = await db.db[cls.COLLECTION_NAME].find_one({"guildId": guild_id})
        
        if not data:
            return None
            
        settings = cls(guild_id)
        settings.prefix = data.get("prefix")
        settings.disabled_commands = data.get("disabledCommands", [])
        settings.log_channel = data.get("logChannel")
        settings.welcome_channel = data.get("welcomeChannel")
        settings.auto_role = data.get("autoRole")
        return settings

    async def save(self):
        """Save guild settings to MongoDB."""
        if not db.db:
            return

        data = {
            "guildId": self.guild_id,
            "prefix": self.prefix,
            "disabledCommands": self.disabled_commands,
            "logChannel": self.log_channel,
            "welcomeChannel": self.welcome_channel,
            "autoRole": self.auto_role
        }
        
        await db.db[self.COLLECTION_NAME].update_one(
            {"guildId": self.guild_id},
            {"$set": data},
            upsert=True
        )
