import os
import json
import pytest
import asyncio
from src.utils.server_manager import load_custom_servers, save_custom_servers, add_custom_server

@pytest.fixture
def temp_server_file(tmp_path):
    return str(tmp_path / "test_servers.json")

@pytest.mark.asyncio
async def test_save_and_load_servers(temp_server_file):
    test_servers = [
        {
            "id": "test.com",
            "friendly_name": "test.com:11451",
            "url": "http://test.com:11451/info"
        }
    ]
    
    # Test saving
    success = await save_custom_servers(test_servers, filename=temp_server_file)
    assert success is True
    assert os.path.exists(temp_server_file)
    
    # Test loading
    loaded_servers = await load_custom_servers(filename=temp_server_file)
    assert len(loaded_servers) == 1
    assert loaded_servers[0]["id"] == "test.com"

@pytest.mark.asyncio
async def test_load_non_existent_file(temp_server_file):
    # Ensure file doesn't exist
    if os.path.exists(temp_server_file):
        os.remove(temp_server_file)
        
    loaded_servers = await load_custom_servers(filename=temp_server_file)
    assert loaded_servers == []

def test_add_custom_server_logic():
    custom_servers = []
    friendly_name = "new-server.org:11451"
    
    # Add new
    added = add_custom_server(custom_servers, friendly_name)
    assert added is True
    assert len(custom_servers) == 1
    assert custom_servers[0]["id"] == "new-server.org"
    
    # Add duplicate
    added_duplicate = add_custom_server(custom_servers, friendly_name)
    assert added_duplicate is False
    assert len(custom_servers) == 1
