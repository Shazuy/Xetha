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

# -------- IDS IMPORTANTES --------

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

MENSAJES_PARA_RESPUESTA = 20
contador_mensajes = 0

# -------- PERSONALIDAD DE XETHA --------

PROMPT_XETHA = """
Eres Xetha.

Eres un bot masculino y uno de los guardianes del servidor.

Personalidad:
Hablas relajado como los usuarios.
No eres demasiado formal.
A veces haces bromas.
A veces eres un poco sarcástico.

Te refieres a ti mismo como hombre.

Familia:
Tu padre es Shazuy.
Tu madre es Princess.
Siempre hablas bien de ellos.

Brandon:
Es tu tío.
A veces haces bromas diciendo que te cae un poco mal.

Pepe y Miguelito:
Son tus hermanos bots.

Tus respuestas deben ser cortas o medianas.
Habla natural como un usuario del chat.
"""

# -------- LISTAS --------

MALAS_PALABRAS = [
"puta",
"mierda",
"idiota",
"imbecil",
"pendejo"
]

BROMAS_BRANDON = [
"Brandon otra vez por aquí… sospechoso 🤨",
"Si Brandon anda aquí seguro algo trama 😅",
"Brandon siempre aparece cuando menos lo espero."
]

PREGUNTAS = [
"¿Quién sigue activo por aquí?",
"Pregunta random: ¿pizza o hamburguesa? 🍕",
"¿Qué están jugando hoy?",
"¿Alguien viendo alguna serie buena?",
"¿Quién anda aburrido por aquí?"
]

# -------- ARCHIVO SHIPS --------

if not os.path.exists("ships.json"):
    with open("ships.json","w") as f:
        json.dump({},f)

# -------- MENSAJES AUTOMATICOS --------

async def mensajes_automaticos():

    await bot.wait_until_ready()

    while not bot.is_closed():

        tiempo = random.randint(900,3600)

        await asyncio.sleep(tiempo)

        canal = bot.get_channel(CANAL_IA)

        if canal:
            await canal.send(random.choice(PREGUNTAS))

# -------- BOT LISTO --------

@bot.event
async def on_ready():

    print(f"Xetha conectado como {bot.user}")

    bot.loop.create_task(mensajes_automaticos())

# -------- DETECTOR BOOST --------

@bot.event
async def on_member_update(before, after):

    if before.premium_since and not after.premium_since:

        canal = bot.get_channel(CANAL_BOOST)

        if canal:
            await canal.send(
                f"⚠️ {after.mention} ya no está boosteando el servidor."
            )

# -------- MENSAJES --------

@bot.event
async def on_message(message):

    global contador_mensajes

    if message.author.bot:
        return

    mensaje = message.content.lower()

    # -------- DETECTOR MALAS PALABRAS --------

    for palabra in MALAS_PALABRAS:

        if palabra in mensaje:

            await message.channel.send(
                f"{message.author.mention} ey 😅 bajemos un poco el tono."
            )
            return

    # -------- DETECTAR FAMILIA --------

    if message.author.id == ID_SHAZUY:
        if random.random() < 0.3:
            await message.channel.send("Mi padre apareció 👀")

    if message.author.id == ID_PRINCESS:
        if random.random() < 0.3:
            await message.channel.send("Mi madre está aquí ✨")

    if message.author.id == ID_BRANDON:
        if random.random() < 0.4:
            await message.channel.send(random.choice(BROMAS_BRANDON))

    if message.author.id == ID_PEPE:
        if random.random() < 0.3:
            await message.channel.send("Pepe deja algo para los demás bots 😆")

    if message.author.id == ID_MIGUELITO:
        if random.random() < 0.3:
            await message.channel.send("Miguelito trabajando duro otra vez 🤖")

    # -------- SISTEMA SHIPS --------

    if message.channel.id == CANAL_SHIPS:

        if len(message.mentions) != 2:

            await message.channel.send(
                "❌ Usa el formato: @usuario + @usuario"
            )
            return

        user1 = message.mentions[0]
        user2 = message.mentions[1]

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

                await message.channel.send(
                    f"⏳ Espera {horas}h {minutos}m para votar otra vez."
                )
                return

        data[ship_key]["count"] += 1
        data[ship_key]["cooldowns"][author_id] = ahora

        with open("ships.json","w") as f:
            json.dump(data,f)

        canal = bot.get_channel(CANAL_REGISTRO)

        if canal:

            await canal.send(
                f"📌 Nuevo Ship\n{user1.mention} ❤️ {user2.mention}\nVotos: {data[ship_key]['count']}"
            )

        await message.add_reaction("❤️")

    # -------- IA SOLO EN CANAL IA --------

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

            await message.channel.send(
                f"{message.author.mention} {texto}"
            )

            if random.random() < 0.15:
                await message.channel.send(random.choice(BROMAS_BRANDON))

    await bot.process_commands(message)

# -------- RANKING SHIPS --------

@bot.command()
async def ranking(ctx):

    with open("ships.json","r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("No hay ships.")
        return

    sorted_ships = sorted(
        data.items(),
        key=lambda x:x[1]["count"],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 Ranking Ships",
        color=discord.Color.pink()
    )

    for i,(ship,info) in enumerate(sorted_ships[:10],1):

        ids = ship.split("-")

        user1 = await bot.fetch_user(int(ids[0]))
        user2 = await bot.fetch_user(int(ids[1]))

        embed.add_field(
            name=f"{i}. {user1.name} ❤️ {user2.name}",
            value=f"{info['count']} votos",
            inline=False
        )

    await ctx.send(embed=embed)

# -------- RESET SHIPS --------

@bot.command()
@commands.has_permissions(administrator=True)
async def resetships(ctx):

    with open("ships.json","w") as f:
        json.dump({},f)

    await ctx.send("✅ Los ships fueron reiniciados.")

bot.run(TOKEN)
