"""Discord bot event handlers."""

import logging
from datetime import datetime, timezone
from typing import List

import discord
import aiohttp
from discord.ext import commands

from src.utils.lanplay_client import LanPlayClient
from src.utils.localization import get_localization, format_uptime_text
from src.config.settings import IMAGE_LANPLAY_URL, LAN_MENU_URL
from src.utils.constants import EMOJI_LIMIT_STANDARD, EMOJI_LIMIT_SOFT

logger = logging.getLogger(__name__)


def _build_select_component(
    bot: commands.Bot,
    user_id: str,
    options: List[discord.SelectOption],
    locale=None
) -> dict:
    """Build a raw Select component dict with guaranteed non-empty options."""
    _fallback_locale = discord.Locale.american_english

    # Ensure at least one option
    if not options or len(options) == 0:
        label = (get_localization(bot, "NO_SERVERS_AVAILABLE", locale) or
                 get_localization(bot, "NO_SERVERS_AVAILABLE", _fallback_locale) or
                 "No servers available")
        description = (get_localization(bot, "ADD_SERVERS_HINT", locale) or
                       get_localization(bot, "ADD_SERVERS_HINT", _fallback_locale) or
                       "Use /add to add a server")
        options = [discord.SelectOption(label=label, value="no_servers", description=description)]

    logger.info(f"_build_select_component: building with {len(options)} options")

    # Convert SelectOptions to raw dicts for the component
    raw_options = []
    for opt in options:
        raw_opt = {"label": str(opt.label), "value": str(opt.value)}
        if hasattr(opt, 'description') and opt.description:
            raw_opt["description"] = str(opt.description)
        if hasattr(opt, 'default') and opt.default:
            raw_opt["default"] = True
        raw_options.append(raw_opt)

    placeholder = (get_localization(bot, "SERVER_SELECT_BUTTON", locale) or
                   get_localization(bot, "SERVER_SELECT_BUTTON", _fallback_locale) or
                   "Select a server to view games")

    return {
        "type": 3,  # Select component type
        "custom_id": f"lan_server_{user_id}",
        "min_values": 1,
        "max_values": 1,
        "placeholder": placeholder,
        "options": raw_options,
    }


def make_server_select_view(
    bot: commands.Bot,
    lan_servers: dict,
    user_id: str,
    options: List[discord.SelectOption],
    locale=None
) -> discord.ui.View:
    """Create a ServerSelectView with the given options.

    Uses raw component dicts to avoid discord.py subclass serialization issues.
    """

    class ServerSelect(discord.ui.Select):
        def __init__(self, bot, lan_servers, user_id, opts, locale=None):
            self._locale = locale or discord.Locale.american_english
            # Build a placeholder for super().__init__ so it doesn't crash
            _fallback_locale = discord.Locale.american_english
            placeholder_opt = discord.SelectOption(
                label=(get_localization(bot, "NO_SERVERS_AVAILABLE", self._locale) or
                       get_localization(bot, "NO_SERVERS_AVAILABLE", _fallback_locale) or
                       "No servers available"),
                value="no_servers",
            )

            super().__init__(
                custom_id=f"lan_server_{user_id}",
                min_values=1,
                max_values=1,
                options=[placeholder_opt],  # minimal placeholder — replaced after init
            )

            # Replace with real options after init
            if opts and len(opts) > 0:
                self.options = list(opts)
                logger.info(f"ServerSelect.__init__: set {len(self.options)} real options")
            else:
                logger.warning("ServerSelect.__init__: no valid options, keeping placeholder")

            self.bot = bot
            self.lan_servers = lan_servers
            self.user_id = user_id

        async def callback(self, interaction: discord.Interaction):
            """Handle server selection from dropdown."""
            if str(interaction.user.id) != self.user_id:
                await _send_permission_error(
                    self.bot, interaction, self.user_id
                )
                return

            values = interaction.data.get("values", [])
            if not values:
                return

            server_name = values[0]
            lan_server_url = f"http://{server_name}/"

            # Show loading embed
            await interaction.response.defer()

            loading_embed = discord.Embed(color=discord.Color.blue())
            loading_embed.title = get_localization(
                self.bot, "EMBED_TITLE", interaction.locale
            )
            loading_embed.description = get_localization(
                self.bot, "EMBED_DESCRIPTION", interaction.locale
            )
            try:
                await interaction.edit_original_response(embed=loading_embed)
            except Exception as e:
                logger.error(f"Failed to send loading embed: {e}")

            # Create main embed
            embed = discord.Embed(color=discord.Color.blue())
            embed.title = server_name
            embed.url = LAN_MENU_URL
            embed.set_thumbnail(url=IMAGE_LANPLAY_URL)

            # Add uptime footer
            uptime_ratio = _get_server_uptime(self.lan_servers, server_name)
            if interaction.guild:
                embed.set_footer(
                    text=format_uptime_text(
                        uptime_ratio, interaction.locale, self.bot
                    ),
                    icon_url=(
                        interaction.guild.icon.url
                        if interaction.guild.icon
                        else None
                    ),
                )

            # Fetch server data
            try:
                client = LanPlayClient()
                server_data = await client.get_server_info(lan_server_url)
            except Exception as e:
                logger.error(
                    f"Failed to fetch server info for {server_name}: {e}"
                )
                error_msg = (get_localization(
                    self.bot, "EMBED_ERROR_DESCRIPTION", interaction.locale
                ) or get_localization(
                    self.bot, "EMBED_ERROR_DESCRIPTION", discord.Locale.american_english
                ) or "❌ Error: Could not reach the server.")
                err_str = str(e).lower()
                if "cannot connect" in err_str or "connect call failed" in err_str:
                    error_msg += "\n\n⚠️ " + (get_localization(self.bot, "ERROR_UNREACHABLE", interaction.locale) or
                                              get_localization(self.bot, "ERROR_UNREACHABLE", discord.Locale.american_english) or
                                              "Server unreachable (timeout or firewall)")
                elif "name or service not known" in err_str:
                    error_msg += "\n\n⚠️ " + (get_localization(self.bot, "ERROR_DNS", interaction.locale) or
                                             get_localization(self.bot, "ERROR_DNS", discord.Locale.american_english) or
                                             "DNS not found — server no longer accessible")
                embed.description = error_msg
            else:
                if not server_data or "room" not in server_data:
                    embed.description = (get_localization(
                        self.bot,
                        "EMBED_ERROR_DESCRIPTION",
                        interaction.locale,
                    ) or get_localization(
                        self.bot,
                        "EMBED_ERROR_DESCRIPTION",
                        discord.Locale.american_english,
                    ) or "❌ Error: Could not reach the server.") + "\n\n⚠️ " + (get_localization(self.bot, "ERROR_NO_LANPLAY", interaction.locale) or
                                                                                   get_localization(self.bot, "ERROR_NO_LANPLAY", discord.Locale.american_english) or
                                                                                   "Server does not respond to LAN Play protocol")
                else:
                    try:
                        await _populate_server_embed(
                            self.bot, embed, server_data, interaction
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to populate server embed for {server_name}: {e}"
                        )
                        embed.description = get_localization(
                            self.bot,
                            "EMBED_ERROR_DESCRIPTION",
                            interaction.locale,
                        )

            embed.timestamp = datetime.now(timezone.utc)
            try:
                await interaction.edit_original_response(embed=embed)
            except Exception as e:
                logger.error(f"Failed to edit response with server data: {e}")

    view = discord.ui.View()
    view.add_item(ServerSelect(bot, lan_servers, user_id, options, locale))
    return view


async def _send_permission_error(
    bot: commands.Bot, interaction: discord.Interaction, owner_id: str
):
    """Send permission error message."""
    embed = discord.Embed(
        title=get_localization(bot, "NO_PERMS_TITLE", interaction.locale),
        colour=discord.Color.red(),
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )

    if interaction.guild:
        try:
            owner = await interaction.guild.get_or_fetch_member(int(owner_id))
            if owner:
                footer_text = get_localization(
                    bot, "NO_PERMS_FOOTER", interaction.locale, member=owner
                )
                embed.set_footer(text=footer_text)
        except (ValueError, discord.NotFound):
            pass

    await interaction.response.send_message(embed=embed, ephemeral=True)


def _get_server_uptime(lan_servers: dict, server_name: str) -> str:
    """Get uptime ratio for a server."""
    for server in lan_servers.get("monitors", []):
        if server.get("friendly_name") == server_name:
            return server.get("all_time_uptime_ratio", "0")
    return "0"


async def _populate_server_embed(
    bot: commands.Bot,
    embed: discord.Embed,
    server_data: dict,
    interaction: discord.Interaction,
):
    """Populate embed with server information."""
    rooms = server_data.get("room", [])
    server_info = server_data.get("serverInfo", {})

    online_players = server_info.get("online", 0)
    idle_players = server_info.get("idle", 0)
    active_players = online_players - idle_players

    embed.description = f"{active_players} :video_game: / {idle_players} :zzz:"

    # Set author based on room count
    room_count = len(rooms)
    if room_count > 1:
        author_text = f"{room_count} {get_localization(bot, 'MULTIPLE_GAME', interaction.locale)}"
    elif room_count == 1:
        author_text = f"{room_count} {get_localization(bot, 'ONE_GAME', interaction.locale)}"
    else:
        author_text = get_localization(bot, "NO_GAME", interaction.locale)

    embed.set_author(name=author_text, icon_url=interaction.user.display_avatar.url)

    # Add room information
    created_emojis: List[discord.Emoji] = []
    for room in rooms:
        await _add_room_field(
            bot, embed, room, interaction, created_emojis
        )


async def _add_room_field(
    bot: commands.Bot,
    embed: discord.Embed,
    room: dict,
    interaction: discord.Interaction,
    created_emojis: List[discord.Emoji],
):
    """Add a room field to the embed."""
    node_count = room.get("nodeCount", 0)
    node_max = room.get("nodeCountMax", 0)
    status_icon = ":x:" if node_count == node_max else ":white_check_mark:"
    player_info = f"({node_count}/{node_max}) {status_icon}"

    # Get player list
    players = [
        node.get("playerName", "Unknown") for node in room.get("nodes", [])
    ]
    players_text = ",\n".join(players)

    # Extract host information
    try:
        advertise_data = room.get("advertiseData", "")
        if len(advertise_data) > 94:
            host_data = advertise_data[56:94].replace("00", "")
            host_name = bytearray.fromhex(host_data).decode(
                "utf-8", errors="ignore"
            )
        else:
            host_name = "Unknown"
    except (ValueError, UnicodeDecodeError):
        host_name = "Unknown"

    host_player = room.get("hostPlayerName", "Unknown")
    game_host_text = get_localization(bot, "GAME_HOST", interaction.locale)
    players_text_label = get_localization(bot, "PLAYERS", interaction.locale)

    # Create field value
    field_value = (
        f"{game_host_text} {host_name} ({host_player})\n"
        f"**{players_text_label}:**\n{players_text}"
    )

    # Handle game icon
    if "iconUrl" in room and interaction.guild:
        await _add_room_with_icon(
            bot, embed, room, player_info, field_value, interaction, created_emojis
        )
    else:
        game_playing_text = get_localization(
            bot, "GAME_PLAYING", interaction.locale
        )
        embed.add_field(name=game_playing_text, value=field_value, inline=False)


async def _add_room_with_icon(
    bot: commands.Bot,
    embed: discord.Embed,
    room: dict,
    player_info: str,
    field_value: str,
    interaction: discord.Interaction,
    created_emojis: List[discord.Emoji],
):
    """Add room field with custom emoji icon."""
    try:
        content_id = room.get("contentId", "unknown")
        emoji_name = content_id[:32].lower()

        # Check if emoji already exists in guild
        emoji = discord.utils.get(interaction.guild.emojis, name=emoji_name)

        if not emoji:
            # Cleanup if limit reached (Discord limit is EMOJI_LIMIT_STANDARD for non-boosted server)
            if len(interaction.guild.emojis) >= EMOJI_LIMIT_SOFT:
                await _cleanup_oldest_emoji(interaction.guild)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    room["iconUrl"], timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    icon_data = await response.read()

            emoji = await interaction.guild.create_custom_emoji(
                name=emoji_name, image=icon_data
            )

        game_name = room.get("gameName", "Unknown Game")
        field_name = f"{emoji} {game_name} {player_info}"
        embed.add_field(name=field_name, value=field_value, inline=False)

    except (aiohttp.ClientError, discord.HTTPException, Exception) as e:
        logger.warning(f"Failed to create emoji for room: {e}")
        game_playing_text = get_localization(
            bot, "GAME_PLAYING", interaction.locale
        )
        embed.add_field(name=game_playing_text, value=field_value, inline=False)


async def _cleanup_oldest_emoji(guild: discord.Guild):
    """Delete the oldest emoji from the guild to make space."""
    if not guild.emojis:
        return
    # Find the oldest emoji by created_at
    oldest_emoji = min(guild.emojis, key=lambda e: e.created_at)
    try:
        await oldest_emoji.delete(reason="LRU Cache Cleanup for LanPlayBot")
        logger.info(f"Deleted emoji {oldest_emoji.name} for cleanup")
    except discord.HTTPException:
        logger.warning(
            f"Failed to delete emoji {oldest_emoji.name} during cleanup"
        )


class LanPlayEvents(commands.Cog):
    """LAN Play Discord bot event handlers."""

    def __init__(self, bot: commands.Bot, lan_servers: dict):
        self.bot = bot
        self.lan_servers = lan_servers
        self.lanplay_client = LanPlayClient()

    @commands.Cog.listener()
    async def on_ready(self):
        """Handle bot ready event."""
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="/help"
        )
        await self.bot.change_presence(activity=activity)
        logger.info(f"{self.bot.user.display_name} is ready!")
