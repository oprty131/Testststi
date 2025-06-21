import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from a .env file

TOKEN = os.getenv('BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Needed to read message content

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == 'ping':
        await message.channel.send('pong')

    await bot.process_commands(message)  # Allows commands to work if you add any later

bot.run(TOKEN)
