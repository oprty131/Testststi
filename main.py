import discord
import os
import requests
import datetime
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

@bot.tree.command(name="raidbutton", description="Send a custom message with a button")
@app_commands.describe(message="The message to send when the button is pressed")
async def say_command(interaction: discord.Interaction, message: str):
    view = CustomMessageButtonView(message)
    await interaction.response.send_message(f"Click the button to send your message.", view=view, ephemeral=True)

@bot.tree.command(name="showwhitelist", description="Send raw whitelist table as a file")
async def showwhitelist(interaction: discord.Interaction):
    try:
        response = requests.get("https://peeky.pythonanywhere.com/edit/UserIdTestTable")
        content = response.text.strip().encode("utf-8")
        file = discord.File(fp=discord.BytesIO(content), filename="UserIdTestTable.lua")
        await interaction.response.send_message("📄 Here's the whitelist file:", file=file, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

bot.run(token)
