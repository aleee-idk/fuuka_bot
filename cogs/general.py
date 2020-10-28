from discord.ext import commands, tasks
from discord import Embed, colour, Game
from dotenv import load_dotenv
import asyncio
import os


class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        load_dotenv()

        self.audioChannel = int(os.getenv('Radio_Channel'))

        self.channels = {
            'general': 619505830730924037,
            'currentPlaying': 738491810283782166,
            'programacion': 738817109475459193,
            'audio': 739248670792351748
        }

        self.server = 619505830730924032

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} Has Connected to Discord!')
        await self.bot.change_presence(activity=Game(name='Providing Suport!'))

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        print(args[0])

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        # Mutear usuarios en canal de radio
        if after.channel.id == self.audioChannel:
            if member != self.bot.user:
                await member.edit(mute=True)

        # Desmutear Usuarios si no es el canal de radio
        elif after.channel.id != self.audioChannel:
            await member.edit(mute=False)

        # # Avandonar canal de voz si no hay nadie
        # if len(after.channel.members) == 1:
        #     await asyncio.sleep(60)
        #     if len(after.channel.members) == 1: await after.channel.disconnect()

    @commands.command()
    async def help(self, ctx):
        '''
        Mostrar esta ayuda
        `!help`
        '''
        cogs = {}
        for command in self.bot.commands:
            if command.cog_name not in cogs:
                cogs[command.cog_name] = []
            cogs[command.cog_name].append(command)

        for cog in cogs:
            cogs[cog].sort(key=lambda command: command.name)
            embed = Embed(
                colour=int("c8dde0", 16)
            )
            embed.set_author(name=cog)

            for item in cogs[cog]:
                embed.add_field(name=f'{item}:',
                                value=f'-{item.help}', inline=False)
            await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        '''
        Revisar latencia de Fuuka
        `!ping`
        '''
        response = f'Pong! {round(self.bot.latency) * 1000} ms'
        await ctx.send(response)

    @commands.command()
    async def clear(self, ctx):
        '''
        Limpiar mensajes en el canal invocado (actualmente elimina 100 mensajes fijo)
        `!clear`
        '''
        await ctx.channel.purge()

    @commands.command()
    async def loadcog(self, ctx, extension):
        '''
        Cargar una extensión cog (motivos de desarrollo)
        `!loadcog`
        '''
        self.bot.load_extension(f'cogs.{extension}')

    @commands.command()
    async def unloadcog(self, ctx, extension):
        '''
        Eliminar una extensión cog (motivos de desarrollo)
        `!unloadcog`
        '''
        self.bot.unload_extension(f'cogs.{extension}')

    @commands.command()
    async def reloadcog(self, ctx, extension):
        '''
        Recargar una extensión cog (motivos de desarrollo)
        `!reloadcog`
        '''
        self.bot.unload_extension(f'cogs.{extension}')
        self.bot.load_extension(f'cogs.{extension}')

    @reloadcog.error
    async def reload_cog_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')

    @loadcog.error
    async def load_cog_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')

    @unloadcog.error
    async def unload_cog_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')


def setup(bot):
    bot.add_cog(General(bot))
