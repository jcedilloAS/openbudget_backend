import asyncio
from typing import Dict


class NotificationManager:
    """Manages active SSE connections per user."""

    def __init__(self):
        self._queues: Dict[int, asyncio.Queue] = {}

    def connect(self, user_id: int) -> asyncio.Queue:
        """Register a new SSE connection for a user and return their queue."""
        queue: asyncio.Queue = asyncio.Queue()
        self._queues[user_id] = queue
        return queue

    def disconnect(self, user_id: int) -> None:
        """Remove the SSE connection for a user."""
        self._queues.pop(user_id, None)

    async def send(self, user_id: int, data: dict) -> None:
        """Send a notification to a connected user. Silently ignored if not connected."""
        queue = self._queues.get(user_id)
        if queue:
            await queue.put(data)

    async def broadcast(self, user_ids: list[int], data: dict) -> None:
        """Send a notification to multiple users."""
        for user_id in user_ids:
            await self.send(user_id, data)

    def is_connected(self, user_id: int) -> bool:
        return user_id in self._queues


# Singleton instance shared across the application
notification_manager = NotificationManager()
