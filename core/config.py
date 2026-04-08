"""
Config module - Re-export from bot_config for backward compatibility.
The configuration is now defined in bot_config.py as Python-native config.
"""
from core.bot_config import config, Config

__all__ = ['config', 'Config']
