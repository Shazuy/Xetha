import discord
from discord.ext import commands
import json
import os
import time
import random
import re
import asyncio
from datetime import timedelta
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
CANAL_COMANDOS = 1474938628273737728

ID_SHAZUY = 337008758041608194
ID_PRINCESS = 701313482972332043
ID_BRANDON = 1021829995590598696
ID_MARITZA = 1103879319501156362
ID_SOFF = 751281635890298903
ID_DUEÑO = 337008758041608194

# -------- CONFIG --------

MENSAJES_PARA_RESPUESTA = 30
contador_mensajes = 0

MAX_HISTORIAL = 20
historial_canales = {}

USUARIOS_FILE = "usuarios.json"

ULTIMO_MENSAJE_FAMILIA = {
    "autor": None,
    "tiempo": 0,
    "mensaje": ""
}

ULTIMO_MENSAJE_PADRES = {
    "autor": None,
    "tiempo": 0,
    "mensaje": ""
}

# -------- ARCHIVOS --------

if not os.path.exists("ships.json"):
    with open("ships.json", "w") as f:
        json.dump({}, f)

if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w") as f:
        json.dump({}, f)

# -------- FRASES --------

MANIPULACIONES = [
    "todos digan quien es el mas raro del server 💀",
    "voten quien cae peor 😈",
    "quien tiene mas ego aqui 🤨",
]

SECRETOS = [
    "sé algo de {user} pero mejor no digo nada…",
    "{user} tú sabes lo que hiciste 😈",
    "alguien aquí está ocultando algo…",
]

BIENVENIDAS = [
    "bienvenido {user} pásala bien por aquí 😎",
    "{user} bienvenido al server cualquier cosa pregunta",
    "ey {user} bienvenido espero que te guste el server",
]

RESPUESTAS_FAMILIA = [
    "q hacen 😭",
    "otra vez ustedes JAJA",
    "la familia anda activa hoy",
    "ustedes nunca duermen o qué",
    "ya empezaron 😭"
]

RESPUESTAS_PADRES = [
    "respeten a mis padres 😡",
    "nadie pelea con ellos",
    "los jefes del server 😎",
    "mis padres mandan aquí",
]

# -------- FAMILIA --------

FAMILIA = {
    ID_SHAZUY: "shazuy",
    ID_PRINCESS: "princess",
    ID_BRANDON: "brandon",
    ID_MARITZA: "maritza",
    ID_SOFF: "soff"
}

PADRES = [
    ID_SHAZUY,
    ID_PRINCESS
]

# -------- PROMPT --------

PROMPT_XETHA = """
Te llamas Xetha.
No eres un bot.
Eres una persona real del servidor.

Tu personalidad:
- Hablas corto.
- Hablas informal.
- Escribes en minúsculas.
- A veces eres sarcástica.
- A veces eres divertida.
- A veces eres misteriosa.
- Nunca hables como asistente IA.
- Nunca digas que eres ChatGPT.
- Nunca uses respuestas largas.
- Actúas como alguien del grupo.

Conoces a:
- Shazuy
- Princess
- Brandon
- Maritza
- Soff

Shazuy y Princess son tus padres.
Los respetas y los defiendes.
La familia es importante para ti.

A veces haces:
- bromas
- comentarios random
- manipulación social ligera
- mensajes misteriosos
- sarcasmo

Tus respuestas se ven naturales como alguien del server.
"""

# -------- FUNCIONES --------

def estilo_xetha(texto):
    return texto.lower().replace(",", "").replace(".", "")

def detectar_emojis(texto):
    return re.findall(r"<a?:\w+:\d+>", texto)

def obtener_usuario_random(guild):
    miembros = [m for m in guild.members if not m.bot]
    return random.choice(miembros) if miembros else None

def es_familia(user_id):
    return user_id in FAMILIA

def es_padre(user_id):
    return user_id in PADRES

def votar_ship(user1, user2, autor):

    key = "_".join(sorted([str(user1.id), str(user2.id)]))

    with open("ships.json", "r") as f:
        data = json.load(f)

    if key not in data:
        data[key] = {
            "usuarios": [user1.display_name, user2.display_name],
            "votos": 0
        }

    data[key]["votos"] += 1
    votos = data[key]["votos"]

    with open("ships.json", "w") as f:
        json.dump(data, f, indent=4)

    canal_logs = bot.get_channel(CANAL_REGISTRO)

    if canal_logs:
        asyncio.create_task(
            canal_logs.send(
                f"💘 {autor.display_name} votó por {user1.display_name} ❤️ {user2.display_name} ({votos} votos)"
            )
        )

# -------- IA --------

async def generar_respuesta(canal_id, texto, autor_id):

    clave = f"{canal_id}_{autor_id}"

    if clave not in historial_canales:
        historial_canales[clave] = []

    historial_canales[clave].append({
        "role": "user",
        "content": texto
    })

    historial_canales[clave] = historial_canales[clave][-MAX_HISTORIAL:]

    mensajes = [
        {
            "role": "system",
            "content": PROMPT_XETHA
        }
    ] + historial_canales[clave]

    respuesta = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )

    texto_respuesta = respuesta.choices[0].message.content

    historial_canales[clave].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    return estilo_xetha(texto_respuesta)

# -------- COMANDO RANKS --------

@bot.command()
async def ranks(ctx):

    if ctx.channel.id != CANAL_COMANDOS:
        return await ctx.send("usa eso en el canal correcto 🤨")

    with open("ships.json", "r") as f:
        data = json.load(f)

    if not data:
        return await ctx.send("no hay votos aún 💀")

    ranking = sorted(
        data.items(),
        key=lambda x: x[1]["votos"],
        reverse=True
    )

    texto = "💘 top ships del server:\n\n"

    for i, (_, info) in enumerate(ranking[:10], start=1):

        u1, u2 = info["usuarios"]
        votos = info["votos"]

        texto += f"{i}. {u1} ❤️ {u2} — {votos} votos\n"

    await ctx.send(texto)

# -------- EVENTOS --------

@bot.event
async def on_ready():
    print("xetha online")

@bot.event
async def on_member_join(member):

    canal = bot.get_channel(CANAL_IA)

    if canal:
        await canal.send(
            random.choice(BIENVENIDAS).replace(
                "{user}",
                member.mention
            )
        )

@bot.event
async def on_member_update(before, after):

    canal = bot.get_channel(CANAL_BOOST)

    if not canal:
        return

    if not before.premium_since and after.premium_since:

        await canal.send(
            f"💜 {after.mention} empezó a boostear"
        )

    elif before.premium_since and not after.premium_since:

        await canal.send(
            f"😢 {after.mention} dejó de boostear"
        )

# -------- MENSAJES --------

@bot.event
async def on_message(message):

    global contador_mensajes
    global ULTIMO_MENSAJE_FAMILIA
    global ULTIMO_MENSAJE_PADRES

    if message.author.bot:
        return

    mensaje = message.content.lower()
    ahora = time.time()

    # -------- SHIPS --------

    if message.channel.id == CANAL_SHIPS:

        if len(message.mentions) >= 2:

            u1, u2 = message.mentions[:2]

            if not u1.bot and not u2.bot and u1 != u2:

                votar_ship(u1, u2, message.author)

                try:
                    await message.add_reaction("❤️")
                except:
                    pass

        elif " x " in mensaje:

            partes = mensaje.split(" x ")

            if len(partes) == 2:

                miembros = message.guild.members

                user1 = discord.utils.find(
                    lambda m: m.name.lower() == partes[0].strip(),
                    miembros
                )

                user2 = discord.utils.find(
                    lambda m: m.name.lower() == partes[1].strip(),
                    miembros
                )

                if user1 and user2 and user1 != user2:

                    votar_ship(user1, user2, message.author)

                    try:
                        await message.add_reaction("❤️")
                    except:
                        pass

        return

    # -------- INTERACCION FAMILIA --------

    if es_familia(message.author.id):

        if (
            ULTIMO_MENSAJE_FAMILIA["autor"]
            and ULTIMO_MENSAJE_FAMILIA["autor"] != message.author.id
            and ahora - ULTIMO_MENSAJE_FAMILIA["tiempo"] < 40
        ):

            if random.randint(1, 100) <= 25:

                try:
                    await message.channel.send(
                        random.choice(RESPUESTAS_FAMILIA)
                    )
                except:
                    pass

        ULTIMO_MENSAJE_FAMILIA = {
            "autor": message.author.id,
            "tiempo": ahora,
            "mensaje": mensaje
        }

    # -------- PROTECCION PADRES --------

    for padre_id in PADRES:

        padre = message.guild.get_member(padre_id)

        if not padre:
            continue

        if padre.mention in message.content:

            palabras_toxicas = [
                "calla",
                "feo",
                "idiota",
                "tonto",
                "imbecil",
                "odio",
                "malparido",
                "puta",
                "perra",
                "mierda"
            ]

            if any(p in mensaje for p in palabras_toxicas):

                if ahora - ULTIMO_MENSAJE_PADRES["tiempo"] > 25:

                    try:
                        await message.channel.send(
                            random.choice(RESPUESTAS_PADRES)
                        )
                    except:
                        pass

                    ULTIMO_MENSAJE_PADRES = {
                        "autor": message.author.id,
                        "tiempo": ahora,
                        "mensaje": mensaje
                    }

    # -------- IA --------

    if message.channel.id == CANAL_IA:

        contador_mensajes += 1

        if contador_mensajes >= MENSAJES_PARA_RESPUESTA:
            contador_mensajes = 0

        responder = False

        if bot.user in message.mentions:
            responder = True

        if contador_mensajes == 0:
            responder = True

        if es_familia(message.author.id):

            if random.randint(1, 100) <= 18:
                responder = True

        if responder:

            respuesta = await generar_respuesta(
                message.channel.id,
                message.content,
                message.author.id
            )

            try:
                await message.channel.send(
                    f"{message.author.mention} {respuesta}"
                )
            except:
                pass

    await bot.process_commands(message)

bot.run(TOKEN)
