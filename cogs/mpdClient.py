'''
TODO 
[*] Hacer Comando shuffle que solo cargue la carpeta Random_Folder
[/] Establecer límite de playlist para mostrar en searchPlaylist y páginar las que no alcancen
[*] eliminar fixme de checkear largo de playlist para verificar si está reproduciendo una playlist
[-] establecer sistema de votación para controlar playback Solo si entra alguien más al server
[*] añadir imágenes con expresiones de fuuka y usarlas para las respuestas
[ ] añador lista de caritas acsii para usarlas en las respuestas
[ ] refraccionar loop de programación a comando con argumentos opcionales para hacer un loop de todos los días
o solo del día especificado
'''
from discord import FFmpegPCMAudio, Embed, colour, File
from discord.ext import commands, tasks
from mpd import MPDClient
from dotenv import load_dotenv
import json
import os
import re
import asyncio
import random
import lyricsgenius
import traceback


class Mpd(commands.Cog):

    def __init__(self, bot):

        load_dotenv()

        self.geniusToken = os.getenv('Genius_Token')
        self.Random_Playlist = os.getenv('Random_Playlist')
        self.MPD_Server = os.getenv('MPD_Server')
        self.MPD_Port = os.getenv('MPD_Port')
        self.MPD_URL = os.getenv('MPD_URL')
        self.Playlist_Path = os.getenv('Playlist_Path')
        self.Horario_Path = os.getenv('Horario_Path')
        self.Images = os.getenv('Images')
        self.Prog_Path = os.getenv('Prog_Path')

        self.bot = bot
        self.mpd = MPDClient()
        self.player = None
        self.voice = None
        self.genius = lyricsgenius.Genius(self.geniusToken)

        self.mpd.connect(self.MPD_Server, self.MPD_Port)
        self.random = self.mpd.listplaylist(self.Random_Playlist)
        self.mpd.disconnect()

        # self.channels = {
        # 'general': 619505830730924037,
        # 'currentPlaying': 738491810283782166,
        # 'programacion': 738817109475459193,
        # 'audio': 739248670792351748
        # }
#
        # self.send_current_song.start()

    @commands.command()
    async def play(self, ctx):
        '''Unirse al canal de voz actual del usuario
        `!play`
        '''
        self.voice = ctx.message.author.voice.channel
        if ctx.message.guild.voice_client != None:
            await ctx.message.guild.voice_client.move_to(self.voice)
        else:
            self.player = await self.voice.connect()
            self.player.play(FFmpegPCMAudio(
                self.MPD_URL), after=lambda e: self.message.start(ctx, self.voice))

    @commands.command(pass_context=True)
    async def leave(self, ctx):
        '''Salir de un canal de voz
        `!leave`
        '''
        channel = ctx.message.guild.voice_client
        await channel.disconnect()

    @commands.command()
    async def getsong(self, ctx, pos: int = 0):
        '''
        Obtener la canción actuál o en la posición indicada"
        `!getsong [-pos|+pos]`
        '''
        self.mpd.connect(self.MPD_Server, self.MPD_Port)
        currentPlaying = int(self.mpd.currentsong()['pos'])

        total = len(self.mpd.playlist()) - 1

        if currentPlaying + pos > total or currentPlaying + pos < 0:
            await ctx.send('Canción fuera de rango!')
            await ctx.send(f'Existen `{currentPlaying - 1}` Canciones antes que esta y `{total - currentPlaying}` despues!')
            self.mpd.disconnect()
            return

        song = self.mpd.playlistinfo(currentPlaying + pos)[-1]

        self.mpd.disconnect()

        embed = Embed(
            colour=int("c8dde0", 16)
        )
        embed.set_author(name='Cancion:')
        if 'title' in song:
            embed.add_field(name='Título', value=song['title'], inline=False)
        if 'album' in song:
            embed.add_field(name='Album', value=song['album'], inline=False)
        if 'artist' in song:
            embed.add_field(name='artista', value=song['artist'], inline=False)
        if 'composer' in song:
            embed.add_field(name='Compositor',
                            value=song['composer'], inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def search(self, ctx, *args):
        '''
        Buscar una canción en la base de datos y ponerla a continuación
        `!search busqueda`
        '''
        type = 'title'
        what = ' '.join(args)
        try:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            if len(self.mpd.playlist()) < 1000:
                self.mpd.disconnect()
                await ctx.send(f'Actualmente está sonando una playlist, no puedes agregar canciones hasta que termine')
                return
            lista = self.mpd.search(type, what)
            self.mpd.disconnect()
        except ConnectionError:
            await ctx.send(f'A ocurrido un problema de conexión con el servidor de música')
        finally:
            self.mpd.disconnect()
        embed = Embed(
            colour=int("c8dde0", 16)
        )

        embed.set_author(name='Esto es lo que encontré')

        for i, song in enumerate(lista, start=1):
            if 'title' in song and 'album' in song:
                embed.add_field(
                    name=f'{i}- {song["title"]}', value=song['album'], inline=False)
            else:
                s = re.split('/', song['file'])
                embed.add_field(
                    name=f'{i}- {s[-1]}', value=s[-2], inline=False)
        opciones = await ctx.send(embed=embed)

        i = await self.check_Answer(ctx, opciones, len(lista))

        if i != None:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            self.mpd.add(lista[i]['file'])
            total = len(self.mpd.playlist()) - 1
            self.mpd.move(total, -1)
            self.mpd.disconnect()
            msg = (lista[i]["title"] if 'title' in lista[i]
                   else re.split('/')[-1])
            await ctx.send(f'{msg} Fue añadida a continuación!')

    @search.error
    async def search_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')

    @commands.command()
    async def next(self, ctx):
        '''
        Reproducir siguiente canción
        `!next`
        '''
        try:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            self.mpd.next()
            self.mpd.disconnect()
        except ConnectionError:
            await ctx.send(f'A ocurrido un problema de conexión con el servidor de música')
        finally:
            self.mpd.disconnect()

    @commands.command()
    async def prev(self, ctx):
        '''
        Reproducir canción anterior
        `!prev`
        '''
        try:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            self.mpd.previous()
            self.mpd.disconnect()
        except ConnectionError:
            await ctx.send(f'A ocurrido un problema de conexión con el servidor de música')
        finally:
            self.mpd.disconnect()

    @commands.command()
    async def listplaylist(self, ctx):
        '''
        Listar las playlist disponibles y reproducir la seleccionada
        `!listplaylist`
        '''
        with open(self.Playlist_Path, 'r') as file:
            playlists = json.load(file)

        embed = Embed(
            color=int("c8dde0", 16)
        )
        embed.set_author(name='Selecciona una saga')
        aux = []
        for i, saga in enumerate(playlists, start=1):
            embed.add_field(
                name=f'{i}- {saga}', value=f'playlists: {len(playlists[saga])}', inline=False)
            aux.append(saga)
        opciones = await ctx.send(embed=embed)

        i = await self.check_Answer(ctx, opciones, len(aux))

        if i != None:
            saga = playlists[aux[i]]
            embed = Embed(
                color=int("c8dde0", 16)
            )
            embed.set_author(name='Selecciona una Playlist')
            for i, pl in enumerate(saga, start=1):
                embed.add_field(
                    name=f'{i}- {pl["Nombre"]}', value=f'{pl["Tipo"]}', inline=False)
            opciones = await ctx.send(embed=embed)

            i = await self.check_Answer(ctx, opciones, len(saga))

            if i != None:
                try:
                    self.mpd.connect(self.MPD_Server, self.MPD_Port)
                    s = int(self.mpd.currentsong()['pos'])
                    self.mpd.delete((s+1,))
                    self.mpd.delete((0, s))
                    self.mpd.load(saga[int(i)]['Playlist'])
                    total = len(self.mpd.playlist())
                    self.mpd.load(self.Random_Playlist)
                    self.mpd.shuffle((total,))
                    file = File(await self.get_images('happy'))
                    await ctx.send(f'{saga[int(i)]["Nombre"]} puesto en cola! c:', file=file)
                except ConnectionError:
                    file = File(await self.get_images('worried'))
                    await ctx.send(f'A ocurrido un problema de conexión con el servidor de música', file=file)
                finally:
                    self.mpd.disconnect()

    @commands.command()
    async def searchplaylist(self, ctx, *args):
        '''
        Buscar una playlist y reproducir la seleccionada
        `!searchplaylist franquicia`
        '''
        with open(self.Playlist_Path, 'r') as file:
            playlists = json.load(file)

        res = []
        for saga, pl in playlists.items():
            for item in pl:
                busqueda = args[0].lower()
                target = item['Nombre'].lower()
                match = re.search(busqueda, target)
                if match:
                    res.append(item.copy())

        embed = Embed(
            color=int("c8dde0", 16)
        )
        embed.set_author(name='Selecciona una saga')

        for i, item in enumerate(res, start=1):
            embed.add_field(
                name=f'{i}- {item["Nombre"]}', value=f'Tipo: {item["Tipo"]}', inline=False)
        opciones = await ctx.send(embed=embed)

        i = await self.check_Answer(ctx, opciones, len(res))

        if i != None:
            try:
                self.mpd.connect(self.MPD_Server, self.MPD_Port)
                s = int(self.mpd.currentsong()['pos'])
                self.mpd.delete((s+1,))
                self.mpd.delete((0, s))
                self.mpd.load(res[int(i)]['Playlist'])
                total = len(self.mpd.playlist())
                self.mpd.load(self.Random_Playlist)
                self.mpd.shuffle((total,))
                file = File(await self.get_images('happy'))
                await ctx.send(f'{res[int(i)]["Nombre"]} puesto en cola! c:', file=file)
            except ConnectionError:
                file = File(await self.get_images('worried'))
                await ctx.send(f'A ocurrido un problema de conexión con el servidor de música', file=file)
            finally:
                self.mpd.disconnect()

    @commands.command()
    async def shuffle(self, ctx):
        '''
        Poner toda la base de datos a la cola en aleatorio
        `!shuffle`
        '''
        try:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            s = int(self.mpd.currentsong()['pos'])
            self.mpd.delete((s+1,))
            self.mpd.delete((0, s))
            total = len(self.mpd.playlist())
            # self.mpd.add(Random_Folder) if Random_Folder != None else self.mpd.load(
            #     self.Random_Playlist)
            self.mpd.load(self.Random_Playlist)
            self.mpd.shuffle((total,))
            file = File(await self.get_images('happy'))
            await ctx.send(f'Se ha puesto una cola randomizada a continuación c:', file=file)
        except ConnectionError:
            file = File(await self.get_images('worried'))
            await ctx.send(f'A ocurrido un problema de conexión con el servidor de música', file=file)
        finally:
            self.mpd.disconnect()

    @commands.command()
    async def disableplaylist(self, ctx):
        '''
        Desabilitar una playlist progamada para la semana
        `!disableplaylist`
        '''
        with open(self.Prog_Path, 'r') as file:
            prog = json.load(file)
        embed = Embed(
            color=int("c8dde0", 16)
        )
        embed.set_author(name='Selecciona una saga')
        aux = []
        for i, day in enumerate(prog, start=1):
            embed.add_field(
                name=f'{i}- {day}', value=f'playlists: {len(prog[day])}', inline=False)
            aux.append(day)
        opciones = await ctx.send(embed=embed)

        i = await self.check_Answer(ctx, opciones, len(aux))

        if i != None:
            day = prog[aux[i]]
            embed = Embed(
                color=int("c8dde0", 16)
            )
            embed.set_author(name='Selecciona una Playlist')
            x = 0
            for i, pl in enumerate(day, start=1):
                if pl['Enable']:
                    embed.add_field(
                        name=f'{i}- {pl["Nombre"]}', value=f'{pl["Tipo"]}', inline=False)
                    x += 1
            if x == 0:
                file = File(await self.get_images('surprised'))
                await ctx.send('No hay playlist habilitadas para este día', file=file)
                return

            opciones = await ctx.send(embed=embed)

            i = await self.check_Answer(ctx, opciones, len(day))

            if i != None:
                day[i]['Enable'] = False
                with open(self.Prog_Path, 'w') as file:
                    json.dump(prog, file, indent=3)
                file = File(await self.get_images('happy'))
                await ctx.send('Playlist desabilitada :3', file=file)

    @commands.command()
    async def enableplaylist(self, ctx):
        '''
        Habilitar una playlist progamada para la semana
        `!enableplaylist`
        '''
        with open(self.Prog_Path, 'r') as file:
            prog = json.load(file)
        embed = Embed(
            color=int("c8dde0", 16)
        )
        embed.set_author(name='Selecciona un dia')
        aux = []
        for i, day in enumerate(prog, start=1):
            embed.add_field(
                name=f'{i}- {day}', value=f'playlists: {len(prog[day])}', inline=False)
            aux.append(day)
        opciones = await ctx.send(embed=embed)

        i = await self.check_Answer(ctx, opciones, len(aux))

        if i != None:
            day = prog[aux[i]]
            embed = Embed(
                color=int("c8dde0", 16)
            )
            embed.set_author(name='Selecciona una Playlist')
            x = 0
            for i, pl in enumerate(day, start=1):
                if not pl['Enable']:
                    embed.add_field(
                        name=f'{i}- {pl["Nombre"]}', value=f'{pl["Tipo"]}', inline=False)
                    x += 1
            if x == 0:
                file = File(await self.get_images('surprised'))
                await ctx.send('No hay playlist deshabilitadas para este día', file=file)
                return

            opciones = await ctx.send(embed=embed)

            i = await self.check_Answer(ctx, opciones, len(day))

            if i != None:
                day[i]['Enable'] = True
                with open(self.Prog_Path, 'w') as file:
                    json.dump(prog, file, indent=3)
                file = File(await self.get_images('happy'))
                await ctx.send('Playlist habilitada :3', file=file)

    @commands.command()
    async def programacion(self, ctx, *args):
        '''
        Revisar la programación semanal (si es más de 1 día rotará por ellos cada 5 seg)
        `!programacion [dia|dias]`
        '''
        e = []
        with open(self.Prog_Path, 'r') as f:
            prog = json.load(f)

        if len(args) != 0:
            for x in args:
                x.lower()
        for day, value in prog.items():
            if len(args) == 0 or day.lower() in args:
                embed = Embed(
                    title=f'{day}:',
                    colour=int("c8dde0", 16)
                )
                embed.set_author(name='Programación:')
                for i, item in enumerate(value):
                    for x, y in item.items():
                        if x != 'Playlist':
                            embed.add_field(
                                name=f'{x}:', value=f'{y}', inline=True)
                    if i != (len(value) - 1):
                        embed.add_field(
                            name='\u200b', value='\u200b', inline=False)
                e.append(embed)
        message = await ctx.send('Aqui está la programación ^^')

        for x in e:
            await message.edit(embed=x)
            await asyncio.sleep(5)

    @programacion.error
    async def send_schedule_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')

    @commands.command()
    async def lyrics(self, ctx, *args):
        '''
        Obtener la letra sobre una canción, esta puede ser la canción actual, una posición en relación a la actual o una busqueda por su nombre
        `!lyrics [-pos|+pos|busqueda]`
        '''
        try:
            self.mpd.connect(self.MPD_Server, self.MPD_Port)
            now = int(self.mpd.currentsong()['pos'])
            if len(args) > 1:
                query = ' '.join(args)
            elif len(args) == 1:
                try:
                    i = int(args[-1])
                    query = self.mpd.playlistinfo(now + i)[-1]['title']
                except ValueError:
                    query = args[-1]
            else:
                query = self.mpd.playlistinfo(now)[-1]['title']
        finally:
            self.mpd.disconnect()
        msg = '```\n'
        msg += f'**{query}**\n\n'
        song = await self.get_lyrics(ctx, query)
        msg += song
        msg += '\n```'
        await ctx.send(msg)

    @lyrics.error
    async def lyrics_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            await ctx.send(f'Error al ejecutar el comando >-<\"\n{error}')

    @commands.command()
    async def remove(self, ctx, pos: int = 0):
        '''
        Eliminar la canción actuál o en la posición indicada de la Playlist aleatoria
        `!remove [-pos|+pos]`
        '''
        self.mpd.connect(self.MPD_Server, self.MPD_Port)
        currentPlaying = int(self.mpd.currentsong()['pos'])

        total = len(self.mpd.playlist()) - 1

        if currentPlaying + pos > total or currentPlaying + pos < 0:
            await ctx.send('Canción fuera de rango!')
            await ctx.send(f'Existen `{currentPlaying - 1}` Canciones antes que esta y `{total - currentPlaying}` despues!')
            self.mpd.disconnect()
            return

        song = self.mpd.playlistinfo(currentPlaying + pos)[-1]

        if song['file'] in self.random:
            index = self.random.index(song['file'])
            self.mpd.playlistdelete(self.Random_Playlist, index)
            self.random.pop(index)
            await ctx.send(f'{song["title"]} fue eliminada de la playlist aleatoria')
        else:
            await ctx.send(f'{song["title"]} No está en la playlist aleatoria')

        self.mpd.disconnect()

    @tasks.loop(seconds=5, count=1)
    async def message(self, ctx):
        channel = ctx.message.guild.voice_client
        await ctx.send('I disconected, please reload me :c')
        await channel.disconnect()

    # @tasks.loop(seconds=5)
    # async def send_current_song(self):
    #     await self.bot.wait_until_ready()
    #     channel = self.bot.get_channel(self.channels['currentPlaying'])

    #     try:
    #         self.mpd.connect(self.MPD_Server, self.MPD_Port)
    #         song = self.mpd.currentsong()
    #         self.mpd.disconnect()
    #         with open('lastSong.json', 'r') as f:
    #             lastSong = json.load(f)

    #         if lastSong['id'] != song['id']:
    #             with open('lastSong.json', 'w') as f:
    #                 json.dump(song, f)
    #             # Settear Embed
    #             embed = Embed(
    #                 title=':headphones:',
    #                 colour=int("c8dde0", 16)
    #             )

    #             embed.set_author(
    #                 name='Actualmente está sonando la siguiente canción:')

    #             if 'title' in song:
    #                 embed.add_field(
    #                     name='Título', value=song['title'], inline=False)
    #             if 'album' in song:
    #                 embed.add_field(
    #                     name='Album', value=song['album'], inline=False)
    #             if 'artist' in song:
    #                 embed.add_field(
    #                     name='artista', value=song['artist'], inline=False)
    #             if 'composer' in song:
    #                 embed.add_field(name='Compositor',
    #                                 value=song['composer'], inline=False)

    #             embed.add_field(name='\u200b', value='\u200b', inline=False)

    #             if int(song['pos']) > 3:
    #                 self.mpd.connect(self.MPD_Server, self.MPD_Port)
    #                 lsSongs = self.mpd.playlistinfo()[int(
    #                     song['pos'])-3:int(song['pos'])+3]
    #                 self.mpd.disconnect()

    #                 last = []
    #                 prox = []

    #                 if 'title' in lsSongs[2]:
    #                     last.append(lsSongs[2]['title'])
    #                 if 'album' in lsSongs[2]:
    #                     last.append(lsSongs[2]['album'])
    #                 last.append('\n')
    #                 if 'title' in lsSongs[1]:
    #                     last.append(lsSongs[1]['title'])
    #                 if 'album' in lsSongs[1]:
    #                     last.append(lsSongs[1]['album'])

    #                 if 'title' in lsSongs[4]:
    #                     prox.append(lsSongs[4]['title'])
    #                 if 'album' in lsSongs[4]:
    #                     prox.append(lsSongs[4]['album'])
    #                 prox.append('\n')
    #                 if 'title' in lsSongs[5]:
    #                     prox.append(lsSongs[5]['title'])
    #                 if 'album' in lsSongs[5]:
    #                     prox.append(lsSongs[5]['album'])

    #                 embed.add_field(name='Anterior',
    #                                 value='\n*'.join(last), inline=True)

    #                 embed.add_field(name='Siguiente',
    #                                 value='\n*'.join(prox), inline=True)

    #             messagesList = await channel.history(limit=10).flatten()
    #             if len(messagesList) == 0:
    #                 await channel.send(embed=embed)
    #             else:
    #                 await messagesList[-1].edit(embed=embed)
    #     finally:
    #         self.mpd.disconnect()

    async def check_Answer(self, ctx, msg, lenght):
        try:
            res = await self.bot.wait_for('message', timeout=15.0, check=lambda message: message.author == ctx.author)
            await msg.delete()
        except asyncio.TimeoutError:
            await msg.delete()
            file = File(await self.get_images('worried'))
            await ctx.send('Tiempo de respuesta superado', file=file)
            return None

        try:
            i = int(res.content) - 1
            if i < 0 or i >= lenght:
                raise Exception('index')
            return i
        except ValueError:
            file = File(await self.get_images('confused'))
            await ctx.send(f'La respuesta no fue un número', file=file)
            return None
        except:
            file = File(await self.get_images('confused'))
            await ctx.send(f'la opción no está en el rango', file=file)
            return None

    async def get_images(self, image):
        aux = []
        for file in os.listdir(self.Images):
            if file.endswith('.png') and re.search(image, file):
                aux.append(file)
        return self.Images + random.choice(aux)

    async def get_lyrics(self, ctx, query):
        async with ctx.channel.typing():
            song = self.genius.search_song(query)
            while song == None:
                asyncio.sleep(1)
            return song.lyrics


def setup(bot):
    bot.add_cog(Mpd(bot))
