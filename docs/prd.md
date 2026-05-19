# LanPlay-DiscordBot Product Requirements Document
# LanPlay-DiscordBot Product Requirements Document

## 1. Introduction
**Project Name:** LanPlay-DiscordBot
**Project Type:** Discord Bot (Python/asyncio)
**Core Functionality:** A Discord bot that monitors LAN Play servers and provides real-time information about Nintendo Switch games, players, and servers across multiple LAN Play instances, with features for managing custom servers and user-created LAN sessions.
**Target Users:** Gaming communities and friends who want to monitor LAN Play activity and organize gaming sessions via Discord.

---

## 2. Vision & Goals

### Vision Statement
Enable gaming communities to easily monitor LAN Play activity and organize gaming sessions through intuitive Discord commands, with real-time server information, session tracking, and robust infrastructure.

### Goals
1. Provide real-time information about LAN Play servers, games, and players
2. Enable users to create and manage their own LAN play sessions via Discord
3. Maintain session state with persistence across bot restarts
4. Ensure bot reliability with health check monitoring
5. Protect against abuse with rate limiting
6. Support multiple concurrent sessions with conflict resolution
7. Allow management of custom LAN Play servers

### Out of Scope (v1.0)
- Authentication/authorization (public bot)
- Session scheduling/recurring events
- Voice channel integration
- Cross-server session sharing

---

## 3. User Interactions & Flows

### Core User Flows

#### Create Session Flow
1. User invokes `/lan create <game_name> [max_players]`
2. Bot validates inputs (game name required, max_players optional, default=8)
3. Bot creates session in session manager
4. Bot posts session message with join/leave buttons
5. Bot responds with confirmation embed

#### List Sessions Flow
1. User invokes `/lan list`
2. Bot retrieves all active sessions
3. Bot displays formatted list of available sessions

#### Join Session Flow
1. User clicks "Join" button on session message
2. Bot validates user not already in another session
3. Bot adds user to session player list
4. Bot updates session message with new player count

#### Leave Session Flow
1. User clicks "Leave" button on session message
2. Bot removes user from session player list
3. Bot updates session message with new player count

#### Delete Session Flow
1. User invokes `/lan delete <session_id>`
2. Bot validates user is session creator
3. Bot removes session from active sessions
4. Bot updates session message to show closed

### Edge Cases
- **Full session:** Bot rejects join attempts when max_players reached
- **Self-removal:** User leaves, updates player list
- **Creator leaves:** Session remains, creator slot becomes vacant
- **Empty session:** Auto-close sessions with 0 players after 5 minutes
- **Duplicate join:** Bot ignores if user already in session

---

## 4. Data Model

### Session Entity
```
Session {
  id: string (UUID)
  game_name: string
  creator_id: string (Discord user ID)
  creator_name: string
  max_players: integer (default: 8)
  players: list[Player] (ordered)
  status: enum [open, full, closed]
  created_at: timestamp
  message_id: string (Discord message ID for update tracking)
  guild_id: string
  channel_id: string
}
```

### Player Entity
```
Player {
  id: string (Discord user ID)
  name: string (Discord username)
  joined_at: timestamp
}
```

### Custom Server Entity
```
CustomServer {
  name: string
  address: string
  region: string
  added_by: string (Discord user ID)
  added_at: timestamp
}
```

---

## 5. Commands & Features

### Slash Commands

| Command | Arguments | Description | Rate Limit |
|---------|-----------|-------------|------------|
| `/lan create` | `game_name` (required), `max_players` (optional, default=8) | Create a new LAN session | 5/min |
| `/lan list` | none | List all active sessions | 10/min |
| `/lan delete` | `session_id` (required) | Delete a session you created | 10/min |
| `/add` | `name`, `address`, `region` | Add custom server to list | 3/min |
| `/delete` | `server_name` (autocomplete) | Remove custom server | 5/min |
| `/help` | none | Show command help | 30/min |

### Button Interactions
- **Join Session:** Adds user to session
- **Leave Session:** Removes user from session
- **Refresh:** Updates session message (admin)

### Autocomplete
- `/delete` server_name: Lists user's deletable servers

---

## 6. Technical Architecture

### Technology Stack
- **Language:** Python 3.11+
- **Discord Library:** disnake (async fork of discord.py)
- **HTTP Client:** aiohttp (async)
- **Persistence:** JSON file storage (sessions.json, custom_servers.json)
- **Rate Limiting:** In-memory token bucket (src/utils/rate_limiter.py)

### Module Structure
```
```
src/
├── bot/
│   ├── bot.py              # Main bot class, cogs setup
│   ├── commands.py         # LanPlayCommands cog (slash commands)
│   ├── events.py           # LanPlayEvents cog (button handlers)
│   ├── session_manager.py  # Session state management
│   └── health.py           # Health check HTTP server
├── config/
│   └── settings.py         # Environment-based configuration
├── utils/
│   ├── rate_limiter.py     # Token bucket rate limiting
│   └── http_client.py      # aiohttp wrapper for API calls
└── api/
    └── lanplay_api.py      # LAN Play API client
```
```

### Session Persistence
- Sessions stored in `data/sessions.json`
- Custom servers stored in `data/custom_servers.json`
- Load on startup, save on every modification
- Backup before write operations

### Health Check Endpoint
- **Endpoint:** `GET /health`
- **Port:** Configurable via `HEALTH_PORT` env var (default: 8080)
- **Response:** `{ "status": "healthy", "sessions": <count>, "uptime": <seconds> }`
- **Implementation:** `src/bot/health.py` (started in `src/bot/bot.py` on_ready)

---

## 7. Configuration

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | required | Discord bot token |
| `LANPLAY_API_URL` | https://api.lanplay.com | LAN Play API base URL |
| `DATA_DIR` | ./data | Directory for JSON storage |
| `HEALTH_PORT` | 8080 | Health check server port |
| `LOG_LEVEL` | INFO | Logging verbosity |
| `MAX_PLAYERS_DEFAULT` | 8 | Default max players per session |
| `SESSION_TIMEOUT_MINUTES` | 30 | Auto-close inactive sessions |
| `RATE_LIMIT_WINDOW_SEC` | 60 | Rate limit window size |

### Rate Limits
| Command | Limit | Window |
|---------|-------|--------|
| `/lan create` | 5 | 60 seconds |
| `/lan list` | 10 | 60 seconds |
| `/lan delete` | 10 | 60 seconds |
| `/add` | 3 | 60 seconds |
| `/delete` | 5 | 60 seconds |
| `/help` | 30 | 60 seconds |

---

## 8. Error Handling

### User-Facing Errors
- **Invalid input:** Clear message with correct usage format
- **Rate limited:** "Please wait X seconds before trying again"
- **Session full:** "Session is full (X/Y players)"
- **Not in session:** "You are not in any session"
- **Not creator:** "Only the session creator can delete this session"

### Internal Errors
- **API failure:** Log error, notify user, retry with backoff
- **Persistence failure:** Log error, maintain in-memory state, alert admin
- **Discord API failure:** Log error, attempt message repair

---

## 9. Acceptance Criteria

### Must Have (v1.0)
- [ ] Bot connects to Discord with slash commands registered
- [ ] `/lan create` creates session with join button
- [ ] `/lan list` shows all active sessions
- [ ] Join button adds user to session
- [ ] Leave button removes user from session
- [ ] `/lan delete` removes session (creator only)
- [ ] Sessions persist across bot restarts
- [ ] Health check endpoint returns status
- [ ] Rate limiting prevents command spam
- [ ] Custom servers can be added/listed/deleted

### Should Have
- [ ] Session auto-closes when empty for 5 minutes
- [ ] Session message updates on player change
- [ ] Autocomplete for server names in `/delete`

### Could Have (Future)
- [ ] Session edit (change game, max players)
- [ ] Session transfer (change creator)
- [ ] Direct join via session ID

---

## 10. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-19 | Claude | Initial PRD for LanPlay-DiscordBot |

---

*Document Status: Draft*
*Methodology: BMAD v6.7.1*