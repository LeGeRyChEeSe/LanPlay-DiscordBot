"Rate limiting utilities for the bot."
import time
from collections import defaultdict
from typing import Dict, List

class RateLimiter:
    "A simple rate limiter using a sliding window."
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Maximum number of calls allowed in the time window.
            time_window: Time window in seconds.
        """
        self.max_calls = max_calls
        self.time_window = time_window
        # user_id -> list of timestamps
        self.calls: Dict[int, List[float]] = defaultdict(list)
    def is_allowed(self, user_id: int) -> bool:
        "Check if a user is allowed to make a call."
        now = time.time()
        # Get the timestamps for this user
        timestamps = self.calls[user_id]
        # Remove timestamps older than the time window
        timestamps[:] = [ts for ts in timestamps if now - ts < self.time_window]
        # Check if we are at the limit
        if len(timestamps) >= self.max_calls:
            return False
        # Add the current timestamp
        timestamps.append(now)
        return True
    def reset(self) -> None:
        "Reset the rate limiter (for testing)."
        self.calls.clear()

# Global rate limiters for different commands
# Discovery command: allow 5 calls per minute per user
DISCOVERY_RATE_LIMITER = RateLimiter(max_calls=5, time_window=60)
# Add server command: allow 2 calls per minute per user (admin only, but still)
ADD_SERVER_RATE_LIMITER = RateLimiter(max_calls=2, time_window=60)
