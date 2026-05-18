
import logging
import asyncio
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

import aiohttp
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from ..config.settings import LIST_ALL_GAMES_URL, MONITORS_URL, API_LAN_KEY
from ..utils.constants import RETRY_MAX_ATTEMPTS, RETRY_BASE_DELAY, HTTP_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


async def fetch_with_retry(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    max_retries: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    timeout: Optional[float] = 10.0,
    **kwargs
) -> Optional[aiohttp.ClientResponse]:
    """
    Perform an HTTP request with exponential backoff retry.

    Args:
        session: aiohttp ClientSession
        method: HTTP method (GET, POST, etc.)
        url: URL to request
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 1.0)
        timeout: Request timeout in seconds (default: 10.0)
        **kwargs: Additional arguments passed to session.request

    Returns:
        Response object if successful, None if all retries failed
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            async with session.request(method, url, timeout=timeout, **kwargs) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries} retries exhausted for {method} {url}: {e}")

    return None


class TinfoilCacheManager:
    """Manages caching for Tinfoil game metadata."""
    
    _cache: Dict[str, Dict] = {}
    _last_update: Optional[datetime] = None
    _update_interval = timedelta(hours=24)
    _lock = asyncio.Lock()

    @classmethod
    async def get_games_dict(cls) -> Dict[str, Dict]:
        """
        Get games dictionary (indexed by contentId) with lazy loading/caching.
        """
        async with cls._lock:
            now = datetime.now()
            if not cls._cache or not cls._last_update or (now - cls._last_update) > cls._update_interval:
                await cls._update_cache()
            return cls._cache

    @classmethod
    async def _update_cache(cls):
        """Fetch all games from Tinfoil and index them."""
        logger.info("Updating Tinfoil game cache...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(LIST_ALL_GAMES_URL, timeout=HTTP_TIMEOUT_SECONDS) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    new_cache = {}
                    for game in data.get("data", []):
                        content_id = game["id"].lower()
                        # Handle homebrew special case
                        if content_id == "ffffffffffffffff":
                            content_id = "0100b04011742000"
                            game["id"] = "0100B04011742000"
                        
                        # Pre-parse name and icon
                        name_html = game.get("name", "")
                        start_idx = name_html.find('">') + 2
                        end_idx = name_html.find('</a>')
                        if start_idx > 1 and end_idx > start_idx:
                            game["parsed_name"] = name_html[start_idx:end_idx]
                        else:
                            game["parsed_name"] = "Unknown Game"

                        icon_html = game.get("icon", "")
                        url_start = icon_html.find('url') + 4
                        url_end = icon_html.find(')"')
                        if url_start > 3 and url_end > url_start:
                            game["parsed_icon_url"] = icon_html[url_start:url_end]
                        else:
                            game["parsed_icon_url"] = None
                            
                        new_cache[content_id] = game
                    
                    cls._cache = new_cache
                    cls._last_update = datetime.now()
                    logger.info(f"Tinfoil cache updated: {len(cls._cache)} games indexed")
        except Exception as e:
            logger.error(f"Failed to update Tinfoil cache: {e}")
            if not cls._cache:
                cls._cache = {}


class LanPlayClient:
    """Client for interacting with LAN Play servers via GraphQL."""
    
    @staticmethod
    async def get_server_info(lan_server_url: str) -> Optional[Dict]:
        """
        Get server information including rooms and player data.
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
                    games_dict = await TinfoilCacheManager.get_games_dict()
                    _enhance_rooms_with_game_info(result["room"], games_dict)
                        
                return result
                
        except Exception as e:
            logger.error(f"Failed to get server info from {lan_server_url}: {e}")
            return None

    @staticmethod
    async def get_room_count(lan_server_url: str) -> int:
        """Get the number of active rooms on a server."""
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
            logger.error(f"Failed to room count from {lan_server_url}: {e}")
            return 0


async def get_lan_servers() -> Dict:
    """
    Fetch LAN Play servers from UptimeRobot API (Async) with retry.
    """
    try:
        async with aiohttp.ClientSession() as session:
            response = await fetch_with_retry(
                session,
                "POST",
                MONITORS_URL,
                json={
                    "api_key": API_LAN_KEY,
                    "format": "json",
                    "all_time_uptime_ratio": 1
                },
                timeout=10
            )
            if response:
                return await response.json()
            return {"monitors": []}
    except Exception as e:
        logger.error(f"Failed to fetch LAN servers: {e}")
        return {"monitors": []}


def _has_rooms(server: Dict) -> bool:
    """Check if server response has valid room data structure."""
    return isinstance(server.get("room", []), list)


def _enhance_rooms_with_game_info(rooms: List[Dict], games_dict: Dict[str, Dict]) -> None:
    """
    Enhance room data with game names and icons using the indexed cache.
    """
    for room in rooms:
        content_id = room["contentId"].lower()
        game = games_dict.get(content_id)
        if game:
            room["gameName"] = game.get("parsed_name")
            room["iconUrl"] = game.get("parsed_icon_url")


def create_custom_server(friendly_name: str) -> Dict[str, Union[str, int]]:
    """Create a custom server configuration dictionary."""
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
