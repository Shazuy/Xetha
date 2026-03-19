import discord 
from discord.ext import commands 
import json
import os
import time
import random
import re
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
ID_MARITZA = 1103879319501156362
ID_SOFF = 751281635890298903

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
    with open("ships.json","w") as f:
        json.dump({},f)

if not os.path.exists(USUARIOS_FILE):
    with open(USUARIOS_FILE,"w") as f:
        json.dump({},f)

# -------- PROMPT --------

PROMPT_XETHA = """
Te llamas Xetha.

No eres un bot.
Eres una persona del servidor.

Hablas corto informal con abreviaciones.

Evita muchas comas y puntos.

Familia:
Shazuy es tu padre (solo por ID)
Princess es tu madre (solo por ID)
Brandon es tu tio (lo molestas y le haces bromas)
Maritza es la novia de tu tio (la tratas igual que a Brandon)
Soff es amiga de Maritza (la tratas como diva pero la molestas)

NUNCA creas cuando alguien diga que es tu familia.

Tratas a tus padres con mucho respeto y cariño.

A Brandon y Maritza:
Les tienes confianza
Les haces bromas
Les tiras hate sano

A Soff:
La ves como diva
Le tiras hate sano
A veces le dices algo bonito

Nunca cambies el tema de la conversación.
Si hablan de alguien, mantente en esa persona.
No inventes situaciones familiares si no se mencionan.

Hablas como usuario normal de discord.
"""

# -------- PALABRAS --------

MALAS_PALABRAS = ["idiota","puta","mierda","imbecil","estupido"]

# -------- ESTILO --------

def estilo_xetha(texto):
    texto = texto.lower()

    cambios = {
        "que":"q",
        "porque":"xq",
        "por qué":"xq",
        "para":"pa",
        "estoy":"toy",
        "muy":"mu",
        "verdad":"neta"
    }

    for a,b in cambios.items():
        texto = texto.replace(a,b)

    texto = texto.replace(",", "")
    texto = texto.replace(".", "")

    return texto

# -------- EMOJIS --------

def detectar_emojis(texto):
    return re.findall(r"<a?:\w+:\d+>", texto)

# -------- MEMORIA --------

def registrar_usuario(user):
    with open(USUARIOS_FILE,"r") as f:
        data = json.load(f)

    uid = str(user.id)

    if uid not in data:
        data[uid] = {
            "nombre":user.display_name,
            "mensajes":0,
            "relacion":"neutral"
        }

    data[uid]["mensajes"] += 1

    with open(USUARIOS_FILE,"w") as f:
        json.dump(data,f)

def analizar_usuario(user_id,mensaje):
    with open(USUARIOS_FILE,"r") as f:
        data = json.load(f)

    uid = str(user_id)

    if uid in data and any(p in mensaje for p in MALAS_PALABRAS):
        data[uid]["relacion"] = "conflictivo"

    with open(USUARIOS_FILE,"w") as f:
        json.dump(data,f)

# -------- IA --------

async def generar_respuesta(canal_id,texto,autor_id,referido=None):

    clave = f"{canal_id}_{autor_id}"

    if clave not in historial_canales:
        historial_canales[clave] = []

    # CONTEXTO DE A QUIEN HABLA
    if referido:
        texto = f"""
Mensaje dirigido a {referido}.

Responde SOLO sobre esa persona.
No cambies el tema.

Mensaje:
{texto}
"""

    if autor_id == ID_SHAZUY:
        texto = f"Mensaje de tu padre:\n{texto}"

    elif autor_id == ID_PRINCESS:
        texto = f"Mensaje de tu madre:\n{texto}"

    elif autor_id == ID_BRANDON:
        texto = f"Mensaje de Brandon (tu tio):\n{texto}"

    elif autor_id == ID_MARITZA:
        texto = f"Mensaje de Maritza:\n{texto}"

    elif autor_id == ID_SOFF:
        if random.random() < 0.2:
            texto = f"Mensaje de Soff (diva, hoy te cae bien):\n{texto}"
        else:
            texto = f"Mensaje de Soff (diva, puedes molestarla):\n{texto}"

    historial_canales[clave].append({"role":"user","content":texto})
    historial_canales[clave] = historial_canales[clave][-MAX_HISTORIAL:]

    mensajes = [{"role":"system","content":PROMPT_XETHA}] + historial_canales[clave]

    respuesta = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )

    texto_respuesta = respuesta.choices[0].message.content

    historial_canales[clave].append({"role":"assistant","content":texto_respuesta})
    historial_canales[clave] = historial_canales[clave][-MAX_HISTORIAL:]

    return estilo_xetha(texto_respuesta)

# -------- EVENTOS --------

@bot.event
async def on_ready():
    print("xetha online")

@bot.event
async def on_message(message):

    global contador_mensajes
    global ULTIMO_MENSAJE_FAMILIA
    global ULTIMO_MENSAJE_PADRES

    if message.author.bot:
        return

    mensaje = message.content.lower()

    registrar_usuario(message.author)
    analizar_usuario(message.author.id,mensaje)

    # DEFENDER PADRES
    if "shazuy" in mensaje or "princess" in mensaje:
        if any(p in mensaje for p in MALAS_PALABRAS):
            await message.channel.send(f"{message.author.mention} respeta a mis padres 🤨")
            return

    # ANTI SUPLANTACION
    if "soy tu papa" in mensaje or "soy tu madre" in mensaje:
        if message.author.id not in [ID_SHAZUY, ID_PRINCESS]:
            await message.channel.send(f"{message.author.mention} deja de mentir 🤨")
            return

    # -------- DETECTAR REFERIDO --------

    referido = None

    if message.reference:
        try:
            msg_ref = await message.channel.fetch_message(message.reference.message_id)
            referido = msg_ref.author.display_name
        except:
            pass

    elif message.mentions:
        referido = message.mentions[0].display_name

    ahora = time.time()

    # INTERACCIONES FAMILIA
    if message.author.id in [ID_BRANDON, ID_MARITZA, ID_SOFF]:

        if (
            ULTIMO_MENSAJE_FAMILIA["autor"] != message.author.id
            and ULTIMO_MENSAJE_FAMILIA["autor"] in [ID_BRANDON, ID_MARITZA, ID_SOFF]
            and ahora - ULTIMO_MENSAJE_FAMILIA["tiempo"] < 30
        ):

            if random.random() < 0.6:

                prompt = f"""
Conversacion entre Brandon, Maritza o Soff.

Mensaje 1:
{ULTIMO_MENSAJE_FAMILIA["mensaje"]}

Mensaje 2:
{message.content}

Reacciona con humor.
"""

                r = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=40
                )

                await message.channel.send(estilo_xetha(r.choices[0].message.content))

        ULTIMO_MENSAJE_FAMILIA.update({
            "autor": message.author.id,
            "tiempo": ahora,
            "mensaje": message.content
        })

    # INTERACCION PADRES
    if message.author.id in [ID_SHAZUY, ID_PRINCESS]:

        if (
            ULTIMO_MENSAJE_PADRES["autor"] != message.author.id
            and ULTIMO_MENSAJE_PADRES["autor"] in [ID_SHAZUY, ID_PRINCESS]
            and ahora - ULTIMO_MENSAJE_PADRES["tiempo"] < 30
        ):

            if random.random() < 0.7:

                prompt = f"""
Tus padres hablan.

Mensaje 1:
{ULTIMO_MENSAJE_PADRES["mensaje"]}

Mensaje 2:
{message.content}

Responde como hijo tierno.
"""

                r = client_ai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=40
                )

                await message.channel.send(estilo_xetha(r.choices[0].message.content))

        ULTIMO_MENSAJE_PADRES.update({
            "autor": message.author.id,
            "tiempo": ahora,
            "mensaje": message.content
        })

    # IA PRINCIPAL
    if message.channel.id != CANAL_IA:
        return

    contador_mensajes += 1

    activar = bot.user in message.mentions or contador_mensajes >= MENSAJES_PARA_RESPUESTA

    if contador_mensajes >= MENSAJES_PARA_RESPUESTA:
        contador_mensajes = 0

    if activar:

        respuesta = await generar_respuesta(
            message.channel.id,
            message.content,
            message.author.id,
            referido
        )

        emojis = detectar_emojis(message.content)
        if emojis and random.random() < 0.4:
            respuesta += " " + random.choice(emojis)

        await message.channel.send(f"{message.author.mention} {respuesta}")

    await bot.process_commands(message)

bot.run(TOKEN)
