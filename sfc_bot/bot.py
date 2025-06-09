import os
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()

BIRTHDAY_FILE = Path("birthdays.json")

def load_birthdays() -> dict:
    if BIRTHDAY_FILE.exists():
        with BIRTHDAY_FILE.open() as f:
            return json.load(f)
    return {}

birthdays = load_birthdays()

def save_birthdays() -> None:
    with BIRTHDAY_FILE.open("w") as f:
        json.dump(birthdays, f)

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    help_command=None,
    activity=discord.Game("<@mention> help"))

@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """Respond with pong."""
    await ctx.send("Pong!")

@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """Display help information."""
    help_text = (
        "!ping: Respond with 'Pong!'\n"
        "!help: Show this help message.\n"
        "!birthday set MM-DD: Set your birthday.\n"
        "!birthday today: Show birthdays today.\n"
        "!birthday list: List all registered birthdays."
    )
    await ctx.send(help_text)


@bot.group(name="birthday", invoke_without_command=True)
async def birthday_group(ctx: commands.Context):
    """Manage birthday reminders."""
    await ctx.send(
        "Use '!birthday set MM-DD' to register your birthday, "
        "'!birthday today' to see today's birthdays, or "
        "'!birthday list' to list birthdays."
    )


@birthday_group.command(name="set")
async def birthday_set(ctx: commands.Context, date: str):
    """Register your birthday in MM-DD format."""
    try:
        datetime.strptime(date, "%m-%d")
    except ValueError:
        await ctx.send("Date must be in MM-DD format.")
        return
    birthdays[str(ctx.author.id)] = date
    save_birthdays()
    await ctx.send(f"Birthday for {ctx.author.display_name} set to {date}.")


@birthday_group.command(name="today")
async def birthday_today(ctx: commands.Context):
    """Show birthdays happening today."""
    today = datetime.now().strftime("%m-%d")
    mentions = [
        (await bot.fetch_user(int(uid))).mention
        for uid, date in birthdays.items()
        if date == today
    ]
    if mentions:
        await ctx.send("Today's birthdays: " + ", ".join(mentions))
    else:
        await ctx.send("No birthdays today.")


@birthday_group.command(name="list")
async def birthday_list(ctx: commands.Context):
    """List all registered birthdays."""
    if not birthdays:
        await ctx.send("No birthdays registered.")
        return
    entries = []
    for uid, date in sorted(birthdays.items(), key=lambda x: x[1]):
        user = await bot.fetch_user(int(uid))
        entries.append(f"{date}: {user.display_name}")
    await ctx.send("\n".join(entries))

def main() -> None:
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
