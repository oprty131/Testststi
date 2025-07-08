import discord
import os
import requests
import aiohttp
import asyncio
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
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="The message to repeat", count="How many times to send the message (max 5)")
async def koko_command(interaction: discord.Interaction, text: str, count: int):
    if count > 5:
        await interaction.response.send_message("Count max is 5.", ephemeral=True)
        return
    await interaction.response.send_message("https://discord.gg/64wwVMagmY", ephemeral=True)
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
    view = KokoButtonView(message, count)
    await interaction.response.send_message(f"Click the button to send the message {count} times.", view=view, ephemeral=True)

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(text="The message to be shown after")
async def say_command(interaction: discord.Interaction, text: str):
    await interaction.response.send_message("https://discord.gg/64wwVMagmY", ephemeral=True)
    await interaction.followup.send(text)
    
@bot.tree.command(name="saybutton", description="Send a custom message with a button")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(message="The message to send when the button is pressed")
async def raidbutton_command(interaction: discord.Interaction, message: str):
    view = CustomMessageButtonView(message)
    await interaction.response.send_message("Click the button to send your message.", view=view, ephemeral=True)
    
@bot.tree.command(name="snipe", description="Find a user in public Roblox servers")
@app_commands.describe(username="The username or display name of the target player", placeid="The PlaceId of the game")
async def snipe(interaction: discord.Interaction, username: str, placeid: int):
    await interaction.response.defer()

    async def get_user_id(name):
        url = f"https://api.roblox.com/users/get-by-username?username={name}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data.get("Id")

    async def get_avatar(user_id):
        url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=48x48&format=Png&isCircular=false"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                return data["data"][0]["imageUrl"]

    async def get_server_avatars(tokens):
        payload = [{
            "token": token,
            "type": "AvatarHeadShot",
            "size": "48x48",
            "isCircular": False
        } for token in tokens]

        url = "https://thumbnails.roblox.com/v1/batch"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                return [d["imageUrl"] for d in data["data"]]

    user_id = await get_user_id(username)
    if not user_id:
        await interaction.followup.send(f"❌ Could not find Roblox user `{username}`")
        return

    avatar_url = await get_avatar(user_id)
    await interaction.followup.send(f"🔍 Searching for `{username}` in game `{placeid}`...", ephemeral=True)

    page = 1
    cursor = ""
    found = False

    while not found:
        url = f"https://games.roblox.com/v1/games/{placeid}/servers/Public?sortOrder=Asc&limit=100"
        if cursor:
            url += f"&cursor={cursor}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

                for server in data["data"]:
                    if "playerTokens" not in server:
                        continue

                    server_avatars = await get_server_avatars(server["playerTokens"])
                    if avatar_url in server_avatars:
                        join_link = f"https://www.roblox.com/games/{placeid}?privateServerLinkCode=&gameInstanceId={server['id']}"
                        await interaction.followup.send(f"🎯 **Found `{username}`!** Join here: {join_link}")
                        found = True
                        return

                cursor = data.get("nextPageCursor", "")
                if not cursor:
                    break
                page += 1
                await asyncio.sleep(1)

    await interaction.followup.send("⚠️ Could not find the user in public servers.")
        
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
