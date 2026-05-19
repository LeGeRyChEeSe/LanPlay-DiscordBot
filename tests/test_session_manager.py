"""Tests for the session manager."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.utils.session_manager import Session, SessionManager


def test_init_loads_empty_sessions():
    """Test that initializing a SessionManager loads an empty session list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            assert manager.sessions == {}
    finally:
        os.unlink(temp_file)


def test_init_loads_sessions_from_file():
    """Test that initializing a SessionManager loads sessions from a file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        # Write a session that will not be expired (far in the future)
        session_data = {
            "sessions": [{
                "id": "test-id",
                "game": "Test Game",
                "host": "127.0.0.1",
                "host_player_name": "TestHost",
                "max_players": 4,
                "current_players": ["TestHost", "Player2"],
                "status": "active",
                "created_at": 1000.0,
                "expires_at": 2000.0,  # Far in the future
                "map_name": "Test Map",
                "game_type": "Test Type",
                "password": "testpass"
            }]
        }
        json.dump(session_data, f)
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            with patch('time.time', return_value=1500.0):  # Mock time to be between created_at and expires_at
                manager = SessionManager()
                assert len(manager.sessions) == 1
                session = manager.sessions["test-id"]
                assert session.game == "Test Game"
                assert session.host == "127.0.0.1"
                assert session.host_player_name == "TestHost"
                assert session.max_players == 4
                assert session.current_players == ["TestHost", "Player2"]
                assert session.status == "active"
                assert session.created_at == 1000.0
                assert session.expires_at == 2000.0
                assert session.map_name == "Test Map"
                assert session.game_type == "Test Type"
                assert session.password == "testpass"
    finally:
        os.unlink(temp_file)

def test_init_handles_corrupted_file():
    """Test that a corrupted session file results in an empty session list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json")
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            assert manager.sessions == {}
    finally:
        os.unlink(temp_file)


def test_init_handles_missing_file():
    """Test that a missing session file results in an empty session list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    # Delete the file so it's missing
    os.unlink(temp_file)

    with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
        manager = SessionManager()
        assert manager.sessions == {}


def test_create_session():
    """Test creating a new session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="TestHost",
                    max_players=4,
                    map_name="Test Map",
                    game_type="Test Type",
                    password="testpass",
                    expiry_hours=1
                )
            assert session.id in manager.sessions
            assert session.game == "Test Game"
            assert session.host == "127.0.0.1"
            assert session.host_player_name == "TestHost"
            assert session.max_players == 4
            assert session.current_players == ["TestHost"]
            assert session.status == "forming"
            assert session.created_at == 1000.0
            assert session.expires_at == 1000.0 + 3600  # 1 hour expiry
            assert session.map_name == "Test Map"
            assert session.game_type == "Test Type"
            assert session.password == "testpass"
    finally:
        os.unlink(temp_file)


def test_get_session():
    """Test getting a session by ID."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="TestHost",
                    max_players=4
                )
            retrieved = manager.get_session(session.id)
            assert retrieved is not None
            assert retrieved.id == session.id
            # Test getting a non-existent session
            assert manager.get_session("non-existent-id") is None
    finally:
        os.unlink(temp_file)


def test_get_active_sessions():
    """Test getting all non-expired sessions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            with patch('time.time', return_value=1000.0):
                manager = SessionManager()
                # Create an active session (expires in the future)
                active_session = manager.create_session(
                    game="Active Game",
                    host="127.0.0.1",
                    host_player_name="Host1",
                    max_players=4
                )
                # Create an expired session (expires in the past)
                expired_session = manager.create_session(
                    game="Expired Game",
                    host="127.0.0.1",
                    host_player_name="Host2",
                    max_players=4,
                    expiry_hours=-1  # Already expired
                )
                # Adjust the expired session's expires_at to be in the past
                expired_session.expires_at = 990.0  # now is 1000.0, so 10 seconds in the past
                manager._save_sessions()

                # Get active sessions
                active = manager.get_active_sessions()
                assert len(active) == 1
                assert active[0].id == active_session.id
    finally:
        os.unlink(temp_file)
def test_join_session_success():
    """Test successfully joining a session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Join the session
            result = manager.join_session(session.id, "Player2")
            assert result is True
            # Check that the player was added
            assert "Player2" in manager.sessions[session.id].current_players
            # Check that the session status is still forming (not full yet)
            assert manager.sessions[session.id].status == "forming"
    finally:
        os.unlink(temp_file)


def test_join_session_full():
    """Test joining a session that is already full."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=2  # Only 2 players max
                )
            # Fill the session
            manager.join_session(session.id, "Player1")
            # Now the session has Host and Player1 (2/2)
            # Try to add a third player
            result = manager.join_session(session.id, "Player2")
            assert result is False
            # Check that the player was not added
            assert len(manager.sessions[session.id].current_players) == 2
    finally:
        os.unlink(temp_file)


def test_join_session_wrong_status():
    """Test joining a session that is not joinable (ended)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # End the session
            manager.end_session(session.id)
            # Try to join
            result = manager.join_session(session.id, "Player2")
            assert result is False
    finally:
        os.unlink(temp_file)


def test_join_session_already_in():
    """Test joining a session when the player is already in it."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Try to join again as the host
            result = manager.join_session(session.id, "Host")
            assert result is False  # Already in session
    finally:
        os.unlink(temp_file)


def test_leave_session_success():
    """Test successfully leaving a session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Add a player
            manager.join_session(session.id, "Player2")
            # Leave the session as Player2
            result = manager.leave_session(session.id, "Player2")
            assert result is True
            # Check that the player was removed
            assert "Player2" not in manager.sessions[session.id].current_players
            # Check that the host is still there
            assert "Host" in manager.sessions[session.id].current_players
            # Check that the session is still forming (not empty)
            assert manager.sessions[session.id].status == "forming"
    finally:
        os.unlink(temp_file)


def test_leave_session_last_player():
    """Test leaving a session when the last player leaves."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Leave the session as the host (only player)
            result = manager.leave_session(session.id, "Host")
            assert result is True
            # Check that the session has no players
            assert len(manager.sessions[session.id].current_players) == 0
            # Check that the session is ended
            assert manager.sessions[session.id].status == "ended"
    finally:
        os.unlink(temp_file)


def test_leave_session_host_leaves_others_present():
    """Test that when the host leaves, the session ends (regardless of other players)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Add another player
            manager.join_session(session.id, "Player2")
            # Host leaves
            result = manager.leave_session(session.id, "Host")
            assert result is True
            # Check that the session is ended (even though Player2 is still there)
            assert manager.sessions[session.id].status == "ended"
    finally:
        os.unlink(temp_file)


def test_leave_session_not_in_session():
    """Test leaving a session when the player is not in it."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # Try to leave as a player not in the session
            result = manager.leave_session(session.id, "Player2")
            assert result is False
    finally:
        os.unlink(temp_file)


def test_leave_session_non_existent():
    """Test leaving a non-existent session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            result = manager.leave_session("non-existent-id", "Player")
            assert result is False
    finally:
        os.unlink(temp_file)


def test_end_session():
    """Test ending a session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            with patch('time.time', return_value=1000.0):
                session = manager.create_session(
                    game="Test Game",
                    host="127.0.0.1",
                    host_player_name="Host",
                    max_players=4
                )
            # End the session
            result = manager.end_session(session.id)
            assert result is True
            # Check that the session status is ended
            assert manager.sessions[session.id].status == "ended"
    finally:
        os.unlink(temp_file)


def test_end_session_non_existent():
    """Test ending a non-existent session."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            manager = SessionManager()
            result = manager.end_session("non-existent-id")
            assert result is False
    finally:
        os.unlink(temp_file)


def test_cleanup_expired():
    """Test cleaning up expired sessions."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"sessions": []}')
        temp_file = f.name

    try:
        with patch('src.utils.session_manager.SESSION_DATA_FILE', temp_file):
            with patch('time.time', return_value=1000.0):
                manager = SessionManager()
                # Create an active session (expires in the future)
                active_session = manager.create_session(
                    game="Active Game",
                    host="127.0.0.1",
                    host_player_name="Host1",
                    max_players=4
                )
                # Create an expired session (expires in the past)
                expired_session = manager.create_session(
                    game="Expired Game",
                    host="127.0.0.1",
                    host_player_name="Host2",
                    max_players=4
                )
                # Adjust the expired session's expires_at to be in the past
                expired_session.expires_at = 990.0  # now is 1000.0, so 10 seconds in the past
                manager._save_sessions()

                # Run cleanup
                manager.cleanup_expired()

                # Check that the active session remains
                assert active_session.id in manager.sessions
                # Check that the expired session is removed
                assert expired_session.id not in manager.sessions
    finally:
        os.unlink(temp_file)