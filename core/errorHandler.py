import sys
import os
import traceback
import aiohttp
import pendulum
from core.config import config
from core.logger import logger
from core.bot_config import config as bot_config

class ErrorHandler:
    def __init__(self):
        self.webhook_url = config.logging.ERROR_WEBHOOK_URL
        self.errors_dir = os.path.join(os.getcwd(), 'errors')
        self._ensure_error_dir()

    def _ensure_error_dir(self):
        if not os.path.exists(self.errors_dir):
            os.makedirs(self.errors_dir)

    def log_error_to_file(self, error_msg):
        """Saves the error stack trace to a timestamped file."""
        try:
            # Check if error logging is enabled
            if not bot_config.error_logging.ENABLED:
                return

            filename = f"{pendulum.now().to_iso8601_string().replace(':', '-')}.txt"
            filepath = os.path.join(self.errors_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(error_msg)
        except Exception:
            pass # Silent fail to prevent recursion

    async def send_webhook_notification(self, message):
        """Sends an error embed to the configured Discord webhook."""
        if not self.webhook_url or "YOUR_DISCORD_WEBHOOK_URL" in self.webhook_url:
            return

        embed = {
            "title": "Error Notification (Python)",
            "description": f"```py\n{message[:2000]}\n```",
            "color": 0xff0000,
            "timestamp": pendulum.now().to_iso8601_string(),
            "footer": {"text": "Discobase Python Error Logger"}
        }

        async with aiohttp.ClientSession() as session:
            try:
                await session.post(self.webhook_url, json={"embeds": [embed]})
            except Exception as e:
                logger.warning(f"Failed to send error notification: {e}")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Standard exception hook for synchronous errors."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error(f"Uncaught Exception: {exc_value}")
        
        self.log_error_to_file(error_msg)
        # Webhook requires async loop, handled elsewhere or via loop.create_task

# Global error handler instance
error_handler = ErrorHandler()

def setup_crash_protection():
    """Injects the error handler into the system."""
    sys.excepthook = error_handler.handle_exception
