import discord
from discord.ext import commands, tasks
import datetime
from dotenv import load_dotenv
import os
import urllib.request, json
import requests
import sqlite3


#--------------Variables a ordenar--------------#
db_path = 'home/ubuntu/discord-bot/bot_discord/src/database/usuarios'
load_dotenv()
token = os.getenv("DISCORD_TOKEN")

chile_tz = datetime.datetime.now().astimezone().tzinfo
hora_entrar = datetime.time(hour=8, minute=30, tzinfo=chile_tz)

bot = commands.Bot(command_prefix='>', description="Bot creado para MK", intents=discord.Intents.all(), help_command=None)

#--------------comandos de bot--------------#

@bot.command()
async def info(ctx):
    dm_privado = await ctx.author.create_dm()
    embed = discord.Embed(
        title="Información acerca del bot", description="Aquí va a ir todo con lo relacionado al bot.", 
        timestamp=datetime.datetime.now(), 
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

    await dm_privado.send(embed=embed)

@bot.command()
async def registrar(ctx, *options):
    dm_privado = await ctx.author.create_dm()
    
    if not options:
        embed = discord.Embed(
            title="Registro", description="Proceso para el registro de asistencia.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Por favor.", value="utiliza '>registrar' seguido de tu rut (con guion).")
        embed.add_field(name="Ejemplo:", value=">registrar 11111111-1")
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        await dm_privado.send(embed=embed)
        return
    
    elif '-' not in options[0]: 
        
        await dm_privado.send("Por favor ingrese su rut con guion.")
        return
    
    elif len(options[0]) < 10 or len(options[0]) > 10:
        await dm_privado.send(f"Estimado, por favor verifique que su rut esté escrito correctamente: '{options[0]}'.")
        await dm_privado.send(f"Le recuerdo que debe ser: '11111111-1'.")
        return
    
    elif options:
        rut = options[0]
        id_discord = ctx.author.id

        mi_conexion = sqlite3.connect(db_path) #db_path en el sv de aws
        cursor = mi_conexion.cursor()

        cursor.execute("SELECT * FROM usuario WHERE id_discord = ?", (id_discord,)) #Comprobamos si hay una usuario ya con el id de discord
        resultado = cursor.fetchone()

        if resultado:
            await dm_privado.send(f"Estimado, usted ya se encuentra en nuestros registros, si cree que esto es un error, por favor comuniquese con <@1154144508490043482>.")
            return
        else:
            cursor.execute("INSERT INTO usuario (id_discord, rut) VALUES (?, ?)", (id_discord, rut))
            await dm_privado.send(f"Registro con exito! con el rut '{options[0]}'")
            mi_conexion.commit()
            return
    
@bot.command()
async def help(ctx):
    dm_privado = await ctx.author.create_dm()
    
    embed = discord.Embed(
        title="Comandos del bot", description="Por ahora solo contamos con el comando de '>registro'.", 
        timestamp=datetime.datetime.now(), 
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")
    await dm_privado.send(embed=embed)

#--------------Eventos de bot--------------#

@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return
    
    confirmar_bot = False 
    
    async for usuario in reaction.users(): #Vemos si el bot reaccionó a su msj
        if usuario.bot:  
            confirmar_bot = True
            break 


    if reaction.message.author == bot.user and str(reaction.emoji) == '✅' and confirmar_bot:
        enviar_dm = await user.create_dm()
        id_discord = user.id

        await enviar_dm.send(marcar_entrada(id_discord))

    if reaction.message.author == bot.user and str(reaction.emoji) == '❗' and confirmar_bot:
        enviar_dm = await user.create_dm()

        id_discord = user.id
        await enviar_dm.send(marcar_salida(id_discord))

@bot.event
async def on_message(ctx):

    if isinstance(ctx.channel, discord.DMChannel):
        if ctx.author.bot:
            return
        else:
            asd = await ctx.author.create_dm()
            await asd.send("Por favor usemos el canal: <#1312559101380657152>.") #Cambiar canal mk-bot dependiendo del sv
            return
        

    elif ctx.channel.name == 'mk-bot' and not ctx.author.bot:
        print("entré al if")
        await ctx.delete()
    else:
        print("entre al else")
        return

    await bot.process_commands(ctx)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="Master🤖 >help"))
    print('todo bien')
    print(datetime.datetime.now())
    mensaje_entrada.start()
    mensaje_salida.start()

@bot.event
async def on_member_join(member: discord.Member) -> None:
    channel = discord.utils.get(member.guild.text_channels, name='bienvenida')
    if channel:
        await channel.send(f'¡Bienvenido/a {member.mention} al equipo de MasterKey. Nos complace contar con tu presencia en nuestra comunidad!.')
        await member.send('Si tienes alguna duda o necesitas asistencia, no dudes en ponerte en contacto con cualquiera de nosotros. ¡Estamos aquí para apoyarte en tu integración!')

#--------------Hasta acá--------------


#--------------Mensajes automatizados--------------#
#Mensaje de entrada
@tasks.loop(time=hora_entrar)
async def mensaje_entrada():
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    
    if hora == hora_entrar.strftime("%H:%M") and not es_feriado(): #Agregar paraa sabado y domingo: and not datetime.datetime.today().weekday() == 5 and not datetime.datetime.today().weekday() == 6:

        guild = discord.utils.get(bot.guilds, id=1308175474140123177)  #Cambiar por id del sv que queremos enviar msj

        channel = discord.utils.get(guild.text_channels, name='mk-bot')
        embed = discord.Embed(
            title="Marcar entrada", 
            description="¡Buenos días! No olviden marcar su entrada antes de comenzar la jornada.", 
            timestamp=datetime.datetime.now(), 
            color=discord.Color.blue()
        )
        
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")
        msg = await channel.send(content="@everyone", embed=embed, delete_after=77390)
        await msg.add_reaction('✅')
        

#Mensaje de salida
@tasks.loop(minutes=1)
async def mensaje_salida():
    print("entré mensaje salida")
    chile_tz = datetime.datetime.now().astimezone().tzinfo
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    hora_salida = calcular_hora_salida().strftime("%H:%M")

    
    if hora == hora_salida and not es_feriado():
        guild = discord.utils.get(bot.guilds, id=1308175474140123177) #Cambiar por id del sv que queremos enviar msj
        channel = discord.utils.get(guild.text_channels, name='mk-bot')

        embed = discord.Embed(
            title="Marcar Salida", 
            description="Recuerden marcar su salida antes de finalizar su jornada. Que tengan un excelente descanso.", 
            timestamp=datetime.datetime.now(), 
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        msg = await channel.send(content="@everyone", embed=embed, delete_after=43200)
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

    mi_conexion = sqlite3.connect(db_path) #db_path en servidor aws
    cursor = mi_conexion.cursor() 

    cursor.execute("SELECT rut FROM usuario WHERE id_discord = ?", (id_discord,))

    try:
        rut = cursor.fetchone()[0]
    except:

        return (f"Usted no se encuentra en nuestra base de datos. Por favor use '>registro'")

    request_entrada = requests.get('https://app.ctrlit.cl/ctrl/dial/registrarweb/EUqtz5lvAg?i=1&lat=&lng=&r=' + rut) 
    estado_entrada = request_entrada.content.decode('utf-8')

    if estado_entrada == 'ok':
        return (f"Ha marcado entrada con exito!.")
    else:
        return (f"Ya marcó entrada, usted no ha marcado salida.")
    
    
def marcar_salida(id_discord):
    mi_conexion = sqlite3.connect(db_path) #db_path en servidor aws
    cursor = mi_conexion.cursor()

    cursor.execute("SELECT rut FROM usuario WHERE id_discord = ?", (id_discord,))

    try:
        rut = cursor.fetchone()[0]
    except:

        return (f"Usted no se encuentra en nuestra base de datos. Por favor use '>registro'")

  
    request_salida = requests.get('https://app.ctrlit.cl/ctrl/dial/registrarweb/EUqtz5lvAg?i=0&lat=&lng=&r=' + rut) 
    estado_salida = request_salida.content.decode('utf-8')

    if estado_salida == 'ok':
        return (f"Ha marcado salida con exito!.")
    else:
        return (f"Ya marcó salida, usted no ha marcado entrada.")
    
def calcular_hora_salida():
    chile_tz = datetime.datetime.now().astimezone().tzinfo
    hoy = datetime.datetime.now(chile_tz).weekday()  # 0 = lunes, 4 = viernes
    
    if hoy == 4:  # si es viernes
        return datetime.time(hour=17, minute=0, tzinfo=chile_tz)
    else:
        return datetime.time(hour=18, minute=0, tzinfo=chile_tz)


bot.run(token)