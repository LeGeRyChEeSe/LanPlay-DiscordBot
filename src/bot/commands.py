"""Discord bot command handlers."""

import logging
import re
from datetime import datetime, timezone
from typing import List

import disnake
from disnake import SelectOption
from disnake.ext import commands
from disnake.ui import Button, Select

from ..utils.lanplay_client import LanPlayClient
from ..utils.server_manager import (
    load_custom_servers, save_custom_servers, 
    add_custom_server, remove_custom_server, get_custom_server_by_name
)
from ..utils.localization import get_localization, format_uptime_text
from ..utils.version import version_manager
from ..utils.changelog import changelog_manager, ChangeType
from ..config.settings import LAN_MENU_URL, LAN_CONFIG_URL, IMAGE_LANPLAY_URL

logger = logging.getLogger(__name__)


def get_timestamp() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class LanPlayCommands(commands.Cog):
    """LAN Play Discord bot commands."""
    
    def __init__(self, bot: commands.InteractionBot, lan_servers: dict):
        self.bot = bot
        self.lan_servers = lan_servers
        self.lanplay_client = LanPlayClient()

    @commands.slash_command(name="lan")
    async def lan_command(self, inter: disnake.ApplicationCommandInteraction):
        """Display current games on LAN Play servers. {{LAN_DESCRIPTION}}"""
        embed = disnake.Embed(color=disnake.Color.blue())
        embed.set_thumbnail(url=IMAGE_LANPLAY_URL)
        embed.title = get_localization(self.bot, "SERVER_SELECT", inter.locale)

        components = [
            Button(
                style=disnake.ButtonStyle.url, 
                label=get_localization(self.bot, "SITE_LANPLAY", inter.locale), 
                url=LAN_MENU_URL
            ),
            Button(
                style=disnake.ButtonStyle.url, 
                label=get_localization(self.bot, "CONFIG_LANPLAY", inter.locale), 
                url=LAN_CONFIG_URL
            ),
            Select(
                placeholder=get_localization(self.bot, "SERVER_SELECT_BUTTON", inter.locale),
                custom_id=f"lan_servers_{inter.author.id}",
                options=self._create_server_options(inter.locale)[:25]
            )
        ]

        await inter.response.send_message(embed=embed, components=components)

    @commands.slash_command(name="help", contexts=disnake.InteractionContextTypes.guild | disnake.InteractionContextTypes.bot_dm | disnake.InteractionContextTypes.private_channel)
    async def help_command(self, inter: disnake.ApplicationCommandInteraction):
        """Display help menu for LAN's Bot commands. {{HELP_DESCRIPTION}}"""
        embed = disnake.Embed(
            title=get_localization(self.bot, "HELP_TITLE", inter.locale),
            color=disnake.Color.blue(),
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(self.bot.user.display_avatar.url)
        
        description = ""
        for command in self.bot.slash_commands:
            localized_desc = get_localization(
                self.bot, f"{command.name.upper()}_DESCRIPTION", inter.locale
            )
            description += f"`/{command.qualified_name}`: {localized_desc}\\n"
        
        embed.description = description
        
        # Add version information
        version_info = version_manager.get_version_info()
        embed.add_field(
            name="Version", 
            value=f"v{version_info['version']}", 
            inline=True
        )
        
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="version", contexts=disnake.InteractionContextTypes.guild | disnake.InteractionContextTypes.bot_dm | disnake.InteractionContextTypes.private_channel)
    async def version_command(self, inter: disnake.ApplicationCommandInteraction):
        """Display bot version and build information. {{VERSION_DESCRIPTION}}"""
        version_info = version_manager.get_version_info()
        
        embed = disnake.Embed(
            title=f"🤖 LAN Play Bot v{version_info['version']}",
            color=disnake.Color.green(),
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(self.bot.user.display_avatar.url)
        
        # Version details
        embed.add_field(
            name="📋 Version Details",
            value=(
                f"**Version:** {version_info['version']}\n"
                f"**Major:** {version_info['major']}\n"
                f"**Minor:** {version_info['minor']}\n"
                f"**Patch:** {version_info['patch']}"
                f"{('\n**Pre-release:** ' + version_info['prerelease']) if version_info['prerelease'] else ''}"
                f"{('\n**Build:** ' + version_info['build']) if version_info['build'] else ''}"
            ),
            inline=False
        )
        
        # Build information
        embed.add_field(
            name="🔨 Build Information",
            value=(
                f"**Built:** {datetime.fromisoformat(version_info['build_date']).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"**Type:** {'Pre-release' if version_info['is_prerelease'] else 'Release'}"
            ),
            inline=False
        )
        
        # Get latest changes
        unreleased = changelog_manager.get_unreleased_changes()
        if unreleased and unreleased.has_changes():
            embed.add_field(
                name="🚧 Upcoming Changes",
                value=f"{unreleased.get_total_changes()} changes pending release",
                inline=True
            )
        
        embed.set_footer(text="Use /changelog to see recent changes")
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="changelog", contexts=disnake.InteractionContextTypes.guild | disnake.InteractionContextTypes.bot_dm | disnake.InteractionContextTypes.private_channel)
    async def changelog_command(self, inter: disnake.ApplicationCommandInteraction):
        """Display recent changes and updates. {{CHANGELOG_DESCRIPTION}}"""
        latest_changes = changelog_manager.get_latest_changes(3)
        
        embed = disnake.Embed(
            title="📝 Recent Changes",
            color=disnake.Color.blue(),
            timestamp=get_timestamp()
        )
        embed.set_thumbnail(self.bot.user.display_avatar.url)
        
        if not latest_changes:
            embed.description = "No version history available yet."
        else:
            for version_entry in latest_changes:
                changes_text = ""
                
                for change_type in ChangeType:
                    entries = version_entry.changes.get(change_type, [])
                    if entries:
                        changes_text += f"**{change_type.value}:**\n"
                        for entry in entries[:3]:  # Limit to 3 entries per type
                            changes_text += f"• {entry.description}\n"
                        if len(entries) > 3:
                            changes_text += f"• ... and {len(entries) - 3} more\n"
                        changes_text += "\n"
                
                if changes_text:
                    embed.add_field(
                        name=f"v{version_entry.version} ({version_entry.date.strftime('%Y-%m-%d')})",
                        value=changes_text[:1024],  # Discord field limit
                        inline=False
                    )
        
        # Add unreleased changes if any
        unreleased = changelog_manager.get_unreleased_changes()
        if unreleased and unreleased.has_changes():
            unreleased_text = ""
            for change_type in ChangeType:
                entries = unreleased.changes.get(change_type, [])
                if entries:
                    unreleased_text += f"**{change_type.value}:**\n"
                    for entry in entries[:3]:
                        unreleased_text += f"• {entry.description}\n"
                    if len(entries) > 3:
                        unreleased_text += f"• ... and {len(entries) - 3} more\n"
                    unreleased_text += "\n"
            
            if unreleased_text:
                embed.add_field(
                    name="🚧 Unreleased Changes",
                    value=unreleased_text[:1024],
                    inline=False
                )
        
        embed.set_footer(text="Full changelog available in CHANGELOG.md")
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="add")
    @commands.default_member_permissions(administrator=True)
    async def add_server_command(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        server: str
    ):
        """
        Add a custom LAN Play server to the list. {{ADD_DESCRIPTION}}

        Parameters
        ----------
        server: :class:`str`
            The custom server to add (e.g., 'example.com:11451') {{ADD_PARAMETER}}
        """
        if not self._validate_server_format(server):
            await inter.response.send_message(
                get_localization(self.bot, "ADD_ERROR", inter.locale), 
                ephemeral=True
            )
            return

        custom_servers = load_custom_servers()
        
        if not add_custom_server(custom_servers, server, self.lan_servers):
            await inter.response.send_message(
                get_localization(self.bot, "ADD_EXISTS", inter.locale, server=server),
                ephemeral=True
            )
            return

        if save_custom_servers(custom_servers):
            # Update runtime server list
            from ..utils.lanplay_client import create_custom_server
            self.lan_servers["monitors"].append(create_custom_server(server))
            
            await inter.response.send_message(
                get_localization(self.bot, "ADD_SUCCESS", inter.locale, server=server),
                ephemeral=True
            )
        else:
            await inter.response.send_message(
                "Failed to save server configuration.", 
                ephemeral=True
            )

    @commands.slash_command(name="delete")
    @commands.default_member_permissions(administrator=True)
    async def delete_server_command(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        server: str
    ):
        """
        Remove a custom LAN Play server from the list. {{DELETE_DESCRIPTION}}

        Parameters
        ----------
        server: :class:`str`
            The custom server to remove (e.g., 'example.com:11451') {{DELETE_PARAMETER}}
        """
        if not self._validate_server_format(server):
            await inter.response.send_message(
                get_localization(self.bot, "DELETE_ERROR", inter.locale),
                ephemeral=True
            )
            return

        custom_servers = load_custom_servers()
        custom_server = get_custom_server_by_name(custom_servers, server)
        
        if not custom_server:
            await inter.response.send_message(
                f"Server {server} not found in custom servers.",
                ephemeral=True
            )
            return

        updated_servers = remove_custom_server(custom_servers, server)
        
        if save_custom_servers(updated_servers):
            # Update runtime server list
            self.lan_servers["monitors"].remove(custom_server)
            
            await inter.response.send_message(
                get_localization(self.bot, "DELETE_SUCCESS", inter.locale, server=server),
                ephemeral=True
            )
        else:
            await inter.response.send_message(
                "Failed to save server configuration.",
                ephemeral=True
            )

    @delete_server_command.autocomplete("server")
    async def server_autocomplete(
        self, 
        inter: disnake.ApplicationCommandInteraction, 
        server: str
    ) -> List[str]:
        """Autocomplete for server deletion."""
        custom_servers = load_custom_servers()
        return [srv["friendly_name"] for srv in custom_servers]

    def _create_server_options(self, locale: disnake.Locale) -> List[SelectOption]:
        """Create server selection options sorted by uptime."""
        sorted_servers = sorted(
            self.lan_servers["monitors"], 
            key=lambda x: x.get("all_time_uptime_ratio", "0"), 
            reverse=True
        )
        
        return [
            SelectOption(
                label=server["friendly_name"],
                value=server["friendly_name"],
                description=format_uptime_text(
                    server.get("all_time_uptime_ratio", "0"), 
                    locale, 
                    self.bot
                )
            )
            for server in sorted_servers
        ]

    @staticmethod
    def _validate_server_format(server: str) -> bool:
        """Validate server format (hostname:port)."""
        pattern = r'^[a-zA-Z0-9.-]+:\\d+$'
        return bool(re.match(pattern, server))