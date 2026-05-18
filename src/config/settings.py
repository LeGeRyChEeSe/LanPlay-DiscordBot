"""Configuration settings for the LAN Play Discord Bot."""

import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN: Final[str] = os.getenv("TOKEN", "")
API_LAN_KEY: Final[str] = os.getenv("API_LAN_KEY", "")

# URLs
LAN_MENU_URL: Final[str] = "http://lan-play.com"
LAN_CONFIG_URL: Final[str] = "http://lan-play.com/install-switch"
IMAGE_LANPLAY_URL: Final[str] = "http://lan-play.com/img/logo.f64272e3.png"
LIST_ALL_GAMES_URL: Final[str] = "https://tinfoil.media/Title/ApiJson/"
MONITORS_URL: Final[str] = "https://api.uptimerobot.com/v2/getMonitors"

# Bot Settings
LOCALE_DIR: Final[str] = "src/config/locale"
CUSTOM_SERVERS_FILE: Final[str] = "data/lan_servers.json"  # Store in data directory
SESSION_DATA_FILE: Final[str] = "data/sessions.json"  # Store session data
TIMEZONE: Final[str] = "Europe/Paris"
LOCALE_SETTING: Final[str] = "en_US.UTF-8"

# Background Refresh Settings
SCAN_INTERVAL_SECONDS: Final[int] = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))  # 5 minutes
ENABLE_BACKGROUND_REFRESH: Final[bool] = os.getenv("ENABLE_BACKGROUND_REFRESH", "true").lower() == "true"