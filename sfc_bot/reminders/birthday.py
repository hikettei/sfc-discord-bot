from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import io
import random
import calendar

import discord
from discord.ext import commands
import cv2
import numpy as np
from PIL import Image, ImageDraw

from .base import ScheduledReminderCog

BIRTHDAY_FILE = Path("birthdays.csv")
NOTIFICATION_FILE = Path("notification_channels.csv")

class BirthdayReminder(ScheduledReminderCog):
    """Cog handling birthday reminders."""
    def __init__(self, bot: commands.Bot) -> None:
        self.birthdays: Dict[str, str] = {}
        self.notification_channels: Dict[str, str] = {}
        super().__init__(bot)
        self._load_birthdays()
        self._load_notifications()

    def _load_birthdays(self) -> None:
        if BIRTHDAY_FILE.exists():
            with BIRTHDAY_FILE.open(newline="") as f:
                reader = csv.reader(f)
                self.birthdays = {uid: date for uid, date in reader}

    def _save_birthdays(self) -> None:
        with BIRTHDAY_FILE.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.birthdays.items())

    def _load_notifications(self) -> None:
        if NOTIFICATION_FILE.exists():
            with NOTIFICATION_FILE.open(newline="") as f:
                reader = csv.reader(f)
                self.notification_channels = {gid: cid for gid, cid in reader}

    def _save_notifications(self) -> None:
        with NOTIFICATION_FILE.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.notification_channels.items())

    @commands.command(name="notification")
    @commands.has_guild_permissions(administrator=True)
    async def set_notification(self, ctx: commands.Context, channel_id: str) -> None:
        """Set the channel to use for reminders."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
        try:
            int(channel_id)
        except ValueError:
            await ctx.send("Invalid channel ID.")
            return
        self.notification_channels[str(ctx.guild.id)] = channel_id
        self._save_notifications()
        await ctx.send(f"Notification channel set to <#{channel_id}>.")

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
        """Reply with a calendar image of all birthdays."""
        if not self.birthdays:
            await ctx.send("No birthdays registered.")
            return
        file = await self._create_calendar_image()
        await ctx.send(file=file)

    async def _create_calendar_image(self) -> discord.File:
        """Create a calendar image with avatars on birthdays."""
        year = datetime.now().year
        month = datetime.now().month
        cal = calendar.monthcalendar(year, month)
        cell_w, cell_h = 100, 80
        img_h = cell_h * (len(cal) + 1)
        img_w = cell_w * 7
        img = np.ones((img_h, img_w, 3), dtype=np.uint8) * 255
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, f"{year}-{month:02d}", (5, 20), font, 0.6, (0, 0, 0), 2)
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                x, y = c * cell_w, (r + 1) * cell_h
                cv2.rectangle(img, (x, y), (x + cell_w, y + cell_h), (0, 0, 0), 1)
                if day:
                    cv2.putText(img, str(day), (x + 2, y + 15), font, 0.5, (0, 0, 0), 1)
                    key = f"{month:02d}-{day:02d}"
                    uids = [uid for uid, d in self.birthdays.items() if d == key]
                    offset = 0
                    for uid in uids:
                        user = await self.bot.fetch_user(int(uid))
                        data = await user.display_avatar.read()
                        avatar = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
                        if avatar is None:
                            continue
                        avatar = cv2.resize(avatar, (32, 32))
                        if avatar.shape[2] == 4:
                            alpha = avatar[:, :, 3] / 255.0
                            for cidx in range(3):
                                img[y + 20 + offset : y + 52 + offset, x + 2 : x + 34, cidx] = (
                                    alpha * avatar[:, :, cidx]
                                    + (1 - alpha)
                                    * img[y + 20 + offset : y + 52 + offset, x + 2 : x + 34, cidx]
                                )
                        else:
                            img[y + 20 + offset : y + 52 + offset, x + 2 : x + 34] = avatar
                        offset += 34
        buf = io.BytesIO()
        _, arr = cv2.imencode(".png", img)
        buf.write(arr.tobytes())
        buf.seek(0)
        return discord.File(fp=buf, filename="birthdays.png")

    async def send_due_reminders(self) -> None:
        today = datetime.now().strftime("%m-%d")
        if not self.birthdays:
            return
        for guild in self.bot.guilds:
            members = [m for m in guild.members if self.birthdays.get(str(m.id)) == today]
            if not members:
                continue
            channel = self._get_notification_channel(guild)
            if not channel:
                continue
            mentions = [m.mention for m in members]
            message = random.choice(["🎂", "🍰", "🥳", "🎉"]) + " " + ", ".join(mentions)
            card = await self._create_birthday_card(members)
            await channel.send(message, file=card)

    def _get_notification_channel(self, guild: discord.Guild) -> discord.abc.Messageable | None:
        channel_id = self.notification_channels.get(str(guild.id))
        channel = None
        if channel_id:
            channel = guild.get_channel(int(channel_id))
        if channel is None:
            channel = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None,
            )
        return channel

    async def _create_birthday_card(self, members: List[discord.Member]) -> discord.File:
        width = 200 + 80 * len(members)
        height = 180
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        emoji = random.choice(["🎂", "🍰", "🥳", "🎉"])
        draw.text((10, 10), f"Happy Birthday {emoji}", fill="black")
        x = 10
        for m in members:
            data = await m.display_avatar.read()
            avatar = Image.open(io.BytesIO(data)).convert("RGBA").resize((64, 64))
            img.paste(avatar, (x, 40), avatar)
            draw.text((x, 110), m.display_name, fill="black")
            x += 80
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return discord.File(fp=buf, filename="card.png")

    async def _announce_birthdays(self, channel: discord.abc.Messageable) -> None:
        today = datetime.now().strftime("%m-%d")
        guild = getattr(channel, "guild", None)
        if guild:
            members = [m for m in guild.members if self.birthdays.get(str(m.id)) == today]
        else:
            members = [await self.bot.fetch_user(int(uid)) for uid, d in self.birthdays.items() if d == today]
        if members:
            mentions = [m.mention for m in members]
            card = await self._create_birthday_card(members)
            await channel.send("Today's birthdays: " + ", ".join(mentions), file=card)
        else:
            await channel.send("No birthdays today.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BirthdayReminder(bot))
