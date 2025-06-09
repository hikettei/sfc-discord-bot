from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict

import discord
from discord.ext import commands

from .base import ScheduledReminderCog

BIRTHDAY_FILE = Path("birthdays.csv")
# Time of day when birthday checks run (hour, minute). Useful for tests.
CHECK_TIME = (0, 1)

class BirthdayReminder(ScheduledReminderCog):
    """Cog handling birthday reminders."""

    SCHEDULE_TIME = CHECK_TIME

    def __init__(self, bot: commands.Bot) -> None:
        self.birthdays: Dict[str, str] = {}
        super().__init__(bot)
        self._load_birthdays()

    def _load_birthdays(self) -> None:
        if BIRTHDAY_FILE.exists():
            with BIRTHDAY_FILE.open(newline="") as f:
                reader = csv.reader(f)
                self.birthdays = {uid: date for uid, date in reader}

    def _save_birthdays(self) -> None:
        with BIRTHDAY_FILE.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.birthdays.items())

    @commands.group(name="birthday", invoke_without_command=True)
    async def birthday_group(self, ctx: commands.Context) -> None:
        """Manage birthday reminders."""
        await ctx.send(
            "Use '!birthday set MM-DD' to register your birthday, "
            "'!birthday today' to see today's birthdays, or "
            "'!birthday list' to list birthdays."
        )

    @birthday_group.command(name="set")
    async def birthday_set(self, ctx: commands.Context, date: str) -> None:
        """Register your birthday in MM-DD format."""
        try:
            datetime.strptime(date, "%m-%d")
        except ValueError:
            await ctx.send("Date must be in MM-DD format.")
            return
        self.birthdays[str(ctx.author.id)] = date
        self._save_birthdays()
        await ctx.send(f"Birthday for {ctx.author.display_name} set to {date}.")

    @birthday_group.command(name="today")
    async def birthday_today(self, ctx: commands.Context) -> None:
        """Show birthdays happening today."""
        await self._announce_birthdays(ctx.channel)

    @birthday_group.command(name="list")
    async def birthday_list(self, ctx: commands.Context) -> None:
        """List all registered birthdays."""
        if not self.birthdays:
            await ctx.send("No birthdays registered.")
            return
        entries = []
        for uid, date in sorted(self.birthdays.items(), key=lambda x: x[1]):
            user = await self.bot.fetch_user(int(uid))
            entries.append(f"{date}: {user.display_name}")
        await ctx.send("\n".join(entries))

    async def send_due_reminders(self) -> None:
        today = datetime.now().strftime("%m-%d")
        if not self.birthdays:
            return
        mentions = [
            (await self.bot.fetch_user(int(uid))).mention
            for uid, date in self.birthdays.items()
            if date == today
        ]
        if not mentions:
            return
        message = "Today's birthdays: " + ", ".join(mentions)
        for guild in self.bot.guilds:
            channel = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None,
            )
            if channel:
                await channel.send(message)

    async def _announce_birthdays(self, channel: discord.abc.Messageable) -> None:
        today = datetime.now().strftime("%m-%d")
        mentions = [
            (await self.bot.fetch_user(int(uid))).mention
            for uid, date in self.birthdays.items()
            if date == today
        ]
        if mentions:
            await channel.send("Today's birthdays: " + ", ".join(mentions))
        else:
            await channel.send("No birthdays today.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BirthdayReminder(bot))
