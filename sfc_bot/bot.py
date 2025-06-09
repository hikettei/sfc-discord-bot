import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()

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
    help_text = "!ping: Respond with 'Pong!'\n!help: Show this help message."
    await ctx.send(help_text)

def main() -> None:
    bot.run(TOKEN)

if __name__ == "__main__":
    main()
