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
    await interaction.response.defer(thinking=True)
    
    # Shared state to allow cancel behavior
    if hasattr(bot, "snipe_task") and bot.snipe_task and not bot.snipe_task.done():
        if not hasattr(bot, "snipe_debounce") or not bot.snipe_debounce:
            bot.snipe_debounce = True
            await interaction.followup.send("⚠️ Click again within 3 seconds to cancel...", ephemeral=True)
            await asyncio.sleep(3)
            bot.snipe_debounce = False
        else:
            bot.snipe_task.cancel()
            await interaction.followup.send("❌ Scan cancelled.", ephemeral=True)
            return
        return
    
    async def get_user_id(name):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.roblox.com/users/get-by-username?username={name}") as resp:
                data = await resp.json()
                return data.get("Id")

    async def get_avatar(user_id):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=48x48&format=Png&isCircular=false"
            ) as resp:
                data = await resp.json()
                return data["data"][0]["imageUrl"]

    async def get_server_avatars(tokens):
        payload = [{
            "token": token,
            "type": "AvatarHeadShot",
            "size": "48x48",
            "isCircular": False
        } for token in tokens]
        async with aiohttp.ClientSession() as session:
            async with session.post("https://thumbnails.roblox.com/v1/batch", json=payload) as resp:
                data = await resp.json()
                return [d["imageUrl"] for d in data["data"]]

    async def run_scan():
        user_id = await get_user_id(username)
        if not user_id:
            await interaction.followup.send(f"❌ Could not find user `{username}`.", ephemeral=True)
            return

        await interaction.followup.send("📷 Loading avatar...", ephemeral=True)
        avatar_url = await get_avatar(user_id)

        page = 1
        found = False
        cursor = ""

        await interaction.followup.send("🛰️ Scanning servers...", ephemeral=True)

        try:
            while True:
                url = f"https://games.roblox.com/v1/games/{placeid}/servers/Public?sortOrder=Asc&limit=100"
                if cursor:
                    url += f"&cursor={cursor}"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()

                for i, server in enumerate(data["data"]):
                    await interaction.followup.send(f"🔎 Page {page} - Server {i+1}/{len(data['data'])} ({server['playing']} players)...", ephemeral=True)

                    if "playerTokens" not in server:
                        continue
                    avatars = await get_server_avatars(server["playerTokens"])
                    if avatar_url in avatars:
                        join_link = f"https://www.roblox.com/games/{placeid}?privateServerLinkCode=&gameInstanceId={server['id']}"
                        await interaction.followup.send(f"🎯 **Found `{username}`!** Join: {join_link}")
                        found = True
                        return

                if not data.get("nextPageCursor"):
                    break
                cursor = data["nextPageCursor"]
                page += 1
                await asyncio.sleep(1)

            if not found:
                await interaction.followup.send("⚠️ The player was not found in any public server.")
        except asyncio.CancelledError:
            await interaction.followup.send("❌ Scan cancelled early.")
        finally:
            bot.snipe_task = None
            bot.snipe_debounce = False

    bot.snipe_task = asyncio.create_task(run_scan())
        
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
