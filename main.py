import os
from discord.ext import commands
import discord

bot = commands.Bot(command_prefix=".",case_insensitive=True,intents=discord.Intents.all())
token = " " #add your bot token

@bot.event
async def on_ready():
  for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
      try:
        await bot.load_extension(f'cogs.{filename[:-3]}')
        print(f"Loaded {filename}")
      except Exception as e:
        print(e)
        pass

bot.run(token)
