from __future__ import annotations

import asyncio
from abc import abstractmethod
from datetime import datetime, timedelta, timezone, time
from typing import Tuple

from discord.ext import tasks, commands

SCHEDULE_TIME = [time(hour=0, minute=1, tzinfo=timezone(timedelta(hours=+9), 'JST'))]

class ScheduledReminderCog(commands.Cog):
    """Base class for reminders that run at a scheduled time each day."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None: pass

    @tasks.loop(time=SCHEDULE_TIME)
    async def _on_ready(self) -> None:
        await self.bot.wait_until_ready()
        await self.send_due_reminders()

    @abstractmethod
    async def send_due_reminders(self) -> None:
        """Send reminders that are due."""
        raise NotImplementedError
