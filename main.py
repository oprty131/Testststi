import discord
import os
import requests
import threading
from discord.ext import commands
from discord import app_commands
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
    app.run(host='0.0.0.0', port=8080)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class CustomMessageButtonView(discord.ui.View):
    def __init__(self, message: str):
        super().__init__(timeout=None)
        self.message = message

    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.primary)
    async def send_custom_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.message, ephemeral=False)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online as {bot.user}")

@bot.tree.command(name="flood", description="Send a message multiple times")
@app_commands.describe(text="The message to repeat", count="How many times to send the message")
async def koko_command(interaction: discord.Interaction, text: str, count: int):
    await interaction.response.send_message("Sending your message...", ephemeral=True)

    if count < 1:
        await interaction.followup.send("Count must be at least 1.")
        return
    elif count > 20:
        await interaction.followup.send("Limit is 20 messages max.")
        return

    for _ in range(count):
        await interaction.followup.send(text)

@bot.tree.command(name="send", description="Say something silently and then visibly reply")
@app_commands.describe(text="The message to be shown after")
async def say_command(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("https://discord.gg/7dV6X7v6sU", ephemeral=True)
    await interaction.followup.send(text)
    
@bot.tree.command(name="sendbutton", description="Send a custom message with a button")
@app_commands.describe(message="The message to send when the button is pressed")
async def sendbutton_command(interaction: discord.Interaction, message: str):
    view = CustomMessageButtonView(message)
    await interaction.response.send_message("Click the button to send your message.", view=view, ephemeral=True)
    
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
