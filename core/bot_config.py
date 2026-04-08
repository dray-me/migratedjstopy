"""
Bot Configuration - Converted from config.json and discobase.json
This replaces the JSON configuration files with Python-native configuration.
"""
import os
from typing import List, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Helper function to parse comma-separated integers from env
def _parse_int_list(env_var: str, default: List[int] = None) -> List[int]:
    """Parse comma-separated integers from environment variable."""
    if default is None:
        default = []
    value = os.getenv(env_var, "")
    if not value:
        return default
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError:
        return default

# Helper function to parse optional int from env
def _parse_optional_int(env_var: str) -> Optional[int]:
    """Parse optional integer from environment variable."""
    value = os.getenv(env_var, "")
    if not value or value == "YOUR_ERROR_WEBHOOK_URL_HERE":
        return None
    try:
        return int(value)
    except ValueError:
        return None

# =============================================================================
# BOT CONFIGURATION (from config.json)
# =============================================================================

class BotConfig:
    """Bot configuration settings."""
    # Bot credentials
    TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    ID: str = os.getenv("BOT_ID", "YOUR_BOT_ID_HERE")
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0") or "0")  # Set to 0 as placeholder
    
    # Admin user IDs (comma-separated in ADMIN_IDS env var)
    ADMINS: List[int] = _parse_int_list("ADMIN_IDS")
    
    # Developer command server IDs (comma-separated in DEV_SERVER_IDS env var)
    DEV_SERVERS: List[int] = _parse_int_list("DEV_SERVER_IDS")

class DatabaseConfig:
    """Database configuration settings."""
    MONGODB_URL: str = os.getenv("MONGODB_URL", "YOUR_MONGODB_URL_HERE")

class LoggingConfig:
    """Logging configuration settings."""
    GUILD_JOIN_LOGS_ID: Optional[int] = _parse_optional_int("GUILD_JOIN_LOGS_ID")
    GUILD_LEAVE_LOGS_ID: Optional[int] = _parse_optional_int("GUILD_LEAVE_LOGS_ID")
    COMMAND_LOGS_CHANNEL_ID: Optional[int] = _parse_optional_int("COMMAND_LOGS_CHANNEL_ID")
    ERROR_WEBHOOK_URL: str = os.getenv("ERROR_WEBHOOK_URL", "YOUR_ERROR_WEBHOOK_URL_HERE")

class PrefixConfig:
    """Prefix configuration settings."""
    VALUE: str = os.getenv("BOT_PREFIX", "!")

# =============================================================================
# DISCOBASE CONFIGURATION (from discobase.json)
# =============================================================================

class ErrorLoggingConfig:
    """Error logging configuration."""
    ENABLED: bool = False

class PresenceConfig:
    """Bot presence configuration."""
    ENABLED: bool = False
    STATUS: str = "dnd"  # online, idle, dnd, invisible
    INTERVAL: int = 10000  # milliseconds
    TYPE: str = "PLAYING"  # PLAYING, STREAMING, LISTENING, WATCHING, COMPETING, CUSTOM
    NAMES: List[str] = [
        "with DiscoBase",
        "with commands",
        "with your server",
        "DiscoBase v3.0.0"
    ]
    STREAMING_URL: str = "https://www.twitch.tv/example"  # Only for STREAMING type
    CUSTOM_STATE: str = "🚀 discobase-py!"  # Only for CUSTOM type

class CommandStatsConfig:
    """Command statistics configuration."""
    ENABLED: bool = True
    TRACK_USAGE: bool = True
    TRACK_SERVERS: bool = True
    TRACK_USERS: bool = True

class ActivityTrackerConfig:
    """Activity tracker configuration."""
    ENABLED: bool = True
    IGNORED_PATHS: List[str] = [
        "**/__pycache__/**",
        "**/.git/**",
        ".gitignore",
        "*.pyc",
        "*.pyo",
        ".env",
        "errors/**",
    ]

# =============================================================================
# PROJECT METADATA (from package.json)
# =============================================================================

class ProjectMetadata:
    """Project metadata information."""
    NAME: str = "create-discobase"
    VERSION: str = "3.0.0"
    DESCRIPTION: str = "Easily create and manage your Discord bot with our powerful toolkit! 🚀"
    AUTHOR: str = "Ethical Programmer"
    LICENSE: str = "Apache-2.0"
    REPOSITORY_URL: str = "https://github.com/ethical-programmer/create-discobase"
    HOMEPAGE: str = "https://www.discobase.site/"
    
    KEYWORDS: List[str] = [
        "discord",
        "bot",
        "commands",
        "command handler",
        "event handler",
        "handler",
        "discobase",
        "toolkit",
        "discord.py"
    ]
    
    CONTRIBUTORS: List[dict] = [
        {"name": "Ethical Programmer", "url": "https://github.com/ethical-programmer"},
        {"name": "Krunal Patil", "url": "https://github.com/KrunalPatil6214"},
    ]

# =============================================================================
# COMBINED CONFIGURATION CLASS
# =============================================================================

class Config:
    """
    Main configuration class that combines all settings.
    This replaces the JSON-based config loading.
    """
    # Bot settings
    bot = BotConfig()
    database = DatabaseConfig()
    logging = LoggingConfig()
    prefix = PrefixConfig()
    
    # Discobase settings
    error_logging = ErrorLoggingConfig()
    presence = PresenceConfig()
    command_stats = CommandStatsConfig()
    activity_tracker = ActivityTrackerConfig()
    
    # Metadata
    meta = ProjectMetadata()
    
    # Convenience properties for backward compatibility
    @property
    def token(self) -> str:
        return self.bot.TOKEN
    
    @property
    def bot_id(self) -> str:
        return self.bot.ID
    
    @property
    def owner_id(self) -> int:
        return self.bot.OWNER_ID
    
    @property
    def admins(self) -> List[int]:
        return self.bot.ADMINS
    
    @property
    def dev_servers(self) -> List[int]:
        return self.bot.DEV_SERVERS
    
    @property
    def mongodb_url(self) -> str:
        return self.database.MONGODB_URL
    
    @property
    def prefix_value(self) -> str:
        return self.prefix.VALUE
    
    def is_configured(self) -> bool:
        """Check if the bot is properly configured."""
        return (
            self.bot.TOKEN != "YOUR_BOT_TOKEN_HERE" and
            self.bot.ID != "YOUR_BOT_ID_HERE" and
            self.bot.OWNER_ID != 0
        )

# Global config instance
config = Config()
