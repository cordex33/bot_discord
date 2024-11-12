import discord
from discord.ext import commands, tasks
import datetime
from dotenv import load_dotenv
import os
import urllib.request, json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


#--------------Variables a ordenar--------------#

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

chile_tz = datetime.datetime.now().astimezone().tzinfo
hora_entrar = datetime.time(hour=18, minute=40, tzinfo=chile_tz)
hora_salida = datetime.time(hour=18, minute=00, tzinfo=chile_tz)

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
    channel = discord.utils.get(ctx.guild.text_channels, name='general')
    
    
    if not options:
       
        embed = discord.Embed(title="Registro", description="Proceso para el registro de asistencia.",
                          color=discord.Color.blue())
        embed.add_field(name="Por favor.", value="utiliza '>registrar' seguido de tu nombre completo (nombre y apellidos)")
        embed.add_field(name="Ejemplo:", value=">registrar PACIENTE PRUEBA GONZALES GONZALES")
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")
        await channel.send(embed=embed)
        return
    
    elif len(options) < 3: 
            await channel.send("Por favor ingrese nombre completo")
            return
    
    elif options:
        id_discord = ctx.author.id

        nombre = ''    
        for x in options:
            nombre += x.capitalize()+ " "
        nombre = nombre[:-1]

        chrome_options = Options()
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        service = Service(executable_path=r"C:\dchrome\chromedriver.exe")
        print("prosigo1")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("http://127.0.0.1:8000/registro/")

        button = driver.find_element(By.ID, "enviar")
        input_id = driver.find_element(By.ID, "registro_id")
        input_nombre = driver.find_element(By.ID, "registro_nombre")
        input_sector = driver.find_element(By.ID, "registro_sector")
        
        input_id.send_keys(id_discord)
        input_nombre.send_keys(nombre)
        button.click()

        time.sleep(0.01)

        console_log = driver.get_log('browser')
        console_log = console_log[0]['message']
        
        if "Ya se ha registrado" in console_log:
            indice = console_log.index("Ya se ha registrado")
            console_log = console_log[indice: -1]
            dm_privado = await ctx.author.create_dm()
            await dm_privado.send(f"Estima@ {nombre}. {console_log}.")
            driver.quit()
            return
        
        elif "Usuario registrado" in console_log:
            indice = console_log.index("Usuario registrado")
            console_log = console_log[indice: -1]
            dm_privado = await ctx.author.create_dm()
            await dm_privado.send(f"Estima@ {nombre}. {console_log}.")
            driver.quit()
            return

        return


    
#evento del bot
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user):
    if user == bot.user:
        return
    
    print(user.id)

    #
    if reaction.message.author == bot.user and str(reaction.emoji) == '✅':
        dm_channel = await user.create_dm()

        discord_id = user.id
        marcar_entrada(discord_id)
        await dm_channel.send("Quedaste registrado.")

    if reaction.message.author == bot.user and str(reaction.emoji) == '❗':
        return
    
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="bot entrenando", url="https://www.twitch.tv/rambodriving"))
    print('todo bien')
    mensaje_entrada.start()
    mensaje_salida.start()


@bot.event
async def on_member_join(member: discord.Member) -> None:
    channel = discord.utils.get(member.guild.text_channels, name='general')
    if channel:
        await channel.send(f'Bienvenido ql {member.mention}')
        await member.send('todo bien todo contento?')

#--------------Hasta acá--------------

#Mensaje de entrar
@tasks.loop(time=hora_entrar)
async def mensaje_entrada():
    print("entré")
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    
    if hora == hora_entrar.strftime("%H:%M") and not es_feriado():
        guild = discord.utils.get(bot.guilds, id=827940399422111754)

        channel = discord.utils.get(guild.text_channels, name='general')
        embed = discord.Embed(title="Marcar entrada", description="marquen entrada monos ql", 
                          timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=-3), 
                          color=discord.Color.blue())
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        msg = await channel.send(embed=embed)
        esperar = await msg.add_reaction('✅')
        

#Mensaje de salida
@tasks.loop(time=hora_salida)
async def mensaje_salida():
    
    hora = datetime.datetime.now(chile_tz).strftime("%H:%M")
    
    if hora == hora_salida.strftime("%H:%M") and not es_feriado():
        guild = discord.utils.get(bot.guilds, id=712797175838408775)
        channel = discord.utils.get(guild.text_channels, name='general')
        embed = discord.Embed(title="Marcar Salida", description="marquen salida monos ql", 
                          timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=-3), 
                          color=discord.Color.blue())
        embed.set_thumbnail(url="https://www.masterkey.cl/images/logo-mk-new.png")

        msg = await channel.send(embed=embed)
        await msg.add_reaction('✅')


#--------------Funciones--------------
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

def marcar_entrada(discord_id):

    service = Service(executable_path=r"C:\dchrome\chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    driver.get("http://127.0.0.1:8000/registro/")
    button = driver.find_element(By.ID, "entrada")
    label = driver.find_element(By.ID, "registro_id_entrada")

    
    label.send_keys(discord_id)
    button.click()
    driver.quit()
    return print("todo bien tod contento!")

bot.run(token)