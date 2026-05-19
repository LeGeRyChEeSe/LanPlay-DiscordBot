"""Health check HTTP server for the LAN Play Discord Bot."""

import logging
from aiohttp import web
from typing import Dict, Optional

from src.utils.version import version_manager

logger = logging.getLogger(__name__)


def create_health_app(bot_instance) -> web.Application:
    """Create an aiohttp web application for health checks.

    Args:
        bot_instance: The LanPlayBot instance to get server data from.

    Returns:
        An aiohttp web application.
    """
    app = web.Application()

    async def health_check(request):
        """Handle health check requests."""
        try:
            # Get server count from the bot's lan_servers
            server_count = 0
            if bot_instance.lan_servers and "monitors" in bot_instance.lan_servers:
                server_count = len(bot_instance.lan_servers["monitors"])

            # Calculate uptime
            uptime_seconds = 0
            if hasattr(bot_instance, '_start_time'):
                import time
                uptime_seconds = int(time.time() - bot_instance._start_time)

            # Get version
            version = version_manager.current() if hasattr(version_manager, 'current') else "unknown"

            # Prepare response
            response_data = {
                "status": "ready",
                "server_count": server_count,
                "uptime": uptime_seconds,
                "version": version
            }

            return web.json_response(response_data)
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )

    app.router.add_get('/health', health_check)
    return app


async def start_health_server(bot_instance, host: str = "0.0.0.0", port: int = 8080) -> Optional[web.AppRunner]:
    """Start the health check HTTP server.

    Args:
        bot_instance: The LanPlayBot instance.
        host: The host to bind to.
        port: The port to bind to.

    Returns:
        The AppRunner if started successfully, None otherwise.
    """
    try:
        app = create_health_app(bot_instance)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Health check server started on http://{host}:{port}/health")
        return runner
    except Exception as e:
        logger.error(f"Failed to start health check server: {e}")
        return None


async def stop_health_server(runner: Optional[web.AppRunner]):
    """Stop the health check HTTP server.

    Args:
        runner: The AppRunner to stop.
    """
    if runner:
        await runner.cleanup()
        logger.info("Health check server stopped")