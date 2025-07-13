import os
import discord
import aiohttp
import imgkit
import threading
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, render_template, request, send_file
from discord.ext import commands
from discord import app_commands

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

PEEKY_ID = 1265687947630481552
GAY_USER_ID = 1391486635962798242

gay_mode_enabled = False
gay_mode_text = " i'm gay"

def gaymode(user_id: int, message: str) -> str:
    if user_id == GAY_USER_ID and gay_mode_enabled:
        return message + gay_mode_text
    return message

class CustomMessageButtonView(discord.ui.View):
    def __init__(self, message: str, user_id: int):
        super().__init__(timeout=None)
        self.message = gaymode(user_id, message)

    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.primary)
    async def send_custom_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.message, ephemeral=False)

class KokoButtonView(discord.ui.View):
    def __init__(self, message: str, count: int, user_id: int):
        super().__init__(timeout=None)
        self.message = gaymode(user_id, message)
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

@bot.tree.command(name="gaymode", description="Toggle gay mode and optionally customize the text")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(status="on or off", text="Optional custom message (only works when turning ON)")
async def gaymode_command(interaction: discord.Interaction, status: str, text: str = None):
    global gay_mode_enabled, gay_mode_text

    if interaction.user.id != PEEKY_ID:
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    status = status.lower()
    if status not in ["on", "off"]:
        await interaction.response.send_message("Please choose either 'on' or 'off'.", ephemeral=True)
        return

    if status == "on":
        gay_mode_enabled = True
        if text:
            gay_mode_text = " " + text
        await interaction.response.send_message(f"Gay mode enabled with text: `{gay_mode_text.strip()}`", ephemeral=True)
    else:
        gay_mode_enabled = False
        await interaction.response.send_message("Gay mode has been turned **off**.", ephemeral=True)

@bot.tree.command(name="flood", description="Send a message repeatedly")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="The message to repeat", count="How many times to send the message (max 5)")
async def koko_command(interaction: discord.Interaction, text: str, count: int):
    if count > 5:
        await interaction.response.send_message("Count max is 5.", ephemeral=True)
        return
    await interaction.response.send_message("https://discord.gg/64wwVMagmY", ephemeral=True)
    text = gaymode(interaction.user.id, text)
    for _ in range(count):
        await interaction.followup.send(text)

@bot.tree.command(name="floodbutton", description="Send a message multiple times using a button")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(message="The message to send", count="How many times to send it (max 5)")
async def kokobutton_command(interaction: discord.Interaction, message: str, count: int):
    if count > 5:
        await interaction.response.send_message("Count max is 5.", ephemeral=True)
        return
    view = KokoButtonView(message, count, interaction.user.id)
    await interaction.response.send_message(f"Click the button to send the message {count} times.", view=view, ephemeral=True)

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="The message to be shown after")
async def say_command(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("https://discord.gg/64wwVMagmY", ephemeral=True)
    text = gaymode(interaction.user.id, text)
    await interaction.followup.send(text)

@bot.tree.command(name="saybutton", description="Send a custom message with a button")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(message="The message to send when the button is pressed")
async def raidbutton_command(interaction: discord.Interaction, message: str):
    view = CustomMessageButtonView(message, interaction.user.id)
    await interaction.response.send_message("Click the button to send your message.", view=view, ephemeral=True)

@bot.tree.command(name="petpet", description="PetPet someone")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(user="The user to pat")
async def petpet_command(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message("🔄 Generating image...", ephemeral=True)

    avatar_url = user.display_avatar.with_format("png").with_size(256).url
    api_url = f"https://api.obamabot.me/v2/image/petpet?image={avatar_url}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as resp:
            if resp.status != 200:
                await interaction.followup.send("❌ Failed to generate petpet image.", ephemeral=True)
                return

            data = await resp.json()
            if data.get("error") or "url" not in data:
                await interaction.followup.send("❌ Error in response from API.", ephemeral=True)
                return

            await interaction.followup.send(data["url"])

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
