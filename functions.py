import requests
import disnake
import json
import os
import typing
from datetime import datetime
from decouple import config
from disnake.ext import commands
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

list_all_games_url = "https://tinfoil.media/Title/ApiJson/"
monitors_url = "https://api.uptimerobot.com/v2/getMonitors"
API_LAN_KEY = config('API_LAN_KEY')
lan_menu_url = "http://lan-play.com"
lan_config_url = "http://lan-play.com/install-switch"
image_lanplay_url = "http://lan-play.com/img/logo.f64272e3.png"


async def getLanPlayInfos(lan_server_url: str) -> typing.Optional[typing.Dict]:
    transport = AIOHTTPTransport(url=lan_server_url)
    async with Client(
        transport=transport,
    ) as session:

        query = gql("""
        query getUsers {
            room {
                contentId
                hostPlayerName
                nodeCountMax
                nodeCount
                advertiseData
                nodes {
                    playerName
                }
            }
            serverInfo {
                online
                idle
            }
        }
        """)

        try:
            result = await session.execute(query)
        except:
            return
        else:
            if hasRooms(result):
                list_games = matchGame(result["room"])
                if list_games and len(list_games) > 0:
                    for room in result["room"]:
                        for game in list_games:
                            if room["contentId"].lower() == game["id"].lower():
                                gameName = game["name"][game["name"].find(
                                    '\"\u003e') + 2: game["name"].find('\u003c/a\u003e')]
                                iconUrl = game["icon"][game["icon"].find(
                                    'url') + 4: game["icon"].find(')\"')]
                                room["gameName"] = gameName
                                room["iconUrl"] = iconUrl
            return result


async def getNumberOfRooms(lan_server_url: str) -> int:
    transport = AIOHTTPTransport(url=lan_server_url)
    async with Client(
        transport=transport,
    ) as session:

        query = gql("""
        query getUsers {
            room {
                nodeCount
            }
        }
        """)

        result = await session.execute(query)
        return len(result["room"])


def hasRooms(server: typing.Dict) -> bool:
    return isinstance(server.get("room", []), list) and bool(server["room"])


def matchGame(rooms: list) -> list:
    list_all_games = requests.get(list_all_games_url)
    if not list_all_games.ok:
        return []

    list_all_games = list_all_games.json()
    content_ids = set([room["contentId"].lower() for room in rooms])
    list_games = [game for game in list_all_games["data"]
                  if game["id"].lower() in content_ids]

    for game in list_games:
        if game["id"].lower() == "ffffffffffffffff":
            game["id"] = "0100B04011742000"

    return list_games


def getLanServers() -> typing.Dict:
    response = requests.post(monitors_url, json={
                             "api_key": API_LAN_KEY, "format": "json", "all_time_uptime_ratio": 1})
    return response.json()


def getLocalization(bot: commands.InteractionBot, key: str, locale: disnake.Locale, **kwargs) -> typing.Optional[str]:
    text_localized = bot.i18n.get(key).get(str(locale))

    for k, value in kwargs.items():
        k_formatted = "{" + k + "}"
        text_localized = text_localized.replace(k_formatted, str(value))

    return text_localized if text_localized else None


def load_lan_servers(filename: str = 'lan_servers.json') -> typing.Optional[typing.Union[typing.List[typing.Dict[str, typing.Union[str, int]]], list]]:
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return []


def save_lan_servers(lan_servers: typing.List[typing.Dict[str, typing.Union[str, int]]], filename: str = 'lan_servers.json') -> None:
    with open(filename, 'w') as file:
        json.dump(lan_servers, file, indent=4)


def create_custom_server(friendly_name: str) -> typing.Dict[str, typing.Union[str, int]]:
    return {
        "id": friendly_name.split(':')[0],  # Utiliser la partie avant les ':'
        "friendly_name": friendly_name,
        "url": f"http://{friendly_name}/info",
        "type": 1,
        "sub_type": "",
        "keyword_type": "None",
        "keyword_case_type": 0,
        "keyword_value": "",
        "http_username": "",
        "http_password": "",
        "port": "",
        "interval": 300,
        "timeout": 30,
        "status": 9,
        "create_datetime": int(datetime.now().timestamp()),  # Timestamp actuel
        "all_time_uptime_ratio": "99.999"
    }


def add_custom_server(temp_lan_servers: typing.List[typing.Dict[str, typing.Union[str, int]]], friendly_name, lan_servers=None) -> bool:
    custom_server = create_custom_server(friendly_name)

    for server in temp_lan_servers:
        if custom_server["id"] == server["id"]:
            return False

    if lan_servers:
        for server in lan_servers["monitors"]:
            if custom_server["friendly_name"] == server["friendly_name"]:
                return False

    temp_lan_servers.append(custom_server)
    return True


def delete_custom_server(lan_servers: typing.List[typing.Dict[str, typing.Union[str, int]]], friendly_name: str) -> typing.List[typing.Dict[str, typing.Union[str, int]]]:
    return [server for server in lan_servers if server.get("friendly_name") != friendly_name]
