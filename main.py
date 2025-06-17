from keep_alive import keep_alive
import discord
import os

# Initialize the keep-alive web server
keep_alive()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Required to read messages in new Discord API

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "ping":
        await message.channel.send("Pong!")

# Run the bot using your token from Replit Secrets
client.run(os.environ["TOKEN"])
