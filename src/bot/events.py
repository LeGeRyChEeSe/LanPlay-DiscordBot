"""Discord bot event handlers."""

import logging
import re
from datetime import datetime, timezone
from typing import List

import disnake
import aiohttp
from disnake.ext import commands

from ..utils.lanplay_client import LanPlayClient
from ..utils.localization import get_localization, format_uptime_text
from ..config.settings import IMAGE_LANPLAY_URL, LAN_MENU_URL

logger = logging.getLogger(__name__)


class LanPlayEvents(commands.Cog):
    """LAN Play Discord bot event handlers."""
    
    def __init__(self, bot: commands.InteractionBot, lan_servers: dict):
        self.bot = bot
        self.lan_servers = lan_servers
        self.lanplay_client = LanPlayClient()

    @commands.Cog.listener()
    async def on_ready(self):
        """Handle bot ready event."""
        activity = disnake.Activity(type=disnake.ActivityType.watching, name="/help")
        await self.bot.change_presence(activity=activity)
        logger.info(f"{self.bot.user.display_name}#{self.bot.user.discriminator} is ready.")

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        """Handle dropdown menu interactions."""
        if not inter.values:
            return

        custom_id = inter.component.custom_id
        
        # Check if this is a server selection dropdown for the current user
        if not custom_id.startswith("lan_servers_"):
            return
            
        user_id = custom_id.replace("lan_servers_", "")
        
        # Validate user permission
        if str(inter.author.id) != user_id:
            await self._send_permission_error(inter, user_id)
            return

        await self._handle_server_selection(inter)

    async def _handle_server_selection(self, inter: disnake.MessageInteraction):
        """Handle server selection from dropdown."""
        server_name = inter.values[0]
        lan_server_url = f"http://{server_name}/"
        
        # Show loading embed
        await inter.response.defer(with_message=False)
        
        loading_embed = disnake.Embed(color=disnake.Color.blue())
        loading_embed.title = get_localization(self.bot, 'EMBED_TITLE', inter.locale)
        loading_embed.description = get_localization(self.bot, 'EMBED_DESCRIPTION', inter.locale)
        await inter.edit_original_message(embed=loading_embed)

        # Create main embed
        embed = disnake.Embed(color=disnake.Color.blue())
        embed.title = server_name
        embed.url = LAN_MENU_URL
        embed.set_thumbnail(url=IMAGE_LANPLAY_URL)
        
        # Add uptime footer
        uptime_ratio = self._get_server_uptime(server_name)
        if inter.guild:
            embed.set_footer(
                text=format_uptime_text(uptime_ratio, inter.locale, self.bot),
                icon_url=inter.guild.icon.url if inter.guild.icon else None
            )

        # Fetch server data
        server_data = await self.lanplay_client.get_server_info(lan_server_url)
        
        if not server_data:
            embed.description = get_localization(self.bot, 'EMBED_ERROR_DESCRIPTION', inter.locale)
        else:
            await self._populate_server_embed(embed, server_data, inter)

        embed.timestamp = datetime.now(timezone.utc)
        await inter.edit_original_message(embed=embed)

    async def _populate_server_embed(
        self, 
        embed: disnake.Embed, 
        server_data: dict, 
        inter: disnake.MessageInteraction
    ):
        """Populate embed with server information."""
        rooms = server_data.get('room', [])
        server_info = server_data.get('serverInfo', {})
        
        online_players = server_info.get('online', 0)
        idle_players = server_info.get('idle', 0)
        active_players = online_players - idle_players
        
        embed.description = f"{active_players} :video_game: / {idle_players} :zzz:"
        
        # Set author based on room count
        room_count = len(rooms)
        if room_count > 1:
            author_text = f"{room_count} {get_localization(self.bot, 'MULTIPLE_GAME', inter.locale)}"
        elif room_count == 1:
            author_text = f"{room_count} {get_localization(self.bot, 'ONE_GAME', inter.locale)}"
        else:
            author_text = get_localization(self.bot, 'NO_GAME', inter.locale)
            
        embed.set_author(name=author_text, icon_url=inter.author.display_avatar.url)
        
        # Add room information
        created_emojis = []
        for room in rooms:
            await self._add_room_field(embed, room, inter, created_emojis)

    async def _add_room_field(
        self, 
        embed: disnake.Embed, 
        room: dict, 
        inter: disnake.MessageInteraction,
        created_emojis: List[disnake.Emoji]
    ):
        """Add a room field to the embed."""
        node_count = room.get('nodeCount', 0)
        node_max = room.get('nodeCountMax', 0)
        status_icon = ":x:" if node_count == node_max else ":white_check_mark:"
        player_info = f"({node_count}/{node_max}) {status_icon}"
        
        # Get player list
        players = [node.get('playerName', 'Unknown') for node in room.get('nodes', [])]
        players_text = ',\\n'.join(players)
        
        # Extract host information
        try:
            advertise_data = room.get('advertiseData', '')
            if len(advertise_data) > 94:
                host_data = advertise_data[56:94].replace('00', '')
                host_name = bytearray.fromhex(host_data).decode('utf-8', errors='ignore')
            else:
                host_name = "Unknown"
        except (ValueError, UnicodeDecodeError):
            host_name = "Unknown"
        
        host_player = room.get('hostPlayerName', 'Unknown')
        game_host_text = get_localization(self.bot, 'GAME_HOST', inter.locale)
        players_text_label = get_localization(self.bot, 'PLAYERS', inter.locale)
        
        # Create field value
        field_value = (
            f"{game_host_text} {host_name} ({host_player})\\n"
            f"**{players_text_label}:**\\n{players_text}"
        )
        
        # Handle game icon
        if 'iconUrl' in room and inter.guild:
            await self._add_room_with_icon(embed, room, player_info, field_value, inter, created_emojis)
        else:
            game_playing_text = get_localization(self.bot, 'GAME_PLAYING', inter.locale)
            embed.add_field(name=game_playing_text, value=field_value, inline=False)

    async def _add_room_with_icon(
        self, 
        embed: disnake.Embed, 
        room: dict, 
        player_info: str, 
        field_value: str,
        inter: disnake.MessageInteraction,
        created_emojis: List[disnake.Emoji]
    ):
        """Add room field with custom emoji icon."""
        try:
            content_id = room.get('contentId', 'unknown')
            emoji_name = content_id[:32].lower()
            
            # Check if emoji already exists in guild
            emoji = disnake.utils.get(inter.guild.emojis, name=emoji_name)
            
            if not emoji:
                # Cleanup if limit reached (Discord limit is 50 for non-boosted)
                if len(inter.guild.emojis) >= 48:
                    await self._cleanup_oldest_emoji(inter.guild)

                async with aiohttp.ClientSession() as session:
                    async with session.get(room['iconUrl'], timeout=10) as response:
                        response.raise_for_status()
                        icon_data = await response.read()
                
                emoji = await inter.guild.create_custom_emoji(
                    name=emoji_name,
                    image=icon_data
                )
            
            game_name = room.get('gameName', 'Unknown Game')
            field_name = f"{emoji} {game_name} {player_info}"
            embed.add_field(name=field_name, value=field_value, inline=False)
            
        except (aiohttp.ClientError, disnake.HTTPException, Exception) as e:
            logger.warning(f"Failed to create emoji for room: {e}")
            game_playing_text = get_localization(self.bot, 'GAME_PLAYING', inter.locale)
            embed.add_field(name=game_playing_text, value=field_value, inline=False)

    async def _cleanup_oldest_emoji(self, guild: disnake.Guild):
        """Delete one emoji from the guild to make space."""
        # Simple strategy: delete the first one that looks like a game icon (hex name)
        for emoji in guild.emojis:
            if re.match(r'^[0-9a-f]{16,32}$', emoji.name.lower()):
                try:
                    await emoji.delete(reason="LRU Cache Cleanup for LanPlayBot")
                    logger.info(f"Deleted emoji {emoji.name} for cleanup")
                    return
                except disnake.HTTPException:
                    continue

    async def _send_permission_error(self, inter: disnake.MessageInteraction, owner_id: str):
        """Send permission error message."""
        embed = disnake.Embed(
            title=get_localization(self.bot, 'NO_PERMS_TITLE', inter.locale),
            colour=disnake.Colour.red()
        )
        embed.set_author(
            name=inter.author.display_name,
            icon_url=inter.author.display_avatar.url
        )
        
        if inter.guild:
            try:
                owner = await inter.guild.get_or_fetch_member(int(owner_id))
                if owner:
                    footer_text = get_localization(
                        self.bot, 'NO_PERMS_FOOTER', inter.locale, member=owner
                    )
                    embed.set_footer(text=footer_text)
            except (ValueError, disnake.NotFound):
                pass
        
        await inter.response.send_message(embed=embed, ephemeral=True)

    def _get_server_uptime(self, server_name: str) -> str:
        """Get uptime ratio for a server."""
        for server in self.lan_servers.get("monitors", []):
            if server.get("friendly_name") == server_name:
                return server.get("all_time_uptime_ratio", "0")
        return "0"