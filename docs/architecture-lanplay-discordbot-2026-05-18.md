# System Architecture: LanPlay-DiscordBot

**Date:** 2026-05-18
**Architect:** Gemini Bot
**Version:** 1.0
**Project Type:** other
**Project Level:** 2
**Status:** Draft

---

## Document Overview

This document defines the system architecture for LanPlay-DiscordBot. It provides the technical blueprint for implementation, addressing all functional and non-functional requirements from the PRD.

**Related Documents:**
- Product Requirements Document: docs/prd-lanplay-discordbot-2026-05-18.md
- Product Brief: Not applicable (created from scratch)

---

## Executive Summary

LanPlay-DiscordBot is a Discord bot that enables seamless LAN game discovery, session management, and launching. The system uses a Modular Monolith architecture with clear separation between Discord interaction layer, business logic layer, and external service integration layer.

**Key Architectural Decisions:**
- **Pattern:** Modular Monolith with Layered Architecture - appropriate for Level 2 project scale
- **Language:** Python 3.9+ with async/await for concurrent operations
- **Discord Framework:** Disnake (async Discord library)
- **Storage:** JSON file-based persistence for custom servers; in-memory caching for game metadata
- **External Integrations:** GraphQL client for LAN Play server communication; REST API for UptimeRobot monitoring

**Architectural Drivers:**
1. NFR-001 (Performance) - Command response <2s, network scan <10s
2. NFR-004 (Security) - No plaintext secrets, rate limiting, permission enforcement
3. NFR-002 (Reliability) - Auto-recovery, retry mechanisms, >99% uptime

---

## Architectural Drivers

These requirements heavily influence architectural decisions:

| NFR ID | Requirement | Driver Type | Architectural Impact |
|--------|-------------|-------------|----------------------|
| NFR-001 | Performance (<2s response, <10s scan) | **Performance** | Async operations, caching, connection pooling |
| NFR-002 | Reliability (>99% uptime, auto-recovery) | **Availability** | Graceful error handling, retry with backoff, health checks |
| NFR-004 | Security (no plaintext secrets, rate limiting) | **Security** | Environment-based secrets, input validation, permission checks |
| NFR-003 | Scalability (100 users, 1000 servers) | **Scalability** | Efficient data structures, caching strategy |
| NFR-005 | Maintainability (80% test coverage, separation of concerns) | **Maintainability** | Clean module boundaries, comprehensive testing |
| NFR-006 | Compatibility (Python 3.9+, cross-platform) | **Compatibility** | Standard library usage, async I/O patterns |

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Discord Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Commands  │  │   Events    │  │   Interaction Handlers  │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │                │                      │
          └────────────────┼──────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                    Business Logic Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Game       │  │  Session    │  │   Configuration         │  │
│  │  Discovery  │  │  Manager    │  │   Manager               │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │                │                      │
          └────────────────┼──────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                   Integration Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  LAN Play   │  │  Uptime     │  │   File-based            │  │
│  │  GraphQL    │  │  Robot API  │  │   Persistence           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Discord API   │
                                    └────────┬────────┘
                                             │
┌────────────────────────────────────────────┼────────────────────────────────────┐
│                                            │         LanPlay Discord Bot        │
│  ┌─────────────────────────────────────────┼─────────────────────────────────┐  │
│  │                                         │                                 │  │
│  │  ┌──────────────────────────────────────▼──────────────────────────────┐  │
│  │  │                         Bot Core                                  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │  │  Commands   │  │   Events    │  │  Localization│  │  Version  │ │  │
│  │  │  │  (Cog)      │  │  (Cog)      │  │  Manager    │  │  Manager   │ │  │
│  │  │  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └───────────┘ │  │
│  │  └─────────┼────────────────┼──────────────────────────────────────┘  │
│  │            │                │                                          │  │
│  │  ┌─────────▼────────────────▼──────────────────────────────────────┐  │
│  │  │                    Utilities Layer                               │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │  │
│  │  │  │ LanPlay     │  │  Server     │  │  Changelog   │  │  Game   │ │  │
│  │  │  │ Client      │  │  Manager    │  │  Manager     │  │  Cache  │ │  │
│  │  │  │ (GraphQL)   │  │  (JSON)     │  │             │  │ Manager │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  │                     Configuration Layer                        │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │  │
│  │  │  │  Settings   │  │  Environment│  │   Locale Files          │ │  │
│  │  │  │  (config)   │  │  (.env)      │  │   (i18n)                │ │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                             │
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
                    │ Uptime  │         │  Tinfoil│         │ Custom  │
                    │ Robot   │         │  Media  │         │ Servers │
                    │ API     │         │ (Games) │         │ (JSON)  │
                    └─────────┘         └─────────┘         └─────────┘
```

### Architectural Pattern

**Pattern:** Modular Monolith with Layered Architecture

**Rationale:**
- **Level 2 project (8 FRs, 6 NFRs):** Microservices would be over-engineered; a well-structured monolith is optimal
- **Clear separation:** Layered architecture provides logical separation without distributed system complexity
- **Single deployment unit:** Simplifies deployment and operations for a single Discord bot
- **Team size fit:** Small team can manage monolithic structure effectively
- **Future evolution:** Can extract components (e.g., game launching service) if scope grows
- **Async I/O:** Python async/await enables high concurrency within the monolith

---

## Technology Stack

### Backend

**Choice:** Python 3.9+ with Disnake

**Rationale:**
- Existing codebase uses Python with disnake library for Discord interactions
- Async/await natively supported for concurrent operations (network I/O, file I/O)
- Disnake provides modern, async-first Discord API wrapper
- Strong ecosystem for Discord bots with established patterns

**Trade-offs:**
- ✓ Gain: Native async support for high-concurrency Discord interactions
- ✓ Gain: Well-documented Discord library with slash command support
- ✗ Lose: Some performance benefits of Go/Rust for CPU-bound tasks
- ✗ Lose: Strict typing benefits of TypeScript

### Database

**Choice:** JSON file-based storage with in-memory caching

**Rationale:**
- Existing implementation uses JSON files for custom server storage
- Data volume is low (<1000 servers, <100 sessions expected)
- Simplicity: No database server to maintain or connect to
- In-memory caching (TinfoilCacheManager) provides fast access to hot data

**Trade-offs:**
- ✓ Gain: Zero infrastructure complexity
- ✓ Gain: Easy backup and sync (file-based)
- ✓ Gain: Fast for small datasets
- ✗ Lose: Not suitable for high-write scenarios
- ✗ Lose: No built-in query capabilities
- ✗ Lose: Single point of failure (mitigated by backup strategy)

**Future Migration Path:** If data grows, migrate to SQLite (file-based, no server) then PostgreSQL

### Third-Party Services

**Choice:** UptimeRobot API (monitoring), Tinfoil Media (game metadata)

**Rationale:**
- UptimeRobot: Existing integration for monitoring LAN Play servers
- Tinfoil Media: Provides game names and icons for discovered rooms
- Both are free tier APIs with simple REST/JSON interfaces

**Trade-offs:**
- ✓ Gain: Existing integrations, no new vendor relationships
- ✓ Gain: Free tier sufficient for current scale
- ✗ Lose: External dependency for game metadata
- ✗ Lose: Rate limiting on external APIs

---

## System Components

### Component: Bot Core

**Purpose:** Main entry point and orchestration for the Discord bot

**Responsibilities:**
- Initialize Discord client with appropriate intents
- Set up locale and timezone environment
- Register all cogs (commands, events)
- Manage bot lifecycle (start, stop, restart)
- Handle Discord connection events

**Interfaces:**
- Discord gateway (WebSocket) for all Discord events
- Internal event bus for cross-component communication

**Dependencies:**
- Disnake library
- Configuration settings

**FRs Addressed:** FR-005 (User Interface & Commands - main bot infrastructure)

---

### Component: Commands (Cog)

**Purpose:** Handle all Discord slash commands and user interactions

**Responsibilities:**
- `/lan` - Display available LAN Play servers with game selection
- `/help` - Show command list and descriptions
- `/version` - Display bot version and build info
- `/changelog` - Show recent changes
- `/add` - Add custom server (admin only)
- `/delete` - Remove custom server (admin only)
- Autocomplete for server names
- Permission checking for admin commands

**Interfaces:**
- Discord interaction API (slash commands, buttons, selects)
- Localization system for localized messages

**Dependencies:**
- Bot Core
- LanPlayClient (for server data)
- ServerManager (for custom servers)
- Localization system

**FRs Addressed:** FR-001 (LAN Game Discovery - display), FR-002 (Session Management - display), FR-005 (UI & Commands), FR-006 (Emoji Management - if dynamic emojis used)

---

### Component: Events (Cog)

**Purpose:** Handle Discord events (ready, error, etc.)

**Responsibilities:**
- On-ready: Load initial server data, log startup
- On-error: Log errors with context, graceful degradation
- On-connect: Re-establish server connections
- Health check endpoint (for container orchestration)

**Interfaces:**
- Discord gateway events
- Internal error handling and logging

**Dependencies:**
- Bot Core
- Server loading logic

**FRs Addressed:** FR-008 (Logging & Monitoring)

---

### Component: LanPlayClient

**Purpose:** Interface to LAN Play GraphQL servers and external APIs

**Responsibilities:**
- Fetch server list from UptimeRobot API
- Query LAN Play servers via GraphQL for room/player data
- Cache Tinfoil game metadata (24-hour TTL)
- Handle network errors with retry logic
- Parse and enhance room data with game names

**Interfaces:**
- UptimeRobot REST API (HTTP POST)
- LAN Play GraphQL endpoint (HTTP)
- Tinfoil Media API (HTTP GET)

**Dependencies:**
- External APIs (UptimeRobot, Tinfoil)
- aiohttp for async HTTP
- gql for GraphQL

**FRs Addressed:** FR-001 (LAN Game Discovery - scanning), FR-002 (Game info display), FR-004 (Real-time updates - data fetching)

---

### Component: ServerManager

**Purpose:** Manage custom server persistence and operations

**Responsibilities:**
- Load custom servers from JSON file
- Save custom servers to JSON file
- Add/remove custom servers with validation
- Validate server format (hostname:port)
- Merge custom servers with API servers

**Interfaces:**
- File system (data/lan_servers.json)
- In-memory server list

**Dependencies:**
- aiofiles for async file I/O
- JSON serialization

**FRs Addressed:** FR-001 (Custom server support), FR-002 (Session management - server selection)

---

### Component: Localization System

**Purpose:** Provide internationalized strings for all bot messages

**Responsibilities:**
- Load locale files from src/config/locale/
- Provide localized strings by key
- Support multiple locales
- Fall back to default locale if key missing

**Interfaces:**
- Locale YAML files
- Discord locale parameter

**Dependencies:**
- Disnake i18n system
- Locale files

**FRs Addressed:** FR-005 (UI & Commands - localized messages)

---

### Component: Configuration

**Purpose:** Centralized configuration management with environment-based secrets

**Responsibilities:**
- Load settings from environment variables
- Provide typed settings to all components
- Store sensitive data (TOKEN, API keys) securely via .env
- Define URLs and constants

**Interfaces:**
- Environment variables (.env file)
- Python constants

**Dependencies:**
- python-dotenv
- decouple

**FRs Addressed:** FR-007 (Configuration Management), NFR-004 (Security - secrets management)

---

## Data Architecture

### Data Model

**Entities:**

1. **Server**
   - `id`: Unique identifier (friendly_name)
   - `friendly_name`: Display name (hostname:port)
   - `url`: Server GraphQL endpoint
   - `type`: Server type (1 = custom)
   - `sub_type`: Additional classification
   - `status`: UptimeRobot status code
   - `all_time_uptime_ratio`: Historical uptime percentage
   - `create_datetime`: When added

2. **GameRoom**
   - `contentId`: Game identifier (from Tinfoil)
   - `hostPlayerName`: Name of room host
   - `nodeCount`: Current player count
   - `nodeCountMax`: Maximum players
   - `advertiseData`: Game-specific data
   - `gameName`: Parsed from Tinfoil (optional)
   - `iconUrl`: Game icon URL (optional)

3. **ServerList**
   - `monitors`: List of Server entities
   - Loaded from UptimeRobot API + custom servers

4. **TinfoilGame** (Cached)
   - `id`: Content ID
   - `name`: Game name (HTML parsed)
   - `parsed_name`: Clean game name
   - `icon`: Icon URL (parsed)
   - `parsed_icon_url`: Clean icon URL

### Database Design

**Storage Strategy:** JSON files + In-memory caching

**Files:**
- `data/lan_servers.json`: Custom server list
  ```json
  [
    {
      "id": "example.com:11451",
      "friendly_name": "example.com:11451",
      "url": "http://example.com:11451/info",
      "type": 1,
      ...
    }
  ]
  ```

**In-Memory Cache (TinfoilCacheManager):**
- TTL: 24 hours
- Index: Dictionary keyed by contentId (lowercase)
- Size: ~1000-5000 games (typical Tinfoil cache)

**Schema Migration Strategy:**
- Version the JSON schema
- On startup, validate and migrate if needed
- Keep backups of old versions

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Discord User                             │
└────────────────────────────┬────────────────────────────────────┘
                             │ /lan command
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Commands (Cog)                              │
│  1. Validate command parameters                                  │
│  2. Call LanPlayClient with server list                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LanPlayClient                                │
│  1. For each server, execute GraphQL query                      │
│  2. Fetch Tinfoil game cache (if stale, refresh)                 │
│  3. Enhance room data with game names                           │
│  4. Aggregate results                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Commands (Cog)                              │
│  1. Format embed with game list                                  │
│  2. Create select menu with options                             │
│  3. Send response to Discord                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Discord User                               │
│  Views available games and selects one                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Design

### API Architecture

**Note:** This is a Discord bot, not a REST API server. The "API" here refers to the Discord command interface and any external API integrations.

**Discord Command Interface:**
- All interaction through Discord slash commands
- Autocomplete for server names
- Button/select interactions for game selection

**External API Integrations:**

| Service | Protocol | Purpose |
|---------|----------|---------|
| UptimeRobot | REST (POST) | Fetch monitored LAN Play servers |
| LAN Play Servers | GraphQL | Query room/player data per server |
| Tinfoil Media | REST (GET) | Fetch game metadata for enrichment |

**Authentication & Authorization:**
- Discord itself handles user authentication
- Bot uses bot token for API access
- Admin-only commands checked via `@commands.default_member_permissions(administrator=True)`
- Environment variables for secrets (TOKEN, API_LAN_KEY)

### Key Endpoints (External APIs)

```
UptimeRobot API:
POST https://api.uptimerobot.com/v2/getMonitors
  Body: {"api_key": "...", "format": "json", "all_time_uptime_ratio": 1}
  Response: {"monitors": [...]}

LAN Play GraphQL:
POST {server_url}/info
  Query: getUsers { room { ... }, serverInfo { ... } }

Tinfoil Media:
GET https://tinfoil.media/Title/ApiJson/
  Response: {"data": [...]}
```

---

## Non-Functional Requirements Coverage

### NFR-001: Performance

**Requirement:** Command response time < 2 seconds for 95% of requests

**Architecture Solution:**
- Async I/O throughout (aiohttp, aiofiles)
- Connection pooling for HTTP/GraphQL clients
- TinfoilCacheManager with 24-hour cache to avoid repeated API calls
- Lazy loading: only fetch data when needed
- Limit autocomplete results to reasonable size

**Implementation Notes:**
- Use asyncio.gather for parallel server queries when displaying all
- Set reasonable timeouts (10s for API calls, 30s for Tinfoil)
- Implement circuit breaker pattern if external API becomes unreliable

**Validation:**
- Monitor command response times via logging timestamps
- Load test with simulated Discord interactions
- Target: <500ms for cached data, <2s for full refresh

---

### NFR-002: Reliability

**Requirement:** Bot automatically recovers from network interruptions; >99% uptime

**Architecture Solution:**
- Async error handling with try/except around all network calls
- Retry mechanisms with exponential backoff for transient failures
- Graceful degradation: if one server fails, continue with others
- Health check endpoint for container orchestration
- Bot logs on ready to confirm successful startup
- JSON file writes use atomic rename pattern (write to temp, then rename)

**Implementation Notes:**
- LanPlayClient catches all exceptions and returns None on failure
- ServerManager validates data on load, returns empty list on corruption
- Implement reconnect logic in on-ready event

**Validation:**
- Track error rates in logs
- Ensure no unhandled exceptions crash the bot
- Test by simulating network failures

---

### NFR-003: Scalability

**Requirement:** Supports 100 concurrent users, 1000 discovered servers

**Architecture Solution:**
- In-memory data structures (dict) for O(1) lookups
- Server list sorted by uptime ratio for efficient display
- Pagination for large server lists (Discord select menu limit: 25 options)
- Caching prevents repeated expensive API calls

**Implementation Notes:**
- Server list loaded once at startup, refreshed periodically
- Custom servers stored in memory after first load
- Tinfoil cache indexed by contentId for fast lookup

**Validation:**
- Test with 100+ servers to ensure no performance degradation
- Monitor memory usage stays under 150MB (NFR-001)

---

### NFR-004: Security

**Requirement:** No sensitive data in plaintext; rate limiting; permission checks

**Architecture Solution:**
- Environment variables for all secrets (TOKEN, API_LAN_KEY)
- python-dotenv and decouple for configuration
- Input validation on all user inputs (server format regex)
- Admin-only commands decorated with `@commands.default_member_permissions(administrator=True)`
- Rate limiting on custom emoji creation (Discord limitation)
- No sensitive data in log output (filter tokens, keys)

**Implementation Notes:**
- Settings loaded once at startup, not stored in memory longer than needed
- Server format validation: `r'^[a-zA-Z0-9.-]+:\d+$'`
- All Discord embeds use ephemeral=True for sensitive command responses

**Validation:**
- Audit logs for any sensitive data leakage
- Test permission enforcement on admin commands
- Verify server format validation rejects invalid input

---

### NFR-005: Maintainability

**Requirement:** 80% test coverage; clear separation of concerns; PEP 8 compliance

**Architecture Solution:**
- Modular structure: src/bot (commands, events), src/utils, src/config
- Type hints throughout (Python 3.9+)
- Docstrings on all public methods
- Async/await pattern consistent throughout
- Unit tests in tests/ directory with pytest

**Implementation Notes:**
- All public classes and methods have docstrings
- Configuration settings in typed Final constants
- Use logging module (not print) for debug output

**Validation:**
- Run pytest with coverage reports
- Use pre-commit hooks for linting (black, isort, flake8)

---

### NFR-006: Compatibility

**Requirement:** Python 3.9+; works in Docker; cross-platform for game launching

**Architecture Solution:**
- Uses only standard library and well-supported packages
- async I/O works on all platforms (Windows, macOS, Linux)
- Docker configuration provided (Dockerfile, docker-compose.yml)
- Environment-based configuration (no hardcoded paths)

**Implementation Notes:**
- Locale and timezone set via environment variables
- File paths use os.path for cross-platform compatibility
- All async operations use asyncio primitives

**Validation:**
- Test in Docker container
- Test on Windows, macOS, Linux if game launching is implemented

---

## Security Architecture

### Authentication

- **Discord Bot Token:** Environment variable TOKEN, never in code or logs
- **UptimeRobot API Key:** Environment variable API_LAN_KEY
- **No user authentication needed:** Discord handles user identity

### Authorization

- **Discord Permissions:** Handled by Discord
- **Admin Commands:** `@commands.default_member_permissions(administrator=True)` decorator
- **DM vs Guild:** Admin commands work in both contexts
- **Role-based checks:** Could be added if needed (not currently required)

### Data Encryption

- **In Transit:** All external API calls use HTTPS
- **At Rest:** JSON file storage on local filesystem (no database encryption needed for non-sensitive data)
- **Secrets:** Stored in .env file, not in code or version control

### Security Best Practices

- **Input Validation:** Server format regex validation before processing
- **SQL Injection:** N/A (no SQL database)
- **XSS:** N/A (Discord embeds, not web)
- **CSRF:** N/A (Discord, not web)
- **Rate Limiting:** Discord handles rate limits on API side; internal rate limits on emoji creation
- **Security Headers:** N/A (not a web server)

---

## Scalability & Performance

### Scaling Strategy

**Horizontal Scaling:**
- Single bot instance sufficient for current scale (<1000 servers, <100 users)
- Bot is inherently horizontally scalable if sharded (Discord sharding for large bots)
- No database to scale; JSON files are read-only after startup

**Vertical Scaling:**
- Memory: Target <150MB (Tinfoil cache ~50MB, code ~10MB, OS ~30MB)
- CPU: Low idle usage; spikes during server refresh

**Future Considerations:**
- If scale increases significantly, could move to Redis for caching
- If many servers, could implement pagination for server list

### Performance Optimization

- **Caching:** TinfoilCacheManager with 24-hour TTL
- **Connection Reuse:** aiohttp ClientSession reused
- **Parallel Queries:** asyncio.gather for multiple GraphQL queries
- **Lazy Loading:** Only fetch data when requested

### Caching Strategy

| Data | Cache Location | TTL | Invalidation |
|------|----------------|-----|--------------|
| Tinfoil Games | TinfoilCacheManager (memory) | 24 hours | Manual refresh or TTL expiry |
| Server List | LanPlayBot.lan_servers (memory) | 5 minutes (background refresh) | On command invocation |

### Load Balancing

Not applicable - single bot instance. If scale requires, Discord provides built-in gateway sharding.

---

## Reliability & Availability

### High Availability Design

- **Single Point of Failure:** Discord connection (mitigated by auto-reconnect)
- **Redundancy:** None needed for Level 2 project
- **Failover:** Bot reconnects automatically on Discord gateway disconnect
- **Circuit Breaker:** If external API fails repeatedly, log and continue with cached/stale data

### Disaster Recovery

- **RPO (Recovery Point Objective):** 24 hours (Tinfoil cache), custom servers on disk
- **RTO (Recovery Time Objective):** Minutes to restart bot
- **Backup:** Custom servers saved to data/lan_servers.json (version controlled)
- **Restore:** Restart bot loads data from files

### Backup Strategy

- Custom servers: data/lan_servers.json (manually backed up)
- Tinfoil cache: In-memory, restored from API on restart
- Configuration: .env file (external)

### Monitoring & Alerting

- **Structured Logging:** Python logging module with levels (DEBUG, INFO, WARN, ERROR)
- **Key Metrics:** Command response times, server refresh duration, error counts
- **Health Check:** On-ready event logs confirm bot is operational
- **Error Context:** All exceptions logged with traceback

---

## Development Architecture

### Code Organization

```
src/
├── bot/
│   ├── __init__.py
│   ├── bot.py          # Main bot class (LanPlayBot)
│   ├── commands.py     # Slash command handlers (LanPlayCommands cog)
│   └── events.py       # Event handlers (LanPlayEvents cog)
├── config/
│   ├── __init__.py
│   ├── settings.py     # Configuration constants
│   └── locale/         # i18n files
├── utils/
│   ├── __init__.py
│   ├── lanplay_client.py   # GraphQL client, Tinfoil cache
│   ├── server_manager.py   # Custom server CRUD
│   ├── localization.py     # i18n helpers
│   ├── version.py          # Version management
│   └── changelog.py        # Changelog parsing
data/
└── lan_servers.json   # Custom server storage
tests/
├── ...
```

### Module Structure

| Module | Responsibility | Public API |
|--------|---------------|------------|
| bot.py | Bot lifecycle | LanPlayBot, create_bot() |
| commands.py | Discord commands | LanPlayCommands (Cog) |
| events.py | Discord events | LanPlayEvents (Cog) |
| settings.py | Configuration | Public constants |
| lanplay_client.py | External APIs | LanPlayClient, TinfoilCacheManager, get_lan_servers() |
| server_manager.py | Custom servers | load_custom_servers(), save_custom_servers(), etc. |

### Testing Strategy

- **Unit Tests:** Test individual functions (server_manager, lanplay_client utilities)
- **Integration Tests:** Test command flow with mocked Discord
- **Coverage Target:** 80% for critical paths
- **Framework:** pytest with pytest-asyncio

### CI/CD Pipeline

**GitHub Actions (existing):**
- Pre-commit hooks: lint, format, type-check
- On push: run tests
- On release: build and push Docker image

**Stages:**
1. Lint (black, isort, flake8)
2. Type check (mypy)
3. Test (pytest)
4. Build (Docker)
5. Deploy (optional)

---

## Deployment Architecture

### Environments

| Environment | Purpose | Configuration |
|-------------|---------|---------------|
| Development | Local testing | .env with dev token |
| Production | Live bot | .env with production token, monitored |

### Deployment Strategy

- **Container:** Docker with multi-stage build
- **Orchestration:** Docker Compose for local, Kubernetes for production (future)
- **Updates:** Rolling update with health checks

### Infrastructure as Code

- **Dockerfile:** Multi-stage build for small image
- **docker-compose.yml:** Local development setup
- **.env:** Configuration (not in version control)

---

## Requirements Traceability

### Functional Requirements Coverage

| FR ID | FR Name | Components | Implementation Notes |
|-------|---------|------------|----------------------|
| FR-001 | LAN Game Discovery | LanPlayClient, Commands (Cog) | GraphQL queries, Tinfoil enrichment |
| FR-002 | Game Session Management | Commands (Cog), LanPlayClient | Server selection, display of games |
| FR-003 | Game Launching | (Future) Companion Client | Out of scope for bot - companion client separate |
| FR-004 | Real-time Updates | Events (Cog), LanPlayClient | Periodic refresh, event logging |
| FR-005 | User Interface & Commands | Commands (Cog), Localization | All slash commands, autocomplete |
| FR-006 | Emoji Management | Commands (Cog) | Rate limiting, cleanup (if emojis used) |
| FR-007 | Configuration Management | Settings, Configuration | Environment variables, JSON persistence |
| FR-008 | Logging & Monitoring | Events (Cog), all components | Structured logging, error context |

### Non-Functional Requirements Coverage

| NFR ID | NFR Name | Solution | Validation |
|--------|----------|----------|------------|
| NFR-001 | Performance | Async I/O, caching, connection pooling | Response time monitoring |
| NFR-002 | Reliability | Error handling, retry, auto-reconnect | Uptime monitoring |
| NFR-003 | Scalability | Efficient data structures, caching | Load testing |
| NFR-004 | Security | Environment secrets, input validation, permissions | Security audit |
| NFR-005 | Maintainability | Clean modules, tests, type hints | Coverage reports |
| NFR-006 | Compatibility | Python 3.9+, cross-platform async | Multi-platform testing |

---

## Trade-offs & Decision Log

### Decision: Modular Monolith vs Microservices

**Decision:** Use Modular Monolith with Layered Architecture

**Trade-off:**
- ✓ Gain: Simple deployment, easy to debug, low overhead
- ✓ Gain: Well-suited for Level 2 project scale
- ✗ Lose: Cannot scale individual components independently
- ✗ Lose: All components share same failure domain

**Rationale:** For a single Discord bot with 8 FRs, microservices would introduce unnecessary complexity. The current scale (<1000 servers, <100 users) does not warrant distributed architecture.

---

### Decision: JSON File Storage vs Database

**Decision:** JSON file storage with in-memory caching

**Trade-off:**
- ✓ Gain: Zero infrastructure, simple backup
- ✓ Gain: Fast for small datasets
- ✗ Lose: Not suitable for high-write scenarios
- ✗ Lose: No atomic transactions
- ✗ Lose: Limited query capability

**Rationale:** Current data volume (<1000 servers, <100 sessions) does not require a database. JSON files provide sufficient capability with much lower operational overhead.

---

### Decision: Disnake over discord.py

**Decision:** Use Disnake (existing library)

**Trade-off:**
- ✓ Gain: Async-first, modern API
- ✓ Gain: Built-in i18n support
- ✓ Gain: Active development
- ✗ Lose: Smaller community than discord.py
- ✗ Lose: Some discord.py extensions may not work

**Rationale:** Project already uses Disnake. The async-first design aligns well with the async architecture throughout the codebase.

---

## Open Issues & Risks

| Issue | Risk | Mitigation |
|-------|------|------------|
| Tinfoil API rate limiting | Game names unavailable | Fallback to contentId display |
| UptimeRobot API failure | Server list empty | Use cached servers, log warning |
| Game launching cross-platform | Complex implementation | Future companion client, out of scope |
| Custom server JSON corruption | Data loss | Validate on load, keep backups |

---

## Assumptions & Constraints

**Assumptions:**
- Users have network connectivity to reach LAN Play servers
- Discord bot has necessary permissions (administrator for some commands)
- Target network is typical home LAN (not heavily segmented enterprise)
- Most games use standard LAN Play discovery protocols

**Constraints:**
- Discord API rate limits apply to all Discord interactions
- Python 3.9+ required for typing and async features
- File-based storage is single-point (no distributed access)

---

## Future Considerations

| Feature | Complexity | When |
|---------|------------|------|
| Redis caching | Medium | If Tinfoil API becomes bottleneck |
| Game launching companion | High | If user demand warrants |
| Web dashboard | High | If admin UI needed beyond Discord |
| PostgreSQL migration | Medium | If data grows beyond JSON capability |
| Discord sharding | Low | If bot reaches guild/user limits |

---

## Approval & Sign-off

**Review Status:**
- [ ] Technical Lead
- [ ] Product Owner
- [ ] Security Architect (if applicable)
- [ ] DevOps Lead

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-18 | Gemini Bot | Initial architecture |

---

## Next Steps

### Phase 4: Sprint Planning & Implementation

Run `/sprint-planning` to:
- Break epics into detailed user stories
- Estimate story complexity
- Plan sprint iterations
- Begin implementation following this architectural blueprint

**Key Implementation Principles:**
1. Follow component boundaries defined in this document
2. Implement NFR solutions as specified
3. Use technology stack as defined
4. Follow API contracts exactly
5. Adhere to security and performance guidelines

---

**This document was created using BMAD Method v6 - Phase 3 (Solutioning)**

*To continue: Run `/workflow-status` to see your progress and next recommended workflow.*

---

## Appendix A: Technology Evaluation Matrix

| Technology | Alternative 1 | Alternative 2 | Decision | Justification |
|------------|---------------|---------------|----------|---------------|
| Python 3.9+ | Node.js | Go | ✓ Python | Existing codebase, async support |
| Disnake | discord.py | discord.js | ✓ Disnake | Existing use, async-first |
| JSON files | SQLite | PostgreSQL | ✓ JSON | Low data volume, zero infra |
| aiohttp | requests (sync) | httpx | ✓ aiohttp | Existing use, async |
| GraphQL (gql) | REST | raw HTTP | ✓ gql | Existing pattern, type-safe |

---

## Appendix B: Capacity Planning

| Metric | Current | Target | Headroom |
|--------|---------|--------|----------|
| Users | <100 concurrent | 100 | 0% |
| Servers | <1000 | 1000 | 0% |
| Memory | <150MB | 150MB | 0% |
| CPU (idle) | <10% | <50% | 400% |
| Command latency | <500ms (cached) | <2000ms | 300% |

---

## Appendix C: Cost Estimation

| Component | Cost | Notes |
|-----------|------|-------|
| UptimeRobot | Free | Up to 50 monitors |
| Tinfoil Media | Free | Public API |
| Discord bot | Free | No bot cost |
| Hosting | $5-20/mo | Small VPS or container hosting |
| Domain | $0-10/yr | If needed for custom servers |
| **Total** | **$5-30/mo** | |