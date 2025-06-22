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

def fetch_table():
    r = requests.get("https://peeky.pythonanywhere.com/UserIdTestTable")
    return eval(r.text.replace("return", "").strip())

def update_table(user_ids):
    lua_data = "return {\n" + ",\n".join(f"    {uid}" for uid in user_ids) + "\n}"
    r = requests.post("https://peeky.pythonanywhere.com/edit/UserIdTestTable", data={"code": lua_data})
    return r.ok

@bot.tree.command(name="whitelist", description="Add a UserId to the premium whitelist")
@app_commands.describe(userid="The Roblox UserId to whitelist")
async def whitelist(interaction: discord.Interaction, userid: int):
    table = fetch_table()
    if userid in table:
        await interaction.response.send_message(f"✅ UserId `{userid}` is already whitelisted.", ephemeral=True)
        return
    table.append(userid)
    if update_table(table):
        embed = discord.Embed(
            title="✅ Whitelisted Roblox Account",
            description=f"Added new Roblox account to premium whitelist.",
            color=0x00ff00
        )
        embed.add_field(name="UserID", value=str(userid), inline=False)
        embed.set_footer(text="Powered by python blyat")
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Failed to update whitelist.", ephemeral=True)

@bot.tree.command(name="replace", description="Replace an old UserId with a new one")
@app_commands.describe(old_userid="Old Roblox UserId", new_userid="New Roblox UserId", old_username="Old username", new_username="New username")
async def replace(interaction: discord.Interaction, old_userid: int, new_userid: int, old_username: str, new_username: str):
    table = fetch_table()
    if old_userid not in table:
        await interaction.response.send_message(f"❌ Old UserId `{old_userid}` not found in whitelist.", ephemeral=True)
        return
    if new_userid in table:
        await interaction.response.send_message(f"✅ New UserId `{new_userid}` is already whitelisted.", ephemeral=True)
        return
    table.remove(old_userid)
    table.append(new_userid)
    if update_table(table):
        embed = discord.Embed(
            title=f"{datetime.datetime.utcnow().strftime('%B %d, %Y')}",
            description="Replaced your Roblox account at premium whitelist.",
            color=discord.Color.green()
        )
        embed.add_field(name="Old UserID", value=str(old_userid), inline=False)
        embed.add_field(name="Old Username", value=old_username, inline=False)
        embed.add_field(name="New UserID", value=str(new_userid), inline=False)
        embed.add_field(name="New Username", value=new_username, inline=False)
        embed.set_footer(text="Powered by python blyat")
        embed.set_thumbnail(url=f"https://tr.rbxcdn.com/ORIGINAL_THUMBNAIL/Avatar?userId={new_userid}&width=420&height=420&format=png")
        embed.timestamp = datetime.datetime.utcnow()
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("❌ Failed to replace UserId.", ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

bot.run(token)
