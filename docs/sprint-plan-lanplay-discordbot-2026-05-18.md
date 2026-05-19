# Sprint Plan: LanPlay-DiscordBot

**Date:** 2026-05-18
**Scrum Master:** Gemini Bot
**Project Level:** 2
**Total Stories:** 14
**Total Points:** 45
**Planned Sprints:** 2

---

## Executive Summary

This sprint plan addresses critical bugs identified in the code review, completes missing functional requirements from the PRD, and implements architectural improvements to meet NFRs. The plan prioritizes bug fixes and core functionality before enhancement work.

**Key Metrics:**
- Total Stories: 14
- Total Points: 45
- Sprints: 2
- Team Capacity: 30 points per sprint
- Target Completion: 2026-06-01 (2 sprints x 2 weeks)

---

## Team Capacity

**Configuration:**
- Team Size: 1 developer
- Sprint Length: 2 weeks (10 workdays)
- Productive Hours/Day: 6 hours
- Holidays/PTO: None
- Experience Level: Senior (2 hours/point)

**Calculation:**
```
Total Hours = 1 × 10 × 6 = 60 hours
Capacity = 60 ÷ 2 = 30 points per sprint
```

**Buffer:** 10-20% reserved for unknowns and bugs (~5-6 points per sprint)

---

## Story Inventory

### Epic 1: Core Discovery & Session Management (Must Have)

---

### STORY-001: Fix Critical Async/Await Bug in Bot Startup

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As a developer
I want the bot to correctly load custom servers on startup
So that users can access their custom server configurations

**Acceptance Criteria:**
- [ ] `load_custom_servers()` is called with `await` in `_load_servers_async()`
- [ ] Custom servers are merged with API servers without blocking
- [ ] Bot logs confirmation of total servers loaded
- [ ] Error handling catches and logs any loading failures

**Technical Notes:**
- File: `src/bot/bot.py:73`
- Fix: Change `load_custom_servers()` → `await load_custom_servers()`
- Impact: Prevents coroutine from being stored instead of server list

**Dependencies:**
- None

**Story Points:** 1

---

### STORY-002: Fix Logic Error in _has_rooms Function

**Epic:** EPIC-001 (Core Discovery & Session Management)
**Priority:** Must Have

**User Story:**
As a user
I want to see servers even when they have zero active rooms
So that I can check server status regardless of current activity

**Acceptance Criteria:**
- [ ] Servers with 0 rooms display correctly (not filtered out as "no rooms")
- [ ] The `_has_rooms()` function correctly identifies valid server response structure
- [ ] Empty room lists are handled gracefully in display logic

**Technical Notes:**
- File: `src/utils/lanplay_client.py:169-171`
- Current: `return isinstance(server.get("room", []), list) and bool(server["room"])`
- Problem: `bool([])` is False, so servers with 0 rooms are treated as invalid
- Fix: Remove `and bool(server["room"])` condition

**Dependencies:**
- STORY-001 (async loading must work first)

**Story Points:** 1

---

### STORY-003: Fix Server Sorting by Numeric Uptime

**Epic:** EPIC-001 (Core Discovery & Session Management)
**Priority:** Must Have

**User Story:**
As a user
I want servers sorted by actual uptime percentage (not alphabetically)
So that I can quickly find the most reliable servers

**Acceptance Criteria:**
- [ ] Servers sort correctly: "99.99" comes before "9.95" (numeric, not string)
- [ ] Sorting works for both API servers and custom servers
- [ ] Handle malformed uptime ratios gracefully (default to "0")

**Technical Notes:**
- File: `src/bot/commands.py:309-311`
- Current: `key=lambda x: x.get("all_time_uptime_ratio", "0")`
- Problem: String sort puts "9" before "10"
- Fix: `key=lambda x: float(x.get("all_time_uptime_ratio", "0"))`

**Dependencies:**
- None

**Story Points:** 1

---

### STORY-004: Add Graceful Shutdown with Signal Handling

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As an operator
I want the bot to shut down gracefully when receiving SIGTERM
So that I can deploy updates without interrupting active users

**Acceptance Criteria:**
- [ ] Bot handles SIGTERM signal (not just SIGINT)
- [ ] On shutdown: log message, close connections, save state
- [ ] On shutdown: exit cleanly with code 0
- [ ] Shutdown completes within 10 seconds

**Technical Notes:**
- File: `src/bot/bot.py`
- Add: `signal.signal(signal.SIGTERM, _shutdown_handler)`
- Add: `_shutdown_handler` function that sets stop flag
- Add: Cleanup in main run loop

**Dependencies:**
- None

**Story Points:** 3

---

### STORY-005: Remove Unused requests Library

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As a developer
I want to remove the unused requests library
So that dependency list is clean and matches actual code

**Acceptance Criteria:**
- [ ] `requests==2.32.5` removed from requirements.txt
- [ ] No imports of `requests` anywhere in source code
- [ ] All HTTP operations use `aiohttp` (async)
- [ ] CI passes after removal

**Technical Notes:**
- File: `requirements.txt:4`
- Files to check: All files in `src/`
- PRD requirement: "aiohttp (for async HTTP requests, replacement for requests)"

**Dependencies:**
- None

**Story Points:** 1

---

### STORY-006: Implement /lanplay discover On-Demand Scan

**Epic:** EPIC-001 (Core Discovery & Session Management)
**Priority:** Must Have

**User Story:**
As a Discord user
I want to trigger a manual network scan with `/lanplay discover`
So that I can find games immediately without waiting for periodic scans

**Acceptance Criteria:**
- [ ] Command `/lanplay discover` or `/scan` exists
- [ ] On invoke: bot scans for LAN Play enabled servers
- [ ] Results posted to channel with embed (game name, host IP, player count)
- [ ] Command responds within 10 seconds (NFR-001)
- [ ] Graceful handling of network errors

**Technical Notes:**
- Component: Commands (Cog) + LanPlayClient
- Use existing `get_lan_servers()` and GraphQL query logic
- Add as new slash command in `commands.py`
- Consider adding rate limit (1 per 30 seconds per user)

**Dependencies:**
- STORY-001, STORY-002 (core bug fixes)

**Story Points:** 3

---

### STORY-007: Implement Session Management Commands

**Epic:** EPIC-001 (Core Discovery & Session Management)
**Priority:** Must Have

**User Story:**
As a LAN party organizer
I want to create, join, and leave game sessions via Discord
So that I can manage gaming sessions without leaving the platform

**Acceptance Criteria:**
- [ ] `/lanplay create <game> [options]` - Creates new session, posts to channel
- [ ] `/lanplay join <session_id>` - Join existing session
- [ ] `/lanplay leave` - Leave current session
- [ ] Session creator can configure: max players, map, game type
- [ ] Active sessions displayed with status updates
- [ ] Sessions auto-expire after configurable timeout

**Technical Notes:**
- Component: Commands (Cog) + new SessionManager
- Data model: Session entity (id, game, host, players, max_players, status, created_at)
- Storage: JSON file or in-memory with persistence
- Consider: Auto-generated session IDs (UUID)

**Dependencies:**
- STORY-006 (discover command)

**Story Points:** 5

---

### STORY-008: Implement Periodic Background Refresh

**Epic:** EPIC-002 (Enhanced User Experience)
**Priority:** Should Have

**User Story:**
As a Discord user
I want the bot to automatically refresh server status every 5 minutes
So that I always see current game availability without manual commands

**Acceptance Criteria:**
- [ ] Background task runs every 5 minutes (configurable)
- [ ] Refresh updates server list and game room cache
- [ ] Updates happen without blocking command responses
- [ ] Errors in refresh don't crash the bot
- [ ] Refresh can be disabled via configuration

**Technical Notes:**
- Component: Events (Cog) or new BackgroundTasks component
- Use `asyncio.create_task()` for independent refresh loop
- Add configurable `SCAN_INTERVAL_SECONDS` to settings
- Implement graceful error handling and retry

**Dependencies:**
- STORY-001 (async loading)

**Story Points:** 3

---

### STORY-009: Implement Retry with Exponential Backoff

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As a developer
I want network requests to automatically retry on transient failures
So that the bot remains reliable despite temporary network issues

**Acceptance Criteria:**
- [ ] HTTP/GraphQL requests retry up to 3 times on failure
- [ ] Exponential backoff: 1s, 2s, 4s between retries
- [ ] Different retry policies for different operations (scan vs critical)
- [ ] Max retry time of 10 seconds total
- [ ] Errors logged after all retries exhausted

**Technical Notes:**
- Add to: `lanplay_client.py`
- Create helper: `async def fetch_with_retry(session, url, max_retries=3)`
- Use `asyncio.sleep()` for backoff
- Handle different exception types differently (timeout vs connection error)

**Dependencies:**
- STORY-001

**Story Points:** 3

---

### STORY-010: Implement Rate Limiting on Commands

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As a bot operator
I want rate limiting on discovery and session commands
So that abusive users cannot spam the bot

**Acceptance Criteria:**
- [ ] Discovery command: max 1 per 30 seconds per user
- [ ] Session create: max 5 per minute per server
- [ ] Rate limit response is user-friendly (ephemeral message)
- [ ] Admins can bypass rate limits (optional)

**Technical Notes:**
- Use `disnake.ext.commands.Cooldown` or custom middleware
- Component: Commands (Cog)
- Add decorator: `@commands.cooldown(1, 30, commands.BucketType.user)`
- Handle rate limit with clear message

**Dependencies:**
- STORY-006

**Story Points:** 2

---

### STORY-011: Fix Admin Command Permission in DMs

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Must Have

**User Story:**
As a bot operator
I want admin commands to only work in guilds (not DMs)
So that random users cannot manage servers via DM

**Acceptance Criteria:**
- [ ] `/add` and `/delete` commands check `inter.guild is not None`
- [ ] If called in DM: response "This command is only available in servers"
- [ ] Error is ephemeral (only user sees it)
- [ ] Other commands continue to work in DMs

**Technical Notes:**
- File: `src/bot/commands.py`
- Add check at start of `add_server_command` and `delete_server_command`
- Response: `await inter.response.send_message(..., ephemeral=True)`

**Dependencies:**
- None

**Story Points:** 2

---

### STORY-012: Add Health Check Endpoint

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Should Have

**User Story:**
As an operator
I want a health check endpoint for container orchestration
So that Docker/health checks can verify bot is operational

**Acceptance Criteria:**
- [ ] Bot responds to health check requests (or logs health status)
- [ ] On-ready event logs "Bot is operational" with timestamp
- [ ] Health status accessible for monitoring integration
- [ ] Bot does not need external web server (can be log-based for now)

**Technical Notes:**
- Implement as: logging health on ready + periodic (every 60s) heartbeat log
- Or: Simple HTTP server on port (optional, not required for PRD)
- Add to: `bot.py` on_ready handler or new BackgroundTasks

**Dependencies:**
- STORY-004 (graceful shutdown as context)

**Story Points:** 2

---

### STORY-013: Add Constants for Magic Numbers

**Epic:** EPIC-003 (Operational Excellence)
**Priority:** Low

**User Story:**
As a developer
I want magic numbers extracted to named constants
So that code is more readable and maintainable

**Acceptance Criteria:**
- [ ] `MAX_SELECT_OPTIONS = 25` (Discord select limit)
- [ ] `EMOJI_LIMIT_STANDARD = 50` (Discord emoji limit)
- [ ] `EMOJI_LIMIT_SOFT = 48` (when to start cleanup)
- [ ] `SERVER_FORMAT_PATTERN` compiled regex constant
- [ ] `TINFOIL_CACHE_TTL_HOURS = 24` in settings

**Technical Notes:**
- Files: `commands.py`, `settings.py`, `lanplay_client.py`
- Move magic numbers to module-level constants
- Use `Final` type hint for immutability
- Add docstring explaining what each constant represents

**Dependencies:**
- None

**Story Points:** 2

---

### STORY-014: Improve Emoji Cleanup Logic

**Epic:** EPIC-001 (Core Discovery & Session Management)
**Priority:** Medium

**User Story:**
As a bot operator
I want emoji cleanup to properly maintain Discord limits
So that the bot doesn't fail when creating emojis at the limit

**Acceptance Criteria:**
- [ ] When emoji limit reached, delete enough emojis to get well below limit (e.g., delete 5 when at 48+)
- [ ] Cleanup targets oldest emojis first
- [ ] Cleanup doesn't delete emojis not created by the bot (if possible)
- [ ] Logs emoji cleanup actions

**Technical Notes:**
- File: `src/bot/events.py:213-221`
- Current: Deletes only 1 emoji, may fail on next creation
- Fix: Loop until `len(guild.emojis) < EMOJI_LIMIT_SOFT`
- Use: `sorted(guild.emojis, key=lambda e: e.created_at)[:5]` to get oldest 5

**Dependencies:**
- STORY-013 (constant extraction)

**Story Points:** 2

---

## Story Summary Table

| ID | Title | Epic | Priority | Points | Status |
|----|-------|------|----------|--------|--------|
| STORY-001 | Fix async/await bug | EPIC-003 | Must Have | 1 | Not Started |
| STORY-002 | Fix _has_rooms logic | EPIC-001 | Must Have | 1 | Not Started |
| STORY-003 | Fix server sorting | EPIC-001 | Must Have | 1 | Not Started |
| STORY-004 | Add graceful shutdown | EPIC-003 | Must Have | 3 | Not Started |
| STORY-005 | Remove requests lib | EPIC-003 | Must Have | 1 | Not Started |
| STORY-006 | Implement /discover | EPIC-001 | Must Have | 3 | Not Started |
|STORY-007|Session mgmt commands|EPIC-001|Must Have|5|Done|||STORY-008|Periodic refresh|EPIC-002|Should Have|3|Done|||STORY-009|Retry with backoff|EPIC-003|Must Have|3|Not Started||
| STORY-010 | Rate limiting | EPIC-003 | Must Have | 2 | Not Started |
| STORY-011 | Fix DM permissions | EPIC-003 | Must Have | 2 | Not Started |
|STORY-012|Health check endpoint|EPIC-003|Should Have|2|Done|||STORY-013|Constants for magic numbers|EPIC-003|Low|2|Not Started||
|STORY-014|Improve emoji cleanup|EPIC-001|Medium|2|Done|||
**Total:** 14 stories, 31 points

---

## Sprint Allocation

### Sprint 1 (Weeks 1-2) - 22/30 points

**Goal:** Fix critical bugs and complete core functionality

**Stories:**
- STORY-001: Fix async/await bug (1 point) - Must Have
- STORY-002: Fix _has_rooms logic (1 point) - Must Have
- STORY-003: Fix server sorting (1 point) - Must Have
- STORY-004: Add graceful shutdown (3 points) - Must Have
- STORY-005: Remove requests lib (1 point) - Must Have
- STORY-006: Implement /discover (3 points) - Must Have
- STORY-009: Retry with backoff (3 points) - Must Have
- STORY-010: Rate limiting (2 points) - Must Have
- STORY-011: Fix DM permissions (2 points) - Must Have

**Total:** 17 points / 30 capacity (56% utilization)

**Buffer:** 13 points for unknowns, bugs, or carryover

**Risks:**
- STORY-006 depends on bug fixes (STORY-001, STORY-002)
- GraphQL client connection pooling may need research

**Dependencies:**
- None external

---

### Sprint 2 (Weeks 3-4) - 19/30 points

**Goal:** Complete session management and enhanced features

**Stories:**
- STORY-007: Session management commands (5 points) - Must Have
- STORY-008: Periodic background refresh (3 points) - Should Have
- STORY-012: Health check endpoint (2 points) - Should Have
- STORY-013: Constants for magic numbers (2 points) - Low
- STORY-014: Improve emoji cleanup (2 points) - Medium

**Total:** 2 points / 30 capacity (6% utilization)

**Buffer:** 16 points for unknowns, polish, or FR-003 game launching prep

**Risks:**
- STORY-007 is largest story (5 points) - could break down if complex
- FR-003 (Game Launching) not included - marked as future companion client in PRD

**Dependencies:**
- STORY-007 depends on STORY-006

---

## Epic Traceability

| Epic ID | Epic Name | Stories | Total Points | Sprint |
|---------|-----------|---------|--------------|--------|
| EPIC-001 | Core Discovery & Session Management | STORY-002, STORY-003, STORY-006, STORY-007, STORY-014 | 12 points | Sprint 1-2 |
| EPIC-002 | Enhanced User Experience | STORY-008 | 3 points | Sprint 2 |
| EPIC-003 | Operational Excellence | STORY-001, STORY-004, STORY-005, STORY-009, STORY-010, STORY-011, STORY-012, STORY-013 | 16 points | Sprint 1-2 |

**Note:** EPIC-001 has highest priority and most points. EPIC-003 stories (bug fixes) are prioritized first in Sprint 1.

---

## Functional Requirements Coverage

| FR ID | FR Name | Story | Sprint | Status |
|-------|---------|-------|--------|--------|
| FR-001 | LAN Game Discovery | STORY-006 | 1 | Not Started |
| FR-002 | Game Session Management | STORY-007 | 2 | Not Started |
| FR-003 | Game Launching | (Out of scope - companion client) | - | - |
| FR-004 | Real-time Updates | STORY-008 | 2 | Not Started |
| FR-005 | User Interface & Commands | STORY-006, STORY-007 | 1-2 | Not Started |
| FR-006 | Emoji Management | STORY-014 | 2 | Not Started |
| FR-007 | Configuration Management | STORY-013 | 2 | Not Started |
| FR-008 | Logging & Monitoring | STORY-004, STORY-012 | 5 | Not Started |

**Coverage:** 7/8 FRs addressed (FR-003 out of scope per PRD)

---

## Non-Functional Requirements Coverage

| NFR ID | NFR Name | Solution | Stories | Sprint |
|--------|----------|----------|---------|--------|
| NFR-001 | Performance | Async I/O, caching, connection pooling | STORY-009 | 1 |
| NFR-002 | Reliability | Retry with backoff, graceful shutdown, error handling | STORY-004, STORY-009 | 1 |
| NFR-003 | Scalability | Efficient data structures, caching | STORY-006 | 1 |
| NFR-004 | Security | Rate limiting, DM permissions, input validation | STORY-010, STORY-011 | 1 |
| NFR-005 | Maintainability | Constants, clean code, tests | STORY-005, STORY-013 | 1 |
| NFR-006 | Compatibility | Already compliant (Python 3.9+, async) | - | - |

**Coverage:** 6/6 NFRs addressed

---

## Risks and Mitigation

**High:**
- STORY-007 (Session Management) is 5 points - largest story. Risk of underestimate.
- **Mitigation:** Break down during Sprint 1 review if needed; allocate extra buffer

**Medium:**
- External API dependencies (UptimeRobot, Tinfoil) may rate limit or fail
- **Mitigation:** STORY-009 (retry with backoff) handles transient failures

**Low:**
- Discord API changes could break emoji cleanup or permissions
- **Mitigation:** Log warnings; graceful degradation if APIs change

---

## Dependencies

**Internal:**
- STORY-006 (discover) depends on STORY-001, STORY-002
- STORY-007 (session mgmt) depends on STORY-006
- STORY-008 (periodic refresh) depends on STORY-001

**External:**
- UptimeRobot API (monitoring servers)
- Tinfoil Media API (game metadata)
- Discord API (bot functionality)

---

## Definition of Done

For a story to be considered complete:
- [ ] Code implemented and committed to feature branch
- [ ] Unit tests written and passing (or update existing tests)
- [ ] Code reviewed (self-review acceptable for solo)
- [ ] All acceptance criteria met
- [ ] No new linting/type errors introduced
- [ ] Deployed to test environment (if applicable)
- [ ] Documentation updated (docstrings, README if needed)

---

## Next Steps

**Immediate:** Begin Sprint 1

**Sprint Cadence:**
- Sprint length: 2 weeks
- Sprint planning: Day 1 of Week 1
- Sprint review: End of Week 2
- Sprint retrospective: End of Week 2

**Recommended Implementation Order:**
1. STORY-001 (async bug - foundation for others)
2. STORY-002, STORY-003 (logic bugs - quick wins)
3. STORY-005 (remove requests - cleanup)
4. STORY-004 (graceful shutdown - operational)
5. STORY-009 (retry logic - reliability)
6. STORY-010 (rate limiting - security)
7. STORY-011 (DM permissions - security)
8. STORY-006 (discover command - core feature)

**Commands:**
- Run `/dev-story STORY-001` to implement first story
- Run `/sprint-status` to check progress

---

**This plan was created using BMAD Method v6 - Phase 4 (Implementation Planning)**

*To continue: Run `/workflow-status` to see your progress and next recommended workflow.*