from flask import Flask
from threading import Thread
import discord
import os

# --- Flask App for Keeping Alive ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Start Flask server in background thread
Thread(target=run_flask).start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # Important for reading messages
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "ping":
        await message.channel.send("Pong!")

# --- Run the Bot ---
client.run(os.environ["TOKEN"])
