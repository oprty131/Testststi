import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class HiButtonView(discord.ui.View):
    @discord.ui.button(label="Say hi too", style=discord.ButtonStyle.primary)
    async def say_hi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("hi too", ephemeral=False)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    print(f"🤖 Bot is online as {bot.user}")

@bot.tree.command(name="hi", description="Say hi")
async def hi_command(interaction: discord.Interaction):
    await interaction.response.send_message("Hey there! 👋 Click the button:", view=HiButtonView())

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN is not set in the environment.")

bot.run(TOKEN)
