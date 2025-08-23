"""Localization utilities for the Discord bot."""

import logging
from typing import Optional

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


def get_localization(
    bot: commands.InteractionBot, 
    key: str, 
    locale: disnake.Locale, 
    **kwargs
) -> Optional[str]:
    """
    Get localized text with optional formatting.
    
    Args:
        bot: The Discord bot instance
        key: The localization key
        locale: The user's locale
        **kwargs: Format parameters for string interpolation
        
    Returns:
        Localized text or None if not found
    """
    try:
        localized_text = bot.i18n.get(key).get(str(locale))
        
        if not localized_text:
            logger.warning(f"No localization found for key '{key}' and locale '{locale}'")
            return None
        
        # Replace format parameters
        for param_key, value in kwargs.items():
            placeholder = "{" + param_key + "}"
            localized_text = localized_text.replace(placeholder, str(value))
        
        return localized_text
        
    except Exception as e:
        logger.error(f"Failed to get localization for key '{key}': {e}")
        return None


def format_uptime_text(uptime_ratio: str, locale: disnake.Locale, bot: commands.InteractionBot) -> str:
    """
    Format uptime percentage with localized suffix.
    
    Args:
        uptime_ratio: The uptime ratio as string
        locale: User's locale
        bot: Bot instance for localization
        
    Returns:
        Formatted uptime text
    """
    uptime_suffix = get_localization(bot, 'UPTIME', locale)
    return f"{uptime_ratio}{uptime_suffix}" if uptime_suffix else f"{uptime_ratio}%"