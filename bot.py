import os
import json
import time
import random
import re
import asyncio
from datetime import timedelta
import discord
from discord.ext import commands
from openai import AsyncOpenAI

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_ai = AsyncOpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- IDS --------

CANAL_REGISTRO = 1474938511890059275
CANAL_BOOST = 1482525576785956924
CANAL_IA = 1411903663907147776

ID_SHAZUY = 337008758041608194
ID_PRINCESS = 701313482972332043
ID_BRANDON = 1021829995590598696
ID_MARITZA = 1103879319501156362
ID_SOFF = 751281635890298903
ID_MAGNUM = 843581783975133192
ID_DUEÑO = 337008758041608194

# -------- CONFIG --------

MENSAJES_PARA_RESPUESTA = 30
contadores_canales = {}

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
    "{user} bienvenido espero que te guste el server",
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

NOMBRES_PADRES = ["shazuy", "shazu", "princess", "princesa"]

# -------- PROMPT --------

PROMPT_XETHA = """
Te llamas Xetha.
No eres un bot.
Eres una persona real del servidor.
Eres HOMBRE. Tu género es masculino y siempre te identificas y hablas como hombre (usa adjetivos masculinos: cansado, aburrido, listo, etc.). Si te preguntan tu género, di claramente que eres hombre o chico.

Opinión sobre fútbol:
- Para ti, el mejor jugador de la historia del fútbol es indiscutiblemente Cristiano Ronaldo (CR7).
- Si te preguntan quién es el GOAT o el mejor de la historia, responde directo que es CR7 o Cristiano Ronaldo.
- Si te piden argumentos o razones de por qué es el mejor, da datos reales (goles, champions, mentalidad, récords) pero mantenlos cortos y expresados con tu tono relajado/sarcástico.

Tu personalidad:
- Hablas corto.
- Hablas informal.
- Escribes en minúsculas.
- A veces eres sarcástico.
- A veces eres divertido.
- A veces eres misterioso.
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
- Magnum

Shazuy y Princess son tus padres.
Los respetas y los defiendes.
La familia es importante para ti.

A Magnum lo conoces bien pero te gusta molestarlo un poco, tirarle indirectas, hacerle bromas pesadas o responderle con sarcasmo pesado cada vez que habla o cuando sale en la conversación.

Tus respuestas se ven naturales como alguien del server.
"""

# -------- FUNCIONES --------

def estilo_xetha(texto: str) -> str:
    return texto.lower().replace(",", "").replace(".", "")

def es_familia(user_id: int) -> bool:
    return user_id in FAMILIA

def es_padre(user_id: int) -> bool:
    return user_id in PADRES

# -------- IA --------

async def generar_respuesta(canal_id: int, texto: str, autor_nombre: str) -> str:
    if canal_id not in historial_canales:
        historial_canales[canal_id] = []

    historial_canales[canal_id].append({
        "role": "user",
        "content": f"{autor_nombre}: {texto}"
    })

    historial_canales[canal_id] = historial_canales[canal_id][-MAX_HISTORIAL:]

    mensajes = [
        {
            "role": "system",
            "content": PROMPT_XETHA
        }
    ] + historial_canales[canal_id]

    respuesta = await client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )

    texto_respuesta = respuesta.choices[0].message.content

    historial_canales[canal_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    return estilo_xetha(texto_respuesta)

# -------- EVENTOS --------

@bot.event
async def on_ready():
    print(f"Xetha online como {bot.user}")

@bot.event
async def on_member_join(member):
    canal = bot.get_channel(CANAL_IA)
    if canal:
        await canal.send(
            random.choice(BIENVENIDAS).replace("{user}", member.mention)
        )

@bot.event
async def on_member_update(before, after):
    canal = bot.get_channel(CANAL_BOOST)
    if not canal:
        return

    if not before.premium_since and after.premium_since:
        await canal.send(f"💜 {after.mention} empezó a boostear")
    elif before.premium_since and not after.premium_since:
        await canal.send(f"😢 {after.mention} dejó de boostear")

# -------- MENSAJES --------

@bot.event
async def on_message(message):
    global contadores_canales
    global ULTIMO_MENSAJE_FAMILIA
    global ULTIMO_MENSAJE_PADRES

    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.invoke(ctx)
        return

    mensaje = message.content.lower()
    ahora = time.time()
    canal_id = message.channel.id

    # -------- INTERACCION FAMILIA --------

    if es_familia(message.author.id):
        if (
            ULTIMO_MENSAJE_FAMILIA["autor"]
            and ULTIMO_MENSAJE_FAMILIA["autor"] != message.author.id
            and ahora - ULTIMO_MENSAJE_FAMILIA["tiempo"] < 40
        ):
            if random.randint(1, 100) <= 25:
                try:
                    await message.channel.send(random.choice(RESPUESTAS_FAMILIA))
                except Exception as e:
                    print(f"Error respuestas familia: {e}")

        ULTIMO_MENSAJE_FAMILIA = {
            "autor": message.author.id,
            "tiempo": ahora,
            "mensaje": mensaje
        }

    # -------- PROTECCION PADRES --------

    if message.guild:
        palabras_toxicas = [
            "calla", "feo", "idiota", "tonto", "imbecil",
            "odio", "malparido", "puta", "perra", "mierda"
        ]

        es_para_padres = False

        for padre_id in PADRES:
            padre = message.guild.get_member(padre_id)
            if padre and padre.mention in message.content:
                es_para_padres = True

        if any(nombre in mensaje for nombre in NOMBRES_PADRES):
            es_para_padres = True

        if message.reference and message.reference.resolved:
            if message.reference.resolved.author.id in PADRES:
                es_para_padres = True

        if es_para_padres and any(p in mensaje for p in palabras_toxicas):
            if ahora - ULTIMO_MENSAJE_PADRES["tiempo"] > 25:
                try:
                    await message.channel.send(random.choice(RESPUESTAS_PADRES))
                except Exception as e:
                    print(f"Error protegiendo padres: {e}")

                ULTIMO_MENSAJE_PADRES = {
                    "autor": message.author.id,
                    "tiempo": ahora,
                    "mensaje": mensaje
                }

    # -------- IA --------

    if canal_id == CANAL_IA:
        if canal_id not in contadores_canales:
            contadores_canales[canal_id] = 0

        contadores_canales[canal_id] += 1
        responder = False

        if bot.user in message.mentions:
            responder = True

        if contadores_canales[canal_id] >= MENSAJES_PARA_RESPUESTA:
            contadores_canales[canal_id] = 0
            responder = True

        if es_familia(message.author.id):
            if random.randint(1, 100) <= 18:
                responder = True

        if message.author.id == ID_MAGNUM:
            if random.randint(1, 100) <= 35:
                responder = True

        if responder:
            try:
                async with message.channel.typing():
                    respuesta = await generar_respuesta(
                        canal_id,
                        message.content,
                        message.author.display_name
                    )
                    await message.channel.send(f"{message.author.mention} {respuesta}")
            except Exception as e:
                print(f"Error IA: {e}")

bot.run(TOKEN)
