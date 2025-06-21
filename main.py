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
        await interaction.response.send_message("hi too", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online as {bot.user}")

@bot.tree.command(name="hi", description="Say hi")
async def hi_command(interaction: discord.Interaction):
    await interaction.response.send_message("Hey there! 👋 Click the button:", view=HiButtonView(), ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")
bot.run(token)
