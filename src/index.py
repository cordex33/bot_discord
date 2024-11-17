import discord
from discord.ext import commands, tasks
import datetime
from dotenv import load_dotenv
import os
import urllib.request, json
import requests

import sqlite3


#--------------Variables a ordenar--------------#

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

chile_tz = datetime.datetime.now().astimezone().tzinfo
hora_entrar = datetime.time(hour=21, minute=21, tzinfo=chile_tz)
hora_salida = datetime.time(hour=21, minute=26, tzinfo=chile_tz)

bot = commands.Bot(command_prefix='>', description="Bot creado para MK", intents=discord.Intents.all())

#--------------comandos de bot--------------#

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="Información acerca del bot", description="Aquí va a ir todo con lo relacionado al bot.", 
                          timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=-3), 
                          color=discord.Color.blue())
    embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

    msg = await ctx.send(embed=embed)
    await msg.add_reaction('❗')

@bot.command()
async def registrar(ctx, *options):

    dm_privado = await ctx.author.create_dm()

    channel = discord.utils.get(ctx.guild.text_channels, name='general')
    
    if not options:
        embed = discord.Embed(title="Registro", description="Proceso para el registro de asistencia.",
                          color=discord.Color.blue())
        embed.add_field(name="Por favor.", value="utiliza '>registrar' seguido de tu rut (con guion).")
        embed.add_field(name="Ejemplo:", value=">registrar 11111111-1")
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")
        await channel.send(embed=embed)
        return
    
    if '-' not in options[0]: 
        
        await dm_privado.send("Por favor ingrese su rut con guion.")
        return
    
    elif len(options[0]) < 10 or len(options[0]) > 10:
        await dm_privado.send(f"Estimado, por favor verifique que su rut esté escrito correctamente: '{options[0]}'.")
        await dm_privado.send(f"Le recuerdo que debe ser: '11111111-1'.")
        return
    
    elif options:
        rut = options[0]
        id_discord = ctx.author.id

        mi_conexion = sqlite3.connect("src/database/usuarios")
        cursor = mi_conexion.cursor()

        cursor.execute("SELECT * FROM usuario WHERE id_discord = ?", (id_discord,)) #Comprobamos si hay una usuario ya con el id de discord
        resultado = cursor.fetchone()

        if resultado:
            await dm_privado.send(f"Estimado, usted ya se encuentra en nuestros registros.")
            return
        else:
            cursor.execute("INSERT INTO usuario (id_discord, rut) VALUES (?, ?)", (id_discord, rut))
            await dm_privado.send(f"Registro con exito! con el rut '{options[0]}'")
            mi_conexion.commit()
            return
    

    
#--------------Eventos de bot--------------#

@bot.event
async def on_reaction_add(reaction: discord.Reaction, user):
    if user == bot.user:
        return
    
    #
    if reaction.message.author == bot.user and str(reaction.emoji) == '✅':
        enviar_dm = await user.create_dm()
        id_discord = user.id

        await enviar_dm.send(marcar_entrada(id_discord))

    if reaction.message.author == bot.user and str(reaction.emoji) == '❗':
        enviar_dm = await user.create_dm()

        id_discord = user.id
        await enviar_dm.send(marcar_salida(id_discord))
    
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="bot entrenando", url="https://www.twitch.tv/rambodriving"))
    print('todo bien')
    print(datetime.datetime.now())
    mensaje_entrada.start()
    mensaje_salida.start()


@bot.event
async def on_member_join(member: discord.Member) -> None:
    channel = discord.utils.get(member.guild.text_channels, name='general')
    if channel:
        await channel.send(f'Bienvenido {member.mention}')
        await member.send('todo bien?')

#--------------Hasta acá--------------


#--------------Mensajes automatizados--------------#
#Mensaje de salida
@tasks.loop(time=hora_entrar)
async def mensaje_entrada():
    print("etnré al msj de entrada")
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    
    if hora == hora_entrar.strftime("%H:%M") and not es_feriado(): #Agregar paraa sabado y domingo: and not datetime.datetime.today().weekday() == 5 and not datetime.datetime.today().weekday() == 6:

        guild = discord.utils.get(bot.guilds, id=827940399422111754)  #Cambiar por id del sv que queremos enviar msj

        channel = discord.utils.get(guild.text_channels, name='general')
        embed = discord.Embed(title="Marcar entrada", description="Buenos días, recuerden marcar entrada!.", 
                          timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=-3), 
                          color=discord.Color.blue())
        
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        msg = await channel.send(embed=embed)
        esperar = await msg.add_reaction('✅')
        

#Mensaje de salida
@tasks.loop(time=hora_salida)
async def mensaje_salida():
    print("entré mensaje salida")
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    
    if hora == hora_salida.strftime("%H:%M") and not es_feriado():

        guild = discord.utils.get(bot.guilds, id=827940399422111754)
        
        channel = discord.utils.get(guild.text_channels, name='general')
        embed = discord.Embed(title="Marcar Salida", description="Hasta mañana, recuerden marcar salida!.", 
                          timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=-3), 
                          color=discord.Color.blue())
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        msg = await channel.send(embed=embed)
        await msg.add_reaction('❗')


#--------------Funciones--------------#

def es_feriado():
    url = "https://apis.digital.gob.cl/fl/feriados/2024"
    autori = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(autori) as datos:
        json_feriados = json.load(datos)  

    for feriado in json_feriados:
        hoy = datetime.datetime.today().strftime('%m-%d')
        fecha_feriado = datetime.datetime.strptime(feriado['fecha'], '%Y-%m-%d').strftime('%m-%d')

        if fecha_feriado == hoy:
            return True
        else:
            return False

def marcar_entrada(id_discord):

    mi_conexion = sqlite3.connect("src/database/usuarios")
    cursor = mi_conexion.cursor()

    cursor.execute("SELECT rut FROM usuario WHERE id_discord = ?", (id_discord,))

    try:
        rut = cursor.fetchone()[0]
    except:
        print("entreasds")
        return (f"Usted no se encuentra en nuestra base de datos. Por favor use '>registro'")

    request_entrada = requests.get('https://app.ctrlit.cl/ctrl/dial/registrarweb/EUqtz5lvAg?i=1&lat=&lng=&r=19275294-9') 
    estado_entrada = request_entrada.content.decode('utf-8')

    if estado_entrada == 'ok':
        return (f"Ha marcado entrada con exito!.")
    else:
        return (f"Ya marcó entrada, usted no ha marcado salida.")
    
    
def marcar_salida(id_discord):
    mi_conexion = sqlite3.connect("src/database/usuarios")
    cursor = mi_conexion.cursor()

    cursor.execute("SELECT rut FROM usuario WHERE id_discord = ?", (id_discord,))

    try:
        rut = cursor.fetchone()[0]
    except:
        print("entre")
        return (f"Usted no se encuentra en nuestra base de datos. Por favor use '>registro'")

  
    request_salida = requests.get('https://app.ctrlit.cl/ctrl/dial/registrarweb/EUqtz5lvAg?i=0&lat=&lng=&r=19275294-9') 
    estado_salida = request_salida.content.decode('utf-8')

    if estado_salida == 'ok':
        return (f"Ha marcado salida con exito!.")
    else:
        return (f"Ya marcó salida, usted no ha marcado entrada.")


bot.run(token)