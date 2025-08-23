"""Configuration settings for the LAN Play Discord Bot."""

import os
from typing import Final
from dotenv import load_dotenv
from decouple import config

# Load environment variables
load_dotenv()

# Bot Configuration
TOKEN: Final[str] = os.getenv("TOKEN", "")
API_LAN_KEY: Final[str] = config('API_LAN_KEY', default="")

# URLs
LAN_MENU_URL: Final[str] = "http://lan-play.com"
LAN_CONFIG_URL: Final[str] = "http://lan-play.com/install-switch"
IMAGE_LANPLAY_URL: Final[str] = "http://lan-play.com/img/logo.f64272e3.png"
LIST_ALL_GAMES_URL: Final[str] = "https://tinfoil.media/Title/ApiJson/"
MONITORS_URL: Final[str] = "https://api.uptimerobot.com/v2/getMonitors"

# Bot Settings
LOCALE_DIR: Final[str] = "src/config/locale"
CUSTOM_SERVERS_FILE: Final[str] = "data/lan_servers.json"  # Store in data directory
TIMEZONE: Final[str] = "Europe/Paris"
LOCALE_SETTING: Final[str] = "en_US.UTF-8"