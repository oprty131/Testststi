import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class SayButtonView(discord.ui.View):
    def __init__(self, message):
        super().__init__()
        self.message = message

    @discord.ui.button(label="raid keep pressing the button", style=discord.ButtonStyle.primary)
    async def say_custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.message, ephemeral=False)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is online as {bot.user}")

@bot.tree.command(name="raidbutton", description="click here to keep sending the message")
@app_commands.describe(message="The message to send when you click the button")
async def say_command(interaction: discord.Interaction, message: str):
    await interaction.response.send_message("Click the button to send it:", view=SayButtonView(message), ephemeral=True)

token = os.getenv("TOKEN")
if not token:
    raise ValueError("TOKEN not set in environment.")
bot.run(token)
