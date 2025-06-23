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
    
class KokoButtonView(discord.ui.View):
    def __init__(self, message: str, count: int):
        super().__init__(timeout=None)
        self.message = message
        self.count = count

    @discord.ui.button(label="Send", style=discord.ButtonStyle.primary)
    async def send_multiple(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.count > 5:
            await interaction.response.send_message("Count max is 5.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        for _ in range(self.count):
            await interaction.followup.send(self.message)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online as {bot.user}")
    
@bot.tree.command(name="flood", description="Send a message repeatedly")
@app_commands.describe(text="The message to repeat", count="How many times to send the message (max 5)")
async def koko_command(interaction: discord.Interaction, text: str, count: int):
    if count > 5:
        await interaction.response.send_message("Count max is 5.", ephemeral=True)
        return
    await interaction.response.send_message("https://discord.gg/7dV6X7v6sU", ephemeral=True)
    for _ in range(count):
        await interaction.followup.send(text)
    
@bot.tree.command(name="floodbutton", description="Send a message multiple times using a button")
@app_commands.describe(message="The message to send", count="How many times to send it (max 5)")
async def kokobutton_command(interaction: discord.Interaction, message: str, count: int):
    if count > 5:
        await interaction.response.send_message("Count max is 5.", ephemeral=True)
        return
    view = KokoButtonView(message, count)
    await interaction.response.send_message(f"Click the button to send the message {count} times.", view=view, ephemeral=True)

@bot.tree.command(name="say", description="Say something silently and then visibly reply")
@app_commands.describe(text="The message to be shown after")
async def say_command(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("https://discord.gg/7dV6X7v6sU", ephemeral=True)
    await interaction.followup.send(text)
    
@bot.tree.command(name="saybutton", description="Send a custom message with a button")
@app_commands.describe(message="The message to send when the button is pressed")
async def raidbutton_command(interaction: discord.Interaction, message: str):
    view = CustomMessageButtonView(message)
    await interaction.response.send_message("Click the button to send your message.", view=view, ephemeral=True)
    
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
