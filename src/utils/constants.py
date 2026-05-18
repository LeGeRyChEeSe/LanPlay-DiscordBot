# Module-level constants for the LanPlay-DiscordBot project.

import re

# Discord limits
MAX_SELECT_OPTIONS: int = 25
EMOJI_LIMIT_STANDARD: int = 50  # Maximum emojis for non-boosted server
EMOJI_LIMIT_SOFT: int = 48      # When to start cleanup (below standard limit)

# Server validation
SERVER_FORMAT_PATTERN: re.Pattern = re.compile(r'^[a-zA-Z0-9.-]+:\d+$')

# Tinfoil Media cache
TINFOIL_CACHE_TTL_HOURS: int = 24
# Retry settings
RETRY_MAX_ATTEMPTS: int = 3
RETRY_BASE_DELAY: float = 1.0

# HTTP timeout settings (in seconds)
HTTP_TIMEOUT_SECONDS: int = 30
