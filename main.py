import functions
import os
import disnake
import locale
import datetime
import requests
import typing
import re
from disnake.ui import Button, Select
from disnake import SelectOption
from dotenv import load_dotenv
from disnake.ext import commands

load_dotenv()


locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
os.environ['TZ'] = 'Europe/Paris'
lan_servers = functions.getLanServers()
custom_servers = functions.load_lan_servers()
lan_servers["monitors"].extend(custom_servers)

intents = disnake.Intents.all()
client = commands.InteractionBot(intents=intents)
client.i18n.load("locale/")


def getTimeStamp() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


@client.listen()
async def on_dropdown(inter: disnake.MessageInteraction):
    """
        Fonction appelée lors de l'interaction avec un menu de sélection.

        Paramètres
        ----------
        inter: :class:`disnake.MessageInteraction`
            L'interaction avec le message.
    """
    if not inter.values:
        return

    custom_id = inter.component.custom_id
    lan_server = f"http://{inter.values[0]}/"

    if custom_id == f"lan_servers_{inter.author.id}":
        await inter.response.defer(with_message=False)
        embed = disnake.Embed(color=disnake.Color.blue())
        embed.title = functions.getLocalization(
            client, 'EMBED_TITLE', inter.locale)
        embed.description = functions.getLocalization(
            client, 'EMBED_DESCRIPTION', inter.locale)
        await inter.edit_original_message(embed=embed)

        embed.title = inter.values[0]
        embed.url = functions.lan_menu_url
        embed.set_thumbnail(url=functions.image_lanplay_url)
        embed.set_footer(text=f"{[s['all_time_uptime_ratio'] for s in lan_servers['monitors'] if s['friendly_name'] in lan_server][0]}{functions.getLocalization(client, 'UPTIME', inter.locale)}", icon_url=inter.guild.icon.url)

        server = await functions.getLanPlayInfos(lan_server)
        emojis = []

        if not server:
            embed.description = functions.getLocalization(
                client, 'EMBED_ERROR_DESCRIPTION', inter.locale)
        else:
            if len(server['room']) > 1:
                embed.description = f"{server['serverInfo']['online']-server['serverInfo']['idle']} :video_game: / {server['serverInfo']['idle']} :zzz:"
                embed.set_author(name=f"{len(server['room'])} {functions.getLocalization(client, 'MULTIPLE_GAME', inter.locale)}", icon_url=inter.author.display_avatar.url)
            elif len(server['room']) == 1:
                embed.description = f"{server['serverInfo']['online']-server['serverInfo']['idle']} :video_game: / {server['serverInfo']['idle']} :zzz:"
                embed.set_author(name=f"{len(server['room'])} {functions.getLocalization(client, 'ONE_GAME', inter.locale)}", icon_url=inter.author.display_avatar.url)
            else:
                embed.description = f"{server['serverInfo']['online']-server['serverInfo']['idle']} :video_game: / {server['serverInfo']['idle']} :zzz:"
                embed.set_author(name=f"{functions.getLocalization(client, 'NO_GAME', inter.locale)}", icon_url=inter.author.display_avatar.url)

            emojis: typing.List[disnake.Emoji] = []
            for room in server["room"]:
                nb_players_room = f"({room['nodeCount']}/{room['nodeCountMax']})"
                players = ',\n'.join(player['playerName']
                                     for player in room['nodes'])

                if room['nodeCount'] == room['nodeCountMax']:
                    nb_players_room += " :x:"
                else:
                    nb_players_room += " :white_check_mark:"

                if 'iconUrl' in room.keys():
                    response = requests.get(room["iconUrl"])
                    if inter.guild:
                        emojis.append(await inter.guild.create_custom_emoji(name=room["contentId"], image=response.content))
                    embed.add_field(name=f"{emojis[-1]} {room['gameName']} {nb_players_room}", value=f"{functions.getLocalization(client, 'GAME_HOST', inter.locale)} {bytearray.fromhex(room['advertiseData'][56:94].replace('00', '')).decode()} ({room['hostPlayerName']})\n**{functions.getLocalization(client, 'PLAYERS', inter.locale)}:**\n{players}", inline=False)
                else:
                    embed.add_field(name=functions.getLocalization(client, 'GAME_PLAYING', inter.locale), value=f"{functions.getLocalization(client, 'GAME_HOST', inter.locale)} {bytearray.fromhex(room['advertiseData'][56:94].replace('00', '')).decode()} ({room['hostPlayerName']})\n**{functions.getLocalization(client, 'PLAYERS', inter.locale)}:**\n{players}", inline=False)

        embed.timestamp = getTimeStamp()

        await inter.edit_original_message(embed=embed)
    else:
        embed = disnake.Embed(title=functions.getLocalization(
            client, 'NO_PERMS_TITLE', inter.locale), colour=disnake.Colour.red())
        embed.set_author(name=inter.author.display_name,
                         icon_url=inter.author.display_avatar)
        if inter.guild and custom_id:
            member = await inter.guild.get_or_fetch_member(re.search('[0-5]+', custom_id).group())
            if member:
                embed.set_footer(text=functions.getLocalization(client, 'NO_PERMS_FOOTER', inter.locale, member=await inter.guild.get_or_fetch_member(re.search('[0-9]+', custom_id).group())))
        await inter.response.send_message(embed=embed, ephemeral=True)


@client.slash_command(name="lan")
async def lan(inter: disnake.ApplicationCommandInteraction):
    """
        Afficher les parties actuelles de n'importe quel serveur LAN-Play. {{LAN_DESCRIPTION}}
    """
    embed = disnake.Embed(color=disnake.Color.blue())
    embed.set_thumbnail(url=functions.image_lanplay_url)

    embed.title = functions.getLocalization(
        client, "SERVER_SELECT", inter.locale)

    components = []

    components.append(Button(style=disnake.ButtonStyle.url, label=functions.getLocalization(
        client, "SITE_LANPLAY", inter.locale), url=functions.lan_menu_url))
    components.append(Button(style=disnake.ButtonStyle.url, label=functions.getLocalization(
        client, "CONFIG_LANPLAY", inter.locale), url=functions.lan_config_url))
    components.append(Select(placeholder=functions.getLocalization(client, "SERVER_SELECT_BUTTON", inter.locale), custom_id=f"lan_servers_{inter.author.id}", options=[SelectOption(label=server["friendly_name"], value=server["friendly_name"], description=f"{server['all_time_uptime_ratio']}{functions.getLocalization(client, 'UPTIME', inter.locale)}") for server in sorted(lan_servers["monitors"], key=lambda x: x["all_time_uptime_ratio"], reverse=True)][0:25]))

    await inter.response.send_message(embed=embed, components=components)


@client.slash_command(name="help", dm_permission=True)
async def help(inter: disnake.ApplicationCommandInteraction):
    """
        Afficher le menu d'aide pour les commandes de Lan'sBot. {{HELP_DESCRIPTION}}
    """
    embed = disnake.Embed(title=functions.getLocalization(
        client, "HELP_TITLE", inter.locale), color=disnake.Color.blue(), timestamp=getTimeStamp())
    embed.set_thumbnail(client.user.display_avatar.url)
    embed.description = ""

    for command in client.slash_commands:
        localized_command = functions.getLocalization(client, f"{command.name.upper()}_DESCRIPTION", inter.locale)
        embed.description += f"`/{command.qualified_name}`: {localized_command}\n"

    await inter.response.send_message(embed=embed, ephemeral=True)


@client.slash_command(name="add")
@commands.default_member_permissions(administrator=True)
async def add(inter: disnake.ApplicationCommandInteraction, server: str):
    """
        Ajouter un serveur custom Lan Play à la liste. {{ADD_DESCRIPTION}}

        Parameters
        ----------
        server: :class:`str`
            Le serveur custom à ajouter. Par exemple 'tekn0.net:11451' {{ADD_PARAMETER}}
    """
    pattern = r'^[a-zA-Z0-9.-]+:\d+$'

    if not re.match(pattern, server):
        await inter.response.send_message(functions.getLocalization(client, "ADD_ERROR", inter.locale), ephemeral=True)
        return

    temp_lan_custom_servers = functions.load_lan_servers()
    custom_server = functions.create_custom_server(server)

    if not functions.add_custom_server(temp_lan_custom_servers, server, lan_servers):
        await inter.response.send_message(functions.getLocalization(client, "ADD_EXISTS", inter.locale, server=server), ephemeral=True)
        return

    functions.save_lan_servers(temp_lan_custom_servers)
    lan_servers["monitors"].extend([custom_server])

    await inter.response.send_message(functions.getLocalization(client, "ADD_SUCCESS", inter.locale, server=server), ephemeral=True)


@client.slash_command(name="delete")
@commands.default_member_permissions(administrator=True)
async def delete(inter: disnake.ApplicationCommandInteraction, server: str):
    """
        Supprimer un serveur custom Lan Play de la liste. {{DELETE_DESCRIPTION}}

        Parameters
        ----------
        server: :class:`str`
            Le serveur custom à supprimer. Par exemple 'tekn0.net:11451' {{ADD_PARAMETER}}
    """
    pattern = r'^[a-zA-Z0-9.-]+:\d+$'

    if not re.match(pattern, server):
        await inter.response.send_message(functions.getLocalization(client, "DELETE_ERROR", inter.locale), ephemeral=True)
        return

    custom_servers = functions.load_lan_servers()
    custom_server = [c for c in custom_servers if server ==
                     c.get("friendly_name")][0] if custom_servers else None
    new_lan_custom_servers = functions.delete_custom_server(
        custom_servers, server) if custom_servers else None

    if new_lan_custom_servers:
        functions.save_lan_servers(new_lan_custom_servers)
        lan_servers["monitors"].remove(custom_server)

    await inter.response.send_message(functions.getLocalization(client, "DELETE_SUCCESS", inter.locale, server=server), ephemeral=True)


@delete.autocomplete("server")
async def server_autocomplete(inter: disnake.ApplicationCommandInteraction, server: str):
    custom_servers = functions.load_lan_servers()
    return [server["friendly_name"] for server in custom_servers]

# Events


@client.event
async def on_ready():
    await client.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name="/help"))
    print(f"{client.user.display_name}#{client.user.discriminator} is ready.")

client.run(os.getenv("TOKEN"))
