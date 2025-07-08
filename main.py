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
    
def get_user_id(username):
    if username.isdigit():
        return int(username)
    url = "https://users.roblox.com/v1/usernames/users"
    response = requests.post(url, json={"usernames": [username]})
    data = response.json()
    if data['data']:
        return data['data'][0]['id']
    return None

def get_avatar_url(user_id):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=48x48&format=Png&isCircular=false"
    response = requests.get(url)
    data = response.json()
    if data['data']:
        return data['data'][0]['imageUrl']
    return None

def get_avatars_by_tokens(tokens):
    url = "https://thumbnails.roblox.com/v1/batch"
    payload = [{
        "token": token,
        "type": "AvatarHeadShot",
        "size": "48x48",
        "isCircular": False
    } for token in tokens]
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return [item['imageUrl'] for item in data['data']]

def scan_servers(place_id, target_avatar_url, min_players):
    cursor = ""
    while True:
        url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Asc&limit=100"
        if cursor:
            url += f"&cursor={cursor}"
        response = requests.get(url)
        if response.status_code != 200:
            break
        data = response.json()
        for server in data['data']:
            if server['playing'] < min_players:
                continue
            tokens = server.get('playerTokens', [])
            if not tokens:
                continue
            avatars = get_avatars_by_tokens(tokens)
            if target_avatar_url in avatars:
                return server
        cursor = data.get('nextPageCursor')
        if not cursor:
            break
    return None
    
@bot.tree.command(name="snipe", description="Scan Roblox servers to find the user")
@app_commands.describe(username="Target Roblox username", place_id="Roblox place ID", min_players="Minimum players in the server")
async def snipe_command(interaction: discord.Interaction, username: str, place_id: str, min_players: int = 1):
    await interaction.response.defer(thinking=True)

    user_id = get_user_id(username)
    if not user_id:
        await interaction.followup.send(f"❌ Could not find user `{username}`.")
        return

    avatar_url = get_avatar_url(user_id)
    if not avatar_url:
        await interaction.followup.send(f"❌ Could not get avatar for `{username}`.")
        return

    server = scan_servers(place_id, avatar_url, min_players)
    if server:
        join_link = f"https://peeky.pythonanywhere.com/join?placeId={place_id}&gameInstanceId={server['id']}"
        await interaction.followup.send(
            f"✅ **Player found!**\n"
            f"👥 Players: `{server['playing']}`\n"
            f"🔗 [Join Server]({join_link})"
        )
    else:
        await interaction.followup.send("❌ Player not found in any public server.")
        
token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in .env.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()
bot.run(token)
