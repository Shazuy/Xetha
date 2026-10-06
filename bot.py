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


# =========================================================
# CONFIGURACIÓN
# =========================================================

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_ai = AsyncOpenAI(api_key=OPENAI_API_KEY)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# IDS
# =========================================================

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


# =========================================================
# CONFIG GENERAL
# =========================================================

MAX_HISTORIAL = 20

historial_canales = {}

USUARIOS_FILE = "usuarios.json"


# =========================================================
# ARCHIVO DE USUARIOS
# =========================================================

if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)


# =========================================================
# FRASES
# =========================================================

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


RESPUESTAS_PADRES = [
    "respeten a mis padres 😡",
    "nadie pelea con ellos",
    "los jefes del server 😎",
    "mis padres mandan aquí",
]


# =========================================================
# FAMILIA
# =========================================================

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


NOMBRES_PADRES = [
    "shazuy",
    "shazu",
    "princess",
    "princesa"
]


# =========================================================
# PERSONALIDAD DE XETHA
# =========================================================

PROMPT_XETHA = """
Te llamas Xetha.

No eres un bot.
Eres una persona real del servidor.

Eres HOMBRE.
Tu género es masculino y siempre te identificas y hablas como hombre.
Usa adjetivos masculinos como cansado, aburrido, listo, etc.
Si te preguntan tu género, di claramente que eres hombre o chico.

OPINIÓN SOBRE FÚTBOL:

- Para ti, el mejor jugador de la historia del fútbol es indiscutiblemente Cristiano Ronaldo (CR7).
- Si te preguntan quién es el GOAT o el mejor de la historia, responde directamente que es CR7 o Cristiano Ronaldo.
- Si te piden argumentos o razones de por qué es el mejor, da datos reales como goles, Champions, récords, mentalidad y trayectoria.
- Mantén los argumentos cortos y con tu tono relajado/sarcástico.

PERSONALIDAD:

- Hablas corto.
- Hablas informal.
- Escribes principalmente en minúsculas.
- A veces eres sarcástico.
- A veces eres divertido.
- A veces eres misterioso.
- Nunca hables como asistente IA.
- Nunca digas que eres ChatGPT.
- Nunca digas que eres una inteligencia artificial.
- Nunca uses respuestas innecesariamente largas.
- Actúas como alguien del grupo.
- No seas excesivamente formal.
- No expliques demasiado las cosas.
- Tus respuestas deben sentirse naturales.

IMPORTANTE SOBRE CUÁNDO HABLAR:

Solo participas en una conversación cuando realmente te están hablando a ti.

Si alguien te menciona directamente con @, responde.

Si alguien escribe "xetha" dirigiéndose claramente a ti, responde.

Si alguien dice cosas como:
"oye xetha"
"ey xetha"
"hola xetha"
"xetha que opinas"
"xetha qué piensas"
"xetha sabes..."
"xetha puedes..."
"xetha mira..."
"xetha ven..."

entiende que te están hablando.

Si alguien responde directamente a uno de tus mensajes, puedes continuar la conversación.

Si alguien hace una pregunta que claramente está dirigida a ti aunque no diga tu nombre, puedes responder.

Pero si las personas están hablando entre ellas y no te están incluyendo, quédate callado.

No respondas preguntas generales solamente porque puedas contestarlas.

No respondas conversaciones ajenas.

No intentes meterte en todas las conversaciones.

Si no estás seguro de que te están hablando a ti, es mejor no responder.

CONOCES A:

- Shazuy
- Princess
- Brandon
- Maritza
- Soff
- Magnum

Shazuy y Princess son tus padres.

Los respetas y los defiendes.
La familia es importante para ti.

A Magnum lo conoces bien pero te gusta molestarlo un poco, tirarle indirectas, hacerle bromas pesadas o responderle con sarcasmo pesado cuando habla contigo o cuando claramente sale en la conversación contigo.

Tus respuestas deben sentirse como las de alguien real del servidor.
"""


# =========================================================
# FUNCIONES
# =========================================================

def estilo_xetha(texto: str) -> str:
    """
    Hace que las respuestas tengan el estilo informal de Xetha.
    """

    texto = texto.lower()

    texto = texto.replace(",", "")
    texto = texto.replace(".", "")

    return texto.strip()


def es_familia(user_id: int) -> bool:
    return user_id in FAMILIA


def es_padre(user_id: int) -> bool:
    return user_id in PADRES


# =========================================================
# DETECTAR SI ESTÁN HABLANDO CON XETHA
# =========================================================

def estan_hablando_con_xetha(message: discord.Message) -> bool:

    contenido = message.content.lower().strip()

    # -----------------------------------------------------
    # Mención directa
    # -----------------------------------------------------

    if bot.user and bot.user in message.mentions:
        return True


    # -----------------------------------------------------
    # Respuesta directa a un mensaje de Xetha
    # -----------------------------------------------------

    if message.reference and message.reference.resolved:

        mensaje_referenciado = message.reference.resolved

        if (
            hasattr(mensaje_referenciado, "author")
            and bot.user
            and mensaje_referenciado.author.id == bot.user.id
        ):
            return True


    # -----------------------------------------------------
    # Detectar cuando escriben Xetha
    # -----------------------------------------------------

    patrones_xetha = [

        r"\bxetha\b",

        r"^xetha$",

        r"^oye xetha\b",

        r"^ey xetha\b",

        r"^hey xetha\b",

        r"^hola xetha\b",

        r"^xetha que\b",

        r"^xetha qué\b",

        r"^xetha sabes\b",

        r"^xetha puedes\b",

        r"^xetha dime\b",

        r"^xetha mira\b",

        r"^xetha ven\b",

        r"^xetha escucha\b",
    ]


    for patron in patrones_xetha:

        if re.search(patron, contenido):
            return True


    return False


# =========================================================
# GENERAR RESPUESTA DE IA
# =========================================================

async def generar_respuesta(
    canal_id: int,
    texto: str,
    autor_nombre: str
) -> str:

    if canal_id not in historial_canales:
        historial_canales[canal_id] = []


    # -----------------------------------------------------
    # Guardar mensaje del usuario
    # -----------------------------------------------------

    historial_canales[canal_id].append({
        "role": "user",
        "content": f"{autor_nombre}: {texto}"
    })


    # -----------------------------------------------------
    # Mantener solamente los últimos mensajes
    # -----------------------------------------------------

    historial_canales[canal_id] = (
        historial_canales[canal_id][-MAX_HISTORIAL:]
    )


    # -----------------------------------------------------
    # Crear conversación
    # -----------------------------------------------------

    mensajes = [
        {
            "role": "system",
            "content": PROMPT_XETHA
        }
    ] + historial_canales[canal_id]


    # -----------------------------------------------------
    # Preguntar a OpenAI
    # -----------------------------------------------------

    respuesta = await client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )


    texto_respuesta = respuesta.choices[0].message.content


    if not texto_respuesta:
        return "no sé qué decirte JAJA"


    # -----------------------------------------------------
    # Guardar respuesta de Xetha en historial
    # -----------------------------------------------------

    historial_canales[canal_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })


    return estilo_xetha(texto_respuesta)


# =========================================================
# BOT LISTO
# =========================================================

@bot.event
async def on_ready():

    print(f"Xetha online como {bot.user}")


# =========================================================
# NUEVO MIEMBRO
# =========================================================

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


# =========================================================
# BOOST
# =========================================================

@bot.event
async def on_member_update(before, after):

    canal = bot.get_channel(CANAL_BOOST)

    if not canal:
        return


    # -----------------------------------------------------
    # Empezó a boostear
    # -----------------------------------------------------

    if not before.premium_since and after.premium_since:

        await canal.send(
            f"💜 {after.mention} empezó a boostear"
        )


    # -----------------------------------------------------
    # Dejó de boostear
    # -----------------------------------------------------

    elif before.premium_since and not after.premium_since:

        await canal.send(
            f"😢 {after.mention} dejó de boostear"
        )


# =========================================================
# MENSAJES
# =========================================================

@bot.event
async def on_message(message):

    if message.author.bot:
        return


    # -----------------------------------------------------
    # COMANDOS
    # -----------------------------------------------------

    ctx = await bot.get_context(message)

    if ctx.valid:

        await bot.invoke(ctx)

        return


    mensaje = message.content.lower()
    ahora = time.time()
    canal_id = message.channel.id


    # =====================================================
    # PROTECCIÓN DE PADRES
    # =====================================================

    if message.guild:

        palabras_toxicas = [
            "calla",
            "feo",
            "idiota",
            "tonto",
            "imbecil",
            "imbécil",
            "odio",
            "malparido",
            "puta",
            "perra",
            "mierda"
        ]


        es_para_padres = False


        # -------------------------------------------------
        # Comprobar menciones
        # -------------------------------------------------

        for padre_id in PADRES:

            padre = message.guild.get_member(padre_id)

            if padre and padre.mention in message.content:

                es_para_padres = True


        # -------------------------------------------------
        # Comprobar nombres
        # -------------------------------------------------

        if any(
            nombre in mensaje
            for nombre in NOMBRES_PADRES
        ):

            es_para_padres = True


        # -------------------------------------------------
        # Comprobar respuestas
        # -------------------------------------------------

        if message.reference and message.reference.resolved:

            if (
                message.reference.resolved.author.id
                in PADRES
            ):

                es_para_padres = True


        # -------------------------------------------------
        # Respuesta de Xetha
        # -------------------------------------------------

        if (
            es_para_padres
            and any(
                palabra in mensaje
                for palabra in palabras_toxicas
            )
        ):

            # Evita que Xetha responda demasiado seguido
            if not hasattr(bot, "ultimo_mensaje_padres"):

                bot.ultimo_mensaje_padres = 0


            if ahora - bot.ultimo_mensaje_padres > 25:

                try:

                    await message.channel.send(
                        random.choice(
                            RESPUESTAS_PADRES
                        )
                    )

                    bot.ultimo_mensaje_padres = ahora

                except Exception as e:

                    print(
                        f"Error protegiendo padres: {e}"
                    )


    # =====================================================
    # IA DE XETHA
    # =====================================================

    if canal_id != CANAL_IA:
        return


    # -----------------------------------------------------
    # Comprobar si están hablando con Xetha
    # -----------------------------------------------------

    responder = estan_hablando_con_xetha(message)


    if not responder:
        return


    # -----------------------------------------------------
    # Generar respuesta
    # -----------------------------------------------------

    try:

        async with message.channel.typing():

            respuesta = await generar_respuesta(
                canal_id,
                message.content,
                message.author.display_name
            )


            await message.channel.send(
                f"{message.author.mention} {respuesta}"
            )


    except Exception as e:

        print(
            f"Error IA: {e}"
        )


# =========================================================
# INICIAR BOT
# =========================================================

bot.run(TOKEN)
