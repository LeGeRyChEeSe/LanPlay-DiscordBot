"""Session management for LAN Play Discord bot."""

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from ..config.settings import SESSION_DATA_FILE


@dataclass
class Session:
    """Represents a LAN Play game session."""
    id: str
    game: str
    host: str
    host_player_name: str
    max_players: int
    current_players: List[str]
    status: str  # 'forming', 'active', 'ended'
    created_at: float
    expires_at: float  # timestamp for auto-expiry
    map_name: Optional[str] = None
    game_type: Optional[str] = None
    password: Optional[str] = None  # if needed

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        return cls(**data)


class SessionManager:
    """Manages LAN Play game sessions."""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self._load_sessions()

    def _load_sessions(self):
        """Load sessions from persistent storage."""
        if os.path.exists(SESSION_DATA_FILE):
            try:
                with open(SESSION_DATA_FILE, 'r') as f:
                    data = json.load(f)
                    for session_data in data.get('sessions', []):
                        session = Session.from_dict(session_data)
                        # Remove expired sessions
                        if session.expires_at > time.time():
                            self.sessions[session.id] = session
            except (json.JSONDecodeError, IOError) as e:
                # If file is corrupted, start fresh
                print(f"Warning: Could not load sessions: {e}")
                self.sessions = {}

    def _save_sessions(self):
        """Save sessions to persistent storage."""
        data = {
            'sessions': [session.to_dict() for session in self.sessions.values()]
        }
        try:
            with open(SESSION_DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save sessions: {e}")

    def create_session(
        self,
        game: str,
        host: str,
        host_player_name: str,
        max_players: int = 4,
        map_name: Optional[str] = None,
        game_type: Optional[str] = None,
        password: Optional[str] = None,
        expiry_hours: int = 24
    ) -> Session:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = time.time()
        session = Session(
            id=session_id,
            game=game,
            host=host,
            host_player_name=host_player_name,
            max_players=max_players,
            current_players=[host_player_name],  # host is first player
            status='forming',
            created_at=now,
            expires_at=now + (expiry_hours * 3600),
            map_name=map_name,
            game_type=game_type,
            password=password
        )
        self.sessions[session.id] = session
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def get_active_sessions(self) -> List[Session]:
        """Get all non-expired sessions."""
        now = time.time()
        return [s for s in self.sessions.values() if s.expires_at > now]

    def join_session(self, session_id: str, player_name: str) -> bool:
        """Add a player to a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        if session.status != 'forming' and session.status != 'active':
            return False
        if len(session.current_players) >= session.max_players:
            return False
        if player_name in session.current_players:
            return False  # already in session
        session.current_players.append(player_name)
        if len(session.current_players) >= session.max_players:
            session.status = 'active'
        self._save_sessions()
        return True

    def leave_session(self, session_id: str, player_name: str) -> bool:
        """Remove a player from a session."""
        session = self.get_session(session_id)
        if not session:
            return False
        if player_name not in session.current_players:
            return False
        # Prevent host from leaving without ending session? We'll allow, but if host leaves, session ends.
        session.current_players.remove(player_name)
        if not session.current_players:
            # No players left, end session
            session.status = 'ended'
        elif session.status == 'active' and len(session.current_players) < session.max_players:
            session.status = 'forming'
        # If host left, we could transfer host or end session; for simplicity, end if host left.
        if player_name == session.host_player_name:
            session.status = 'ended'
        self._save_sessions()
        return True

    def end_session(self, session_id: str) -> bool:
        """End a session (by host or admin)."""
        session = self.get_session(session_id)
        if not session:
            return False
        session.status = 'ended'
        self._save_sessions()
        return True

    def cleanup_expired(self):
        """Remove expired sessions."""
        now = time.time()
        expired = [sid for sid, session in self.sessions.items() if session.expires_at <= now]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            self._save_sessions()