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

@bot.tree.command(name="whitelist", description="Add a user ID to the whitelist")
@app_commands.describe(userid="Roblox user ID to whitelist")
async def whitelist(interaction: discord.Interaction, userid: int):
    try:
        user_info = requests.get(f"https://users.roblox.com/v1/users/{userid}")
        if user_info.status_code != 200:
            await interaction.response.send_message(f"❌ User ID `{userid}` does not exist on Roblox.", ephemeral=True)
            return
        user_data = user_info.json()
        username = user_data.get("name", "Unknown")
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={userid}&width=420&height=420&format=png"
        response = requests.get("https://peeky.pythonanywhere.com/UserIdTestTable")
        table_code = response.text.strip()
        start = table_code.find("{") + 1
        end = table_code.find("}")
        current_ids = [int(i.strip()) for i in table_code[start:end].split(",") if i.strip().isdigit()]
        if userid in current_ids:
            embed = discord.Embed(
                title="ℹ️ Already Whitelisted",
                description=f"**{username}** (`{userid}`) is already in the whitelist.",
                color=0xFFFF00
            )
            embed.set_thumbnail(url=avatar_url)
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        current_ids.append(userid)
        new_table = "return {\n    " + ",\n    ".join(map(str, current_ids)) + "\n}"
        post_response = requests.post(
            "https://peeky.pythonanywhere.com/edit/UserIdTestTable",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"content": new_table}
        )
        if post_response.status_code == 200:
            embed = discord.Embed(
                title="✅ Whitelisted",
                description=f"**{username}** (`{userid}`) has been added to the whitelist.",
                color=0x00FF00
            )
            embed.set_thumbnail(url=avatar_url)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(f"❌ Failed to update. Status {post_response.status_code}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        
@bot.tree.command(name="replacewhitelist", description="Replace an old user ID in the whitelist with a new one")
@app_commands.describe(old_userid="The user ID to replace", new_userid="The new user ID to insert")
async def replacewhitelist(interaction: discord.Interaction, old_userid: int, new_userid: int):
    try:
        user_info = requests.get(f"https://users.roblox.com/v1/users/{new_userid}")
        if user_info.status_code != 200:
            await interaction.response.send_message(f"❌ New user ID `{new_userid}` does not exist on Roblox.", ephemeral=True)
            return
        user_data = user_info.json()
        username = user_data.get("name", "Unknown")
        avatar_url = f"https://www.roblox.com/headshot-thumbnail/image?userId={new_userid}&width=420&height=420&format=png"

        response = requests.get("https://peeky.pythonanywhere.com/UserIdTestTable")
        table_code = response.text.strip()
        start = table_code.find("{") + 1
        end = table_code.find("}")
        current_ids = [int(i.strip()) for i in table_code[start:end].split(",") if i.strip().isdigit()]

        if old_userid not in current_ids:
            await interaction.response.send_message(f"❌ Old user ID `{old_userid}` is not in the whitelist.", ephemeral=True)
            return

        current_ids = [i for i in current_ids if i != old_userid]
        if new_userid not in current_ids:
            current_ids.append(new_userid)

        new_table = "return {\n    " + ",\n    ".join(map(str, current_ids)) + "\n}"
        post_response = requests.post(
            "https://peeky.pythonanywhere.com/edit/UserIdTestTable",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"content": new_table}
        )

        if post_response.status_code == 200:
            embed = discord.Embed(
                title="🔁 Whitelist Updated",
                description=f"Replaced `{old_userid}` with **{username}** (`{new_userid}`) in the whitelist.",
                color=0x3498db
            )
            embed.set_image(url=avatar_url)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(f"❌ Failed to update. Status {post_response.status_code}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

bot.run(token)
