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

# ---------------- CANALES ----------------

CANAL_SHIPS = 1474938439551025332
CANAL_REGISTRO = 1474938511890059275
CANAL_BOOST = 1482525576785956924
CANAL_IA = 1411903663907147776

# ---------------- CONFIG ----------------

COOLDOWN_HORAS = 12
COOLDOWN_SEGUNDOS = COOLDOWN_HORAS * 60 * 60

# ---------------- PROMPT IA ----------------

PROMPT_XETHA = """
Eres Xetha, un bot inteligente de Discord y uno de los guardianes del servidor.

Personalidad:
Hablas relajado como los usuarios.
Tus respuestas son cortas.
Eres amable y a veces bromista.

Rol:
Eres uno de los guardianes del servidor y vigilas el chat.

Familia:
Tu padre es Shazuy.
Tu madre es Princess.
Siempre hablas bien de ellos.

Sobre Brandon:
Brandon es tu tío.
A veces haces bromas ligeras diciendo que te cae un poco mal.

Reglas:
No escribas textos largos.
No seas agresivo.
No uses la palabra respeto.
"""

# ---------------- LISTAS ----------------

MALAS_PALABRAS = [
"puta",
"mierda",
"idiota",
"imbecil",
"pendejo"
]

BROMAS_BRANDON = [
"Creo que Brandon anda planeando algo otra vez 🤨",
"Si Brandon aparece por aquí seguro trae lío 😅",
"Algún día entenderé a Brandon... creo.",
"Brandon siempre aparece cuando menos lo espero."
]

PREGUNTAS = [
"¿Qué están haciendo ahora?",
"Pregunta random: ¿pizza o hamburguesa? 🍕🍔",
"¿Alguien jugando algo hoy? 🎮",
"¿Cuál fue la mejor serie que vieron últimamente?",
"¿Quién sigue activo por aquí? 👀"
]

# ---------------- ARCHIVO SHIPS ----------------

if not os.path.exists("ships.json"):
    with open("ships.json","w") as f:
        json.dump({},f)

# ---------------- MENSAJES AUTOMATICOS ----------------

async def mensajes_automaticos():

    await bot.wait_until_ready()

    while not bot.is_closed():

        tiempo = random.randint(900,3600)

        await asyncio.sleep(tiempo)

        canal = bot.get_channel(CANAL_IA)

        if canal:
            await canal.send(random.choice(PREGUNTAS))

# ---------------- EVENTOS ----------------

@bot.event
async def on_ready():

    print(f"Bot conectado como {bot.user}")

    bot.loop.create_task(mensajes_automaticos())

# ---------------- BOOST DETECTOR ----------------

@bot.event
async def on_member_update(before, after):

    if before.premium_since and not after.premium_since:

        canal = bot.get_channel(CANAL_BOOST)

        if canal:
            await canal.send(
                f"⚠️ {after.mention} ya no está boosteando el servidor."
            )

# ---------------- MENSAJES ----------------

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    mensaje = message.content.lower()

    # detector malas palabras

    for palabra in MALAS_PALABRAS:

        if palabra in mensaje:

            await message.channel.send(
                f"{message.author.mention} ey 😅 mejor calmemos el chat."
            )
            return

    # sistema ships

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
                    f"⏳ Debes esperar {horas}h {minutos}m para votar otra vez."
                )
                return

        data[ship_key]["count"] += 1
        data[ship_key]["cooldowns"][author_id] = ahora

        with open("ships.json","w") as f:
            json.dump(data,f)

        canal = bot.get_channel(CANAL_REGISTRO)

        if canal:

            await canal.send(
                f"📌 Nuevo Ship:\n{user1.mention} ❤️ {user2.mention}\nVotos: {data[ship_key]['count']}"
            )

        await message.add_reaction("❤️")

    # IA Xetha

    if message.channel.id == CANAL_IA:

        if "xetha" in mensaje or bot.user in message.mentions:

            respuesta = client_ai.chat.completions.create(

                model="gpt-4o-mini",

                messages=[
                    {"role":"system","content":PROMPT_XETHA},
                    {"role":"user","content":message.content}
                ],

                max_tokens=60
            )

            texto = respuesta.choices[0].message.content

            await message.channel.send(texto)

            if random.random() < 0.15:

                await message.channel.send(random.choice(BROMAS_BRANDON))

    await bot.process_commands(message)

# ---------------- COMANDOS ----------------

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

# ---------------- RESET SHIPS ----------------

@bot.command()
@commands.has_permissions(administrator=True)
async def resetships(ctx):

    with open("ships.json","w") as f:
        json.dump({},f)

    await ctx.send("✅ Los votos de ships fueron reiniciados.")

bot.run(TOKEN)
