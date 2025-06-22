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
    
WHITELIST_FILE = "whitelist.json"
MAPPING_FILE = "mapping.json"

def load_whitelist():
    if not os.path.isfile(WHITELIST_FILE):
        return []
    with open(WHITELIST_FILE, "r") as f:
        return json.load(f)

def save_whitelist(data):
    with open(WHITELIST_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_mapping():
    if not os.path.isfile(MAPPING_FILE):
        return {}
    with open(MAPPING_FILE, "r") as f:
        return json.load(f)

def save_mapping(data):
    with open(MAPPING_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
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

@bot.tree.command(name="whitelist", description="Add a user ID to the whitelist")
@has_required_permissions()
@app_commands.describe(userid="Roblox user ID to whitelist")
async def whitelist(interaction: discord.Interaction, userid: int):
    try:
        discord_id = str(interaction.user.id)
        mapping = load_mapping()
        if discord_id in mapping:
            await interaction.response.send_message(
                "❌ You already whitelisted a Roblox user. Use /replacewhitelist to change it.", ephemeral=True
            )
            return

        user_info = requests.get(f"https://users.roblox.com/v1/users/{userid}")
        if user_info.status_code != 200:
            await interaction.response.send_message(f"❌ User ID `{userid}` does not exist on Roblox.", ephemeral=True)
            return
        user_data = user_info.json()
        username = user_data.get("name", "Unknown")
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={userid}&width=420&height=420&format=png"

        whitelist = load_whitelist()
        if userid in whitelist:
            embed = discord.Embed(
                title="ℹ️ Already Whitelisted",
                description=f"**{username}** (`{userid}`) is already in the whitelist.",
                color=0xFFFF00
            )
            embed.set_image(url=avatar_url)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        whitelist.append(userid)
        save_whitelist(whitelist)

        mapping[discord_id] = userid
        save_mapping(mapping)

        embed = discord.Embed(
            title="✅ Whitelisted",
            description=f"**{username}** (`{userid}`) has been added to the whitelist.",
            color=0x00FF00
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="replacewhitelist", description="Replace your whitelisted user ID with a new one")
@has_required_permissions()
@app_commands.describe(new_userid="The new Roblox user ID to whitelist")
async def replacewhitelist(interaction: discord.Interaction, new_userid: int):
    try:
        discord_id = str(interaction.user.id)
        mapping = load_mapping()
        if discord_id not in mapping:
            await interaction.response.send_message("❌ You have no whitelisted user to replace. Use /whitelist first.", ephemeral=True)
            return

        old_userid = mapping[discord_id]

        user_info = requests.get(f"https://users.roblox.com/v1/users/{new_userid}")
        if user_info.status_code != 200:
            await interaction.response.send_message(f"❌ New user ID `{new_userid}` does not exist on Roblox.", ephemeral=True)
            return
        user_data = user_info.json()
        username = user_data.get("name", "Unknown")
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={new_userid}&width=420&height=420&format=png"

        whitelist = load_whitelist()

        if old_userid not in whitelist:
            await interaction.response.send_message("❌ Your old user ID is not in the whitelist anymore.", ephemeral=True)
            return

        index = whitelist.index(old_userid)
        if new_userid not in whitelist:
            whitelist[index] = new_userid
        else:
            whitelist.pop(index)

        save_whitelist(whitelist)

        mapping[discord_id] = new_userid
        save_mapping(mapping)

        embed = discord.Embed(
            title="✅ Whitelist Updated",
            description=f"Replaced your Roblox ID with **{username}** (`{new_userid}`).",
            color=0x00FF00
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="check", description="Check which Roblox user ID you have whitelisted")
async def check(interaction: discord.Interaction):
    try:
        discord_id = str(interaction.user.id)
        mapping = load_mapping()
        if discord_id not in mapping:
            await interaction.response.send_message("❌ You have not whitelisted any Roblox user.", ephemeral=True)
            return

        userid = mapping[discord_id]

        user_info = requests.get(f"https://users.roblox.com/v1/users/{userid}")
        if user_info.status_code != 200:
            await interaction.response.send_message("❌ Your whitelisted Roblox user ID does not exist anymore.", ephemeral=True)
            return
        user_data = user_info.json()
        username = user_data.get("name", "Unknown")
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={userid}&width=420&height=420&format=png"

        embed = discord.Embed(
            title="Your Whitelisted acc",
            description=f"**{username}** (`{userid}`)",
            color=0x00FF00
        )
        embed.set_image(url=avatar_url)
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

bot.run(token)
