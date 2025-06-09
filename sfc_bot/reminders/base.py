from __future__ import annotations

import asyncio
from abc import abstractmethod
from datetime import datetime, timedelta, time
from typing import Tuple

from discord.ext import commands

class ScheduledReminderCog(commands.Cog):
    """Base class for reminders that run at a scheduled time each day."""

    #: Time to trigger the reminder each day as (hour, minute).
    SCHEDULE_TIME: Tuple[int, int] = (0, 1)

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._task = self.bot.loop.create_task(self._schedule_loop())

    async def cog_unload(self) -> None:
        self._task.cancel()

    async def _schedule_loop(self) -> None:
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now()
            target = datetime.combine(now.date(), time(*self.SCHEDULE_TIME))
            if target <= now:
                target += timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())
            await self.send_due_reminders()

    @abstractmethod
    async def send_due_reminders(self) -> None:
        """Send reminders that are due."""
        raise NotImplementedError
