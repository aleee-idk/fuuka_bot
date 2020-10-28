from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

Bot_Token = os.getenv('Bot_Token')

for file in os.listdir('./cogs'):
    if file.endswith('.py') and file != 'credentials.py':
        bot.load_extension(f'cogs.{file[:-3]}')

bot.run(Bot_Token)
