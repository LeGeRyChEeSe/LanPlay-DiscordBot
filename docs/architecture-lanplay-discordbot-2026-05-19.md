---
name: lanplay-discordbot-architecture-2026
description: LanPlay-DiscordBot system architecture with disnake cogs, JSON persistence, rate limiting, health check
metadata:
  type: project
---

# LanPlay-DiscordBot Architecture Summary

## Pattern
Modular Monolith with Cogs (disnake)

## Components
1. LanPlayBot (bot.py) - Main bot, cogs setup, background tasks
2. LanPlayCommands (commands.py) - /lan create/list/delete, /add, /delete, /help
3. LanPlayEvents (events.py) - Join/Leave button handlers
4. SessionManager (session_manager.py) - Session state + JSON persistence
5. RateLimiter (rate_limiter.py) - Token bucket rate limiting
6. HealthServer (health_server.py) - HTTP /health endpoint
7. LanPlayAPIClient (lanplay_api.py) - LAN Play API HTTP client

## Tech Stack
- Python 3.11+, disnake (async Discord), aiohttp, JSON files
- Docker container, no external DB

## Key Decisions
- JSON persistence over SQLite (simplicity)
- In-memory rate limiting (single instance)
- Separate health server (non-blocking)

## Files
- docs/prd.md - Product Requirements Document
- docs/architecture-lanplay-discordbot-2026-05-19.md - Full architecture

## Next
Sprint Planning via /sprint-planning