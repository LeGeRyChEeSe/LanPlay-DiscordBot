"""Entry point for the LAN Play Discord Bot."""

from src.bot.bot import create_bot

if __name__ == "__main__":
    bot = create_bot()
    bot.run()