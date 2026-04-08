from motor.motor_asyncio import AsyncIOMotorClient
from core.config import config
from core.logger import logger
import asyncio

class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        if not config.mongodb_url or config.mongodb_url == "YOUR_MONGODB_URL_HERE":
            logger.info("MongoDB URL not provided. Skipping database connection.")
            return

        try:
            self.client = AsyncIOMotorClient(config.mongodb_url)
            # Try to ping the database to verify connection
            await self.client.admin.command('ping')
            self.db = self.client.get_database() # Uses the DB in the URL or default
            logger.success("Successfully connected to MongoDB! Database is ready.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None

# Global database instance
db = Database()
