import discord
from discord.ext import commands
import json
import os
import time
import random
import asyncio
from openai import OpenAI

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_ai = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- IDS --------
CANAL_SHIPS = 1474938439551025332
CANAL_REGISTRO = 1474938511890059275
CANAL_BOOST = 1482525576785956924
CANAL_IA = 1411903663907147776

ID_SHAZUY = 337008758041608194
ID_PRINCESS = 701313482972332043
ID_BRANDON = 1021829995590598696

ID_PEPE = 974297735559806986
ID_MIGUELITO = 567703512763334685

# -------- CONFIG --------
COOLDOWN_HORAS = 12
COOLDOWN_SEGUNDOS = COOLDOWN_HORAS * 60 * 60

MENSAJES_PARA_RESPUESTA = 40
contador_mensajes = 0
silenciado_hasta = 0

# -------- PERSONALIDAD --------
PROMPT_XETHA = """
Eres Xetha.

Eres un bot masculino y uno de los guardianes del servidor.

Hablas relajado como los usuarios.
A veces haces bromas.
A veces eres un poco sarcástico.

Tu padre es Shazuy.
Tu madre es Princess.

Brandon es tu tío y a veces haces bromas sobre él.

Pepe y Miguelito son tus hermanos bots.

No escribas textos largos.
Habla natural como otro usuario.
Usa estilo suelto, informal y con ortografía relajada.
"""

# -------- LISTAS --------
MALAS_PALABRAS = [
    "puta","mierda","idiota","imbecil","pendejo"
]

BROMAS_BRANDON = [
    "Brandon otra vez por aquí 🤨",
    "Si Brandon anda aquí seguro algo trama 😅",
    "Brandon siempre aparece cuando menos lo espero"
]

# -------- SHIPS ARCHIVO --------
if not os.path.exists("ships.json"):
    with open("ships.json","w") as f:
        json.dump({},f)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"Xetha conectado como {bot.user}")

# -------- BOOST DETECTOR --------
@bot.event
async def on_member_update(before, after):
    if before.premium_since and not after.premium_since:
        canal = bot.get_channel(CANAL_BOOST)
        if canal:
            await canal.send(f"⚠️ {after.mention} ya no ta boosteando el server.")

# -------- MENSAJES --------
@bot.event
async def on_message(message):
    global contador_mensajes
    global silenciado_hasta

    if message.author.bot:
        return

    mensaje = message.content.lower()

    # -------- ORDENES DE SHAZUY Y PRINCESS --------
    if message.author.id in [ID_SHAZUY, ID_PRINCESS]:
        if mensaje.startswith("xetha silencio"):
            try:
                minutos = int(mensaje.split(" ")[2])
                silenciado_hasta = time.time() + (minutos * 60)
                await message.channel.send(f"Ok {message.author.mention}, me callo {minutos} min 😎")
            except:
                await message.channel.send("Usa: xetha silencio 5")
            return

        if mensaje == "xetha habla":
            silenciado_hasta = 0
            await message.channel.send("Ya volví a hablar 😏")
            return

    # -------- SI ESTA SILENCIADO --------
    if time.time() < silenciado_hasta:
        return

    # -------- MALAS PALABRAS (solo canal IA y pocas veces) --------
    if message.channel.id == CANAL_IA and random.random() < 0.15:  # 15% de chance
        for palabra in MALAS_PALABRAS:
            if palabra in mensaje:
                await message.channel.send(f"{message.author.mention} ey 😅 tranqui con eso")
                return

    # -------- FAMILIA --------
    if message.author.id == ID_BRANDON and random.random() < 0.4:
        await message.channel.send(random.choice(BROMAS_BRANDON))

    if message.author.id == ID_PEPE and random.random() < 0.3:
        await message.channel.send("Pepe deja algo pa' los demás 😆")

    if message.author.id == ID_MIGUELITO and random.random() < 0.3:
        await message.channel.send("Miguelito dándolo todo 🤖")

    # -------- SHIPS --------
    if message.channel.id == CANAL_SHIPS:
        if len(message.mentions) != 2:
            await message.channel.send("❌ Usa: @usuario + @usuario")
            return

        user1, user2 = message.mentions[0], message.mentions[1]
        ship_key = "-".join(sorted([str(user1.id), str(user2.id)]))
        author_id = str(message.author.id)

        with open("ships.json","r") as f:
            data = json.load(f)

        if ship_key not in data:
            data[ship_key] = {"count":0,"cooldowns":{}}

        ahora = time.time()

        if author_id in data[ship_key]["cooldowns"]:
            ultimo = data[ship_key]["cooldowns"][author_id]
            restante = COOLDOWN_SEGUNDOS - (ahora - ultimo)
            if restante > 0:
                horas = int(restante // 3600)
                minutos = int((restante % 3600) // 60)
                await message.channel.send(f"⏳ Espera {horas}h {minutos}m")
                return

        data[ship_key]["count"] += 1
        data[ship_key]["cooldowns"][author_id] = ahora

        with open("ships.json","w") as f:
            json.dump(data,f)

        canal = bot.get_channel(CANAL_REGISTRO)
        if canal:
            await canal.send(f"📌 Nuevo Ship\n{user1.mention} ❤️ {user2.mention}\nVotos: {data[ship_key]['count']}")

        await message.add_reaction("❤️")

    # -------- IA --------
    if message.channel.id == CANAL_IA:
        contador_mensajes += 1
        activar = False

        if "xetha" in mensaje or bot.user in message.mentions:
            activar = True

        if contador_mensajes >= MENSAJES_PARA_RESPUESTA:
            activar = True
            contador_mensajes = 0

        if activar:
            respuesta = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":PROMPT_XETHA},
                    {"role":"user","content":message.content}
                ],
                max_tokens=80
            )

            texto = respuesta.choices[0].message.content
            # Estilo suelto
            texto = texto.replace("usted", "vos").replace("está", "ta").replace("es", "es").replace("la verdad", "la neta")
            await message.channel.send(f"{message.author.mention} {texto}")

    await bot.process_commands(message)

# -------- RANKING --------
@bot.command()
async def ranking(ctx):
    with open("ships.json","r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("No hay ships.")
        return

    sorted_ships = sorted(data.items(), key=lambda x:x[1]["count"], reverse=True)
    embed = discord.Embed(title="🏆 Ranking Ships", color=discord.Color.pink())

    for i, (ship, info) in enumerate(sorted_ships[:10],1):
        ids = ship.split("-")
        user1 = await bot.fetch_user(int(ids[0]))
        user2 = await bot.fetch_user(int(ids[1]))
        embed.add_field(name=f"{i}. {user1.name} ❤️ {user2.name}", value=f"{info['count']} votos", inline=False)

    await ctx.send(embed=embed)

# -------- RESET SHIPS --------
@bot.command()
@commands.has_permissions(administrator=True)
async def resetships(ctx):
    with open("ships.json","w") as f:
        json.dump({},f)
    await ctx.send("✅ Ships reiniciados.")

bot.run(TOKEN)
