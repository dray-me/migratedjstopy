import discord
from core.logger import logger

# Mapping of event names to their required intents (matching Node.js discord.js structure)
REQUIRED_INTENTS = {
    'on_guild_join': 'guilds',
    'on_guild_update': 'guilds',
    'on_guild_remove': 'guilds',
    'on_guild_role_create': 'guilds',
    'on_guild_role_update': 'guilds',
    'on_guild_role_delete': 'guilds',
    'on_guild_channel_create': 'guilds',
    'on_guild_channel_update': 'guilds',
    'on_guild_channel_delete': 'guilds',
    'on_channel_create': 'guilds',
    'on_channel_update': 'guilds',
    'on_channel_delete': 'guilds',
    'on_thread_create': 'guilds',
    'on_thread_update': 'guilds',
    'on_thread_delete': 'guilds',
    'on_member_join': 'members',
    'on_member_update': 'members',
    'on_member_remove': 'members',
    'on_user_update': 'members',
    'on_message': ['messages', 'message_content', 'guild_messages'],
    'on_message_edit': ['messages', 'message_content', 'guild_messages'],
    'on_message_delete': ['messages', 'guild_messages'],
    'on_bulk_message_delete': ['messages', 'guild_messages'],
    'on_reaction_add': 'reactions',
    'on_reaction_remove': 'reactions',
    'on_reaction_clear': 'reactions',
    'on_typing': 'typing',
    'on_invite_create': 'invites',
    'on_invite_delete': 'invites',
    'on_webhooks_update': 'webhooks',
    'on_integration_create': 'integrations',
    'on_integration_update': 'integrations',
    'on_integration_delete': 'integrations',
    'on_guild_emojis_update': 'emojis',
    'on_guild_stickers_update': 'emojis',
    'on_voice_state_update': 'voice_states',
    'on_presence_update': 'presences',
    'on_scheduled_event_create': 'guild_scheduled_events',
    'on_scheduled_event_update': 'guild_scheduled_events',
    'on_scheduled_event_delete': 'guild_scheduled_events',
    'on_scheduled_event_user_add': 'guild_scheduled_events',
    'on_scheduled_event_user_remove': 'guild_scheduled_events',
    'on_auto_moderation_rule_create': 'auto_moderation_configuration',
    'on_auto_moderation_rule_update': 'auto_moderation_configuration',
    'on_auto_moderation_rule_delete': 'auto_moderation_configuration',
    'on_auto_moderation_action_execution': 'auto_moderation_execution',
}

def check_missing_intents(bot):
    """
    Checks if any registered event listeners require intents that the bot currently lacks.
    Matches the functionality of requiredIntents.js
    """
    missing_intents = set()
    current_intents = bot.intents
    
    # Get all event listeners from the bot
    all_listeners = []
    
    # Get listeners from cogs
    for cog in bot.cogs.values():
        for listener_name in cog.get_listeners():
            all_listeners.append(listener_name[0] if isinstance(listener_name, tuple) else listener_name)
    
    # Get extra events
    for event_name in bot.extra_events.keys():
        all_listeners.append(event_name)
    
    # Check each listener
    for event_name in all_listeners:
        required = REQUIRED_INTENTS.get(event_name)
        if not required:
            continue
            
        # Handle single intent or list of intents
        intent_list = [required] if isinstance(required, str) else required
        
        for intent_name in intent_list:
            intent_value = getattr(current_intents, intent_name, None)
            if intent_value is not None and not intent_value:
                missing_intents.add(intent_name)
    
    if missing_intents:
        msg = f"Missing gateway intents detected: {', '.join(missing_intents)}"
        logger.warning(msg)
        return list(missing_intents)
    
    return []
