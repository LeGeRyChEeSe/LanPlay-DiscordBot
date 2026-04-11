# LanPlay-DiscordBot

Modern Discord bot for real-time LAN Play server monitoring of Nintendo Switch games.

## Project Overview

- **Purpose**: Monitor Nintendo Switch LAN Play servers, active games, and player counts with Discord integration.
- **Main Technologies**:
  - **Language**: Python 3.12+
  - **Discord Library**: [disnake](https://github.com/DisnakeDev/disnake) (Discord.py fork)
  - **APIs**: GraphQL (via `gql`), UptimeRobot API, Tinfoil API (for game metadata)
  - **Configuration**: `python-decouple`, `python-dotenv`
  - **Containerization**: Docker & Docker Compose
- **Architecture**:
  - `main.py`: Entry point.
  - `src/bot/`: Bot core, slash commands, and event handlers.
  - `src/utils/`: API clients, server management, and versioning utilities.
  - `src/config/`: Application settings and localization data.

## Building and Running

### Prerequisites
- Discord Bot Token
- LAN Play API Key (extracted from lan-play.com)

### Key Commands
- **Install Dependencies**: `make install`
- **Run Bot**: `python main.py`
- **Build Docker**: `make docker-build`
- **Run Docker**: `make docker-run` (uses `docker-compose`)
- **Lint Code**: `make lint`
- **Format Code**: `make format`

## Development Conventions

- **Versioning**: Custom semantic versioning managed via `VERSION` file and `scripts/version.sh`.
  - Bump versions: `make bump-patch`, `make bump-minor`, `make bump-major`.
- **Changelog**: Automated management using `CHANGELOG.md`.
  - Add changes: `make add-change TYPE=added DESC="New feature"`.
- **Localization**: Multi-language support (EN/FR) using `disnake` i18n.
  - Locale files: `src/config/locale/`.
- **Code Style**:
  - **Formatter**: Black (line length 100).
  - **Linter**: Flake8.
- **Custom Servers**: User-added servers are persisted in `data/lan_servers.json`.

## Key Files
- `main.py`: Application entry point.
- `src/bot/bot.py`: Bot initialization and configuration.
- `src/bot/commands.py`: Implementation of slash commands.
- `src/utils/lanplay_client.py`: GraphQL client for server data fetching.
- `src/config/settings.py`: Centralized configuration management.
- `Makefile`: Comprehensive development and build automation.
- `Dockerfile` & `docker-compose.yml`: Containerization setup.
