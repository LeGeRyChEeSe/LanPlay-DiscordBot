"""Main Discord bot class and initialization."""

import locale
import logging
import os
import signal
import asyncio
from typing import Dict

import disnake
from disnake.ext import commands

from .commands import LanPlayCommands
from .events import LanPlayEvents
from ..utils.lanplay_client import get_lan_servers
from ..utils.server_manager import load_custom_servers
from ..config.settings import TOKEN, LOCALE_DIR, TIMEZONE, LOCALE_SETTING

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
_shutdown_requested = False


class LanPlayBot:
    """Main Discord bot for LAN Play server monitoring."""
    
    def __init__(self):
        self.bot: commands.InteractionBot = None
        self.lan_servers: Dict = {"monitors": []}
        self._setup_environment()
        self._initialize_bot()
        self._register_cogs()

    def _setup_environment(self):
        """Set up locale and timezone."""
        try:
            locale.setlocale(locale.LC_ALL, LOCALE_SETTING)
            os.environ['TZ'] = TIMEZONE
            logger.info(f"Environment configured: locale={LOCALE_SETTING}, tz={TIMEZONE}")
        except locale.Error as e:
            logger.warning(f"Failed to set locale {LOCALE_SETTING}: {e}")

    def _initialize_bot(self):
        """Initialize the Discord bot."""
        intents = disnake.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        self.bot = commands.InteractionBot(intents=intents)
        
        # Load localization files
        try:
            self.bot.i18n.load(LOCALE_DIR)
            logger.info(f"Loaded localization from {LOCALE_DIR}")
        except Exception as e:
            logger.error(f"Failed to load localization: {e}")

        @self.bot.event
        async def on_ready():
            logger.info(f"Logged in as {self.bot.user}")
            await self._load_servers_async()

    async def _load_servers_async(self):
        """Load LAN Play servers from API and custom servers (Async)."""
        try:
            # Load API servers
            api_servers = await get_lan_servers()
            self.lan_servers["monitors"] = api_servers.get("monitors", [])
            logger.info(f"Loaded {len(self.lan_servers['monitors'])} API servers")
            
            # Load and merge custom servers
            custom_servers = await load_custom_servers()
            self.lan_servers["monitors"].extend(custom_servers)
            logger.info(f"Added {len(custom_servers)} custom servers")
            
        except Exception as e:
            logger.error(f"Failed to load servers: {e}")
            self.lan_servers = {"monitors": []}

    def _register_cogs(self):
        """Register bot cogs."""
        try:
            self.bot.add_cog(LanPlayCommands(self.bot, self.lan_servers))
            self.bot.add_cog(LanPlayEvents(self.bot, self.lan_servers))
            logger.info("Registered all cogs successfully")
        except Exception as e:
            logger.error(f"Failed to register cogs: {e}")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals (SIGTERM, SIGINT)."""
        global _shutdown_requested
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        _shutdown_requested = True

    def run(self):
        """Start the bot."""
        if not TOKEN:
            logger.error("Discord bot token not found. Please set the TOKEN environment variable.")
            return

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

        try:
            logger.info("Starting LAN Play Discord Bot...")
            self.bot.run(TOKEN)
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
        finally:
            # Cleanup on shutdown
            logger.info("Bot shutdown complete")


def create_bot() -> LanPlayBot:
    """Create and return a LanPlayBot instance."""
    return LanPlayBot()