from __future__ import annotations

import os

from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    help_command=None,
    activity=discord.Game("<@mention> help"),
)


@bot.command(name="ping")
async def ping(ctx: commands.Context) -> None:
    """Respond with pong."""
    await ctx.send("Pong!")


@bot.command(name="help")
async def help_command(ctx: commands.Context) -> None:
    """Display help information."""
    help_text = (
        "!ping: Respond with 'Pong!'\n"
        "!help: Show this help message.\n"
        "!birthday set MM-DD: Set your birthday.\n"
        "!birthday today: Show birthdays today.\n"
        "!birthday list: List all registered birthdays."
    )
    await ctx.send(help_text)


async def main() -> None:
    await bot.load_extension("sfc_bot.reminders.birthday")
    await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
