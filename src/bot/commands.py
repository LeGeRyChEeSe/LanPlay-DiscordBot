"""Discord bot command handlers using discord.py."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.utils.lanplay_client import LanPlayClient, create_custom_server
from src.utils.rate_limiter import DISCOVERY_RATE_LIMITER, ADD_SERVER_RATE_LIMITER
from src.utils.server_manager import (
    load_custom_servers, save_custom_servers, 
    add_custom_server, remove_custom_server, get_custom_server_by_name
)
from src.utils.localization import get_localization, format_uptime_text
from src.utils.version import version_manager
from src.config.settings import LAN_MENU_URL, LAN_CONFIG_URL, IMAGE_LANPLAY_URL
from src.utils.constants import (
    MAX_SELECT_OPTIONS,
    SERVER_FORMAT_PATTERN,
)

logger = logging.getLogger(__name__)


class LanPlayCommands(commands.Cog):
    """LAN Play Discord bot commands."""

    def __init__(self, bot: commands.Bot, lan_servers: dict):
        self.bot = bot
        self.lan_servers = lan_servers
        self.lanplay_client = LanPlayClient()

    def _validate_server_format(self, server: str) -> bool:
        """Validate server format (hostname:port)."""
        return bool(SERVER_FORMAT_PATTERN.match(server))

    def _create_server_options(self, locale: discord.Locale) -> List[discord.SelectOption]:
        """Create server selection options sorted by uptime."""
        # Filter out servers without friendly_name and sort by uptime
        valid_servers = [
            server for server in self.lan_servers["monitors"]
            if server.get("friendly_name")  # Only include servers with friendly_name
        ]

        def _safe_uptime(server: dict) -> float:
            """Safely extract uptime ratio, defaulting to 0.0."""
            try:
                val = server.get("all_time_uptime_ratio", "0")
                return float(val) if val is not None else 0.0
            except (ValueError, TypeError):
                return 0.0

        sorted_servers = sorted(valid_servers, key=_safe_uptime, reverse=True)
        logger.info(f"_create_server_options: {len(self.lan_servers['monitors'])} total monitors, {len(valid_servers)} with friendly_name")

        options = []
        for server in sorted_servers[:MAX_SELECT_OPTIONS]:
            try:
                uptime_ratio = server.get("all_time_uptime_ratio", "0") or "0"
                desc = format_uptime_text(uptime_ratio, locale, self.bot) or ""
                label = str(server["friendly_name"])
                value = str(server["friendly_name"])
                options.append(discord.SelectOption(
                    label=label,
                    value=value,
                    description=desc
                ))
            except Exception as e:
                logger.warning(f"Skipping server {server.get('friendly_name', '?')}: {e}")

        # Always ensure at least one option to prevent Discord API validation error.
        if not options:
            label = get_localization(self.bot, "NO_SERVERS_AVAILABLE", locale) or \
                    "No servers available"
            description = get_localization(self.bot, "ADD_SERVERS_HINT", locale) or \
                          "Use /add to add a server"
            logger.warning(f"No valid servers found, using fallback option: label={label!r}")
            options = [
                discord.SelectOption(
                    label=label,
                    value="no_servers",
                    description=description,
                    default=True
                )
            ]

        logger.info(f"_create_server_options returning {len(options)} options")
        return options

    # Helper method to get timestamp
    def _get_timestamp(self) -> datetime:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc)

    @app_commands.command(name="lan", description="Display current games on LAN Play servers")
    async def lan_command(self, interaction: discord.Interaction):
        """Display current games on LAN Play servers."""
        # Rate limit check
        if not DISCOVERY_RATE_LIMITER.is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are using this command too frequently. Please wait a moment before trying again.",
                ephemeral=True
            )
            return

        try:
            embed = discord.Embed(color=discord.Color.blue())
            embed.set_thumbnail(url=IMAGE_LANPLAY_URL)
            embed.title = get_localization(self.bot, "SERVER_SELECT", interaction.locale)

            # Build options with defensive fallback — never send empty options to Discord
            server_options = self._create_server_options(interaction.locale)
            logger.info(f"lan_command: {len(server_options)} options generated")

            if not server_options or len(server_options) == 0:
                logger.warning("No server options generated for /lan command, using hardcoded fallback")
                server_options = [
                    discord.SelectOption(
                        label=get_localization(self.bot, "NO_SERVERS_AVAILABLE", interaction.locale) or get_localization(self.bot, "NO_SERVERS_AVAILABLE", discord.Locale.american_english) or "No servers available",
                        value="no_servers",
                        description=get_localization(self.bot, "ADD_SERVERS_HINT", interaction.locale) or get_localization(self.bot, "ADD_SERVERS_HINT", discord.Locale.american_english) or "Use /add to add a server",
                        default=True
                    )
                ]

            # Use factory function that properly creates Select with options for discord.py 2.x
            from src.bot.events import make_server_select_view

            logger.info(f"lan_command: calling make_server_select_view with {len(server_options)} options")
            view = make_server_select_view(
                bot=self.bot,
                lan_servers=self.lan_servers,
                user_id=str(interaction.user.id),
                options=server_options[:MAX_SELECT_OPTIONS],
                locale=interaction.locale
            )

            # Verify the Select has options before sending (safety check)
            select_item = None
            for item in view.children:
                if isinstance(item, discord.ui.Select):
                    select_item = item
                    break
            if not select_item or not getattr(select_item, 'options', None):
                logger.error("Select component has no options after construction! Using hardcoded fallback.")
                # Recreate with guaranteed options
                from src.bot.events import make_server_select_view as mssv
                view = mssv(
                    bot=self.bot,
                    lan_servers=self.lan_servers,
                    user_id=str(interaction.user.id),
                    options=[discord.SelectOption(label=get_localization(self.bot, "NO_SERVERS_AVAILABLE", interaction.locale) or get_localization(self.bot, "NO_SERVERS_AVAILABLE", discord.Locale.american_english) or "No servers available", value="no_servers", description=get_localization(self.bot, "ADD_SERVERS_HINT", interaction.locale) or get_localization(self.bot, "ADD_SERVERS_HINT", discord.Locale.american_english) or "Use /add to add a server", default=True)],
                    locale=interaction.locale
                )
                logger.info(f"lan_command: recreated Select with fallback options")

            # Verify AGAIN before sending
            final_select = None
            for item in view.children:
                if isinstance(item, discord.ui.Select):
                    final_select = item
                    break
            if not final_select or not getattr(final_select, 'options', None) or len(getattr(final_select, 'options', [])) == 0:
                logger.critical("CRITICAL: Select still has no options after all fallbacks! Creating emergency fallback.")
                from src.bot.events import make_server_select_view as mssv2
                view = mssv2(
                    bot=self.bot,
                    lan_servers=self.lan_servers,
                    user_id=str(interaction.user.id),
                    options=[discord.SelectOption(label="No servers available", value="no_servers", description="Use /add to add a server", default=True)],
                    locale=interaction.locale
                )

            # Add URL buttons to the view
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.url, 
                label=get_localization(self.bot, "SITE_LANPLAY", interaction.locale) or "LAN Play Website", 
                url=LAN_MENU_URL
            ))
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.url, 
                label=get_localization(self.bot, "CONFIG_LANPLAY", interaction.locale) or "Setup Guide", 
                url=LAN_CONFIG_URL
            ))

            await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error in /lan command: {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"An error occurred while loading server data. Please try again later.",
                    ephemeral=True
                )

    @app_commands.command(name="help", description="Display help menu for LAN's Bot commands")
    @app_commands.allowed_contexts(
        guilds=True,
        dms=True,
        private_channels=True
    )
    @app_commands.allowed_installs(
        guilds=True,
        users=True
    )
    async def help_command(self, interaction: discord.Interaction):
        """Display help menu for LAN's Bot commands."""
        # Rate limit check
        if not DISCOVERY_RATE_LIMITER.is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are using this command too frequently. Please wait a moment before trying again.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=get_localization(self.bot, "HELP_TITLE", interaction.locale),
            color=discord.Color.blue(),
            timestamp=self._get_timestamp()
        )
        embed.set_thumbnail(url=str(self.bot.user.display_avatar.url))

        description = ""
        for command in self.bot.tree.get_commands():
            localized_desc = get_localization(
                self.bot, f"{command.name.upper()}_DESCRIPTION", interaction.locale
            )
            description += f"`/{command.name}`: {localized_desc}\n"

        embed.description = description

        # Add version information
        version_info = version_manager.get_version_info()
        version_lines = [
            f"**Version:** {version_info['version']}",
            f"**Major:** {version_info['major']}",
            f"**Minor:** {version_info['minor']}",
            f"**Patch:** {version_info['patch']}",
        ]
        if version_info['prerelease']:
            version_lines.append(f"**Pre-release:** {version_info['prerelease']}")
        if version_info['build']:
            version_lines.append(f"**Build:** {version_info['build']}")
        version_value = "\n".join(version_lines)

        embed.add_field(
            name="📋 Version Details",
            value=version_value,
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add", description="Add a custom LAN Play server to the list")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_server_command(self, interaction: discord.Interaction, server: str):
        """Add a custom LAN Play server to the list."""
        # Rate limit check
        if not ADD_SERVER_RATE_LIMITER.is_allowed(interaction.user.id):
            await interaction.response.send_message(
                "You are using this command too frequently. Please wait a moment before trying again.",
                ephemeral=True
            )
            return
            
        if not self._validate_server_format(server):
            await interaction.response.send_message(
                get_localization(self.bot, "ADD_ERROR", interaction.locale),
                ephemeral=True
            )
            return

        custom_servers = await load_custom_servers()
        
        if not add_custom_server(custom_servers, server, self.lan_servers):
            await interaction.response.send_message(
                get_localization(self.bot, "ADD_EXISTS", interaction.locale, server=server),
                ephemeral=True
            )
            return

        if await save_custom_servers(custom_servers):
            # Update runtime server list
            self.lan_servers["monitors"].append(create_custom_server(server))
            await interaction.response.send_message(
                get_localization(self.bot, "ADD_SUCCESS", interaction.locale, server=server),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to save server configuration.",
                ephemeral=True
            )

    @app_commands.command(name="delete", description="Remove a custom LAN Play server from the list")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_server_command(self, interaction: discord.Interaction, server: str):
        """Remove a custom LAN Play server from the list."""
        if not self._validate_server_format(server):
            await interaction.response.send_message(
                get_localization(self.bot, "DELETE_ERROR", interaction.locale),
                ephemeral=True
            )
            return

        custom_servers = await load_custom_servers()
        custom_server = get_custom_server_by_name(custom_servers, server)
        
        if not custom_server:
            await interaction.response.send_message(
                get_localization(self.bot, "DELETE_ERROR", interaction.locale),
                ephemeral=True
            )
            return

        updated_servers = remove_custom_server(custom_servers, server)
        
        if await save_custom_servers(updated_servers):
            # Update runtime server list
            self.lan_servers["monitors"].remove(custom_server)
            await interaction.response.send_message(
                get_localization(self.bot, "DELETE_SUCCESS", interaction.locale, server=server),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Failed to save server configuration.",
                ephemeral=True
            )

    @delete_server_command.autocomplete('server')
    async def server_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for server deletion."""
        custom_servers = await load_custom_servers()
        return [
            app_commands.Choice(name=str(srv["friendly_name"]), value=str(srv["friendly_name"]))
            for srv in custom_servers
            if current.lower() in str(srv["friendly_name"]).lower()
        ][:25]  # Discord limits to 25 choices
