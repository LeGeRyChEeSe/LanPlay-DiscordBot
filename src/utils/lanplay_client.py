"""LAN Play GraphQL client and game matching utilities."""

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

import requests
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from ..config.settings import LIST_ALL_GAMES_URL, MONITORS_URL, API_LAN_KEY

logger = logging.getLogger(__name__)


class LanPlayClient:
    """Client for interacting with LAN Play servers via GraphQL."""
    
    @staticmethod
    async def get_server_info(lan_server_url: str) -> Optional[Dict]:
        """
        Get server information including rooms and player data.
        
        Args:
            lan_server_url: URL of the LAN Play server
            
        Returns:
            Dictionary containing server info or None if failed
        """
        transport = AIOHTTPTransport(url=lan_server_url)
        
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
            async with Client(transport=transport) as session:
                result = await session.execute(query)
                
                if _has_rooms(result):
                    list_games = await _match_games(result["room"])
                    if list_games:
                        _enhance_rooms_with_game_info(result["room"], list_games)
                        
                return result
                
        except Exception as e:
            logger.error(f"Failed to get server info from {lan_server_url}: {e}")
            return None

    @staticmethod
    async def get_room_count(lan_server_url: str) -> int:
        """
        Get the number of active rooms on a server.
        
        Args:
            lan_server_url: URL of the LAN Play server
            
        Returns:
            Number of active rooms
        """
        transport = AIOHTTPTransport(url=lan_server_url)
        
        query = gql("""
        query getRooms {
            room {
                nodeCount
            }
        }
        """)

        try:
            async with Client(transport=transport) as session:
                result = await session.execute(query)
                return len(result.get("room", []))
        except Exception as e:
            logger.error(f"Failed to get room count from {lan_server_url}: {e}")
            return 0


def get_lan_servers() -> Dict:
    """
    Fetch LAN Play servers from UptimeRobot API.
    
    Returns:
        Dictionary containing monitor information
    """
    try:
        response = requests.post(
            MONITORS_URL, 
            json={
                "api_key": API_LAN_KEY, 
                "format": "json", 
                "all_time_uptime_ratio": 1
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch LAN servers: {e}")
        return {"monitors": []}


def _has_rooms(server: Dict) -> bool:
    """Check if server has active rooms."""
    return isinstance(server.get("room", []), list) and bool(server["room"])


async def _match_games(rooms: List[Dict]) -> List[Dict]:
    """
    Match room content IDs with game information from Tinfoil API.
    
    Args:
        rooms: List of room dictionaries
        
    Returns:
        List of matching games
    """
    try:
        response = requests.get(LIST_ALL_GAMES_URL, timeout=10)
        response.raise_for_status()
        all_games = response.json()
        
        content_ids = {room["contentId"].lower() for room in rooms}
        matching_games = [
            game for game in all_games.get("data", [])
            if game["id"].lower() in content_ids
        ]
        
        # Handle special case for homebrew
        for game in matching_games:
            if game["id"].lower() == "ffffffffffffffff":
                game["id"] = "0100B04011742000"
                
        return matching_games
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch game list: {e}")
        return []


def _enhance_rooms_with_game_info(rooms: List[Dict], games: List[Dict]) -> None:
    """
    Enhance room data with game names and icons.
    
    Args:
        rooms: List of room dictionaries to enhance
        games: List of game dictionaries with metadata
    """
    for room in rooms:
        for game in games:
            if room["contentId"].lower() == game["id"].lower():
                # Extract game name from HTML
                name_html = game.get("name", "")
                start_idx = name_html.find('">') + 2
                end_idx = name_html.find('</a>')
                
                if start_idx > 1 and end_idx > start_idx:
                    room["gameName"] = name_html[start_idx:end_idx]
                
                # Extract icon URL
                icon_html = game.get("icon", "")
                url_start = icon_html.find('url') + 4
                url_end = icon_html.find(')"')
                
                if url_start > 3 and url_end > url_start:
                    room["iconUrl"] = icon_html[url_start:url_end]
                    
                break


def create_custom_server(friendly_name: str) -> Dict[str, Union[str, int]]:
    """
    Create a custom server configuration dictionary.
    
    Args:
        friendly_name: Server address (e.g., 'example.com:11451')
        
    Returns:
        Server configuration dictionary
    """
    return {
        "id": friendly_name.split(':')[0],
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
        "create_datetime": int(datetime.now().timestamp()),
        "all_time_uptime_ratio": "99.999"
    }