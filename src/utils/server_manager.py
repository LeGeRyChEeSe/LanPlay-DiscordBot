"""Custom server management utilities."""

import json
import os
import logging
import aiofiles
from typing import Dict, List, Union

from ..config.settings import CUSTOM_SERVERS_FILE
from .lanplay_client import create_custom_server

logger = logging.getLogger(__name__)

ServerDict = Dict[str, Union[str, int]]


async def load_custom_servers(filename: str = CUSTOM_SERVERS_FILE) -> List[ServerDict]:
    """
    Load custom servers from JSON file (Async).
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(filename)
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    if not os.path.exists(filename):
        return []
        
    try:
        async with aiofiles.open(filename, mode='r', encoding='utf-8') as file:
            content = await file.read()
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load custom servers from {filename}: {e}")
        return []


async def save_custom_servers(servers: List[ServerDict], filename: str = CUSTOM_SERVERS_FILE) -> bool:
    """
    Save custom servers to JSON file (Async).
    """
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.dirname(filename)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            
        async with aiofiles.open(filename, mode='w', encoding='utf-8') as file:
            content = json.dumps(servers, indent=4, ensure_ascii=False)
            await file.write(content)
        return True
    except IOError as e:
        logger.error(f"Failed to save custom servers to {filename}: {e}")
        return False


def add_custom_server(
    custom_servers: List[ServerDict], 
    friendly_name: str, 
    existing_servers: Dict = None
) -> bool:
    """
    Add a custom server to the list if it doesn't already exist.
    """
    new_server = create_custom_server(friendly_name)
    
    # Check if server already exists in custom servers
    for server in custom_servers:
        if server.get("id") == new_server["id"]:
            return False
    
    # Check if server already exists in API servers
    if existing_servers:
        for server in existing_servers.get("monitors", []):
            if server.get("friendly_name") == new_server["friendly_name"]:
                return False
    
    custom_servers.append(new_server)
    return True


def remove_custom_server(custom_servers: List[ServerDict], friendly_name: str) -> List[ServerDict]:
    """
    Remove a custom server from the list.
    """
    return [
        server for server in custom_servers 
        if server.get("friendly_name") != friendly_name
    ]


def get_custom_server_by_name(custom_servers: List[ServerDict], friendly_name: str) -> ServerDict:
    """
    Get a custom server by its friendly name.
    """
    for server in custom_servers:
        if server.get("friendly_name") == friendly_name:
            return server
    return None
