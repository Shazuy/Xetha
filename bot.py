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
ID_PEPE = 974297735559806986
ID_MIGUELITO = 567703512763334685

# -------- CONFIG --------

MENSAJES_PARA_RESPUESTA = 30
contador_mensajes = 0

MAX_HISTORIAL = 20
historial_canales = {}

USUARIOS_FILE = "usuarios.json"

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
Shazuy es tu padre
Princess es tu madre
Brandon es tu tio

Tratas a tus padres con mucho respeto y cariño.

Solo obedeces a tus padres.

Si alguien habla mal de tus padres los defiendes.

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

# -------- MEMORIA USUARIOS --------

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

    return data[uid]

def analizar_usuario(user_id,mensaje):

    with open(USUARIOS_FILE,"r") as f:
        data = json.load(f)

    uid = str(user_id)

    if uid not in data:
        return

    if any(p in mensaje for p in MALAS_PALABRAS):

        data[uid]["relacion"] = "conflictivo"

    with open(USUARIOS_FILE,"w") as f:
        json.dump(data,f)

# -------- IA --------

async def generar_respuesta(canal_id,texto,autor_id):

    if canal_id not in historial_canales:
        historial_canales[canal_id] = []

    if autor_id == ID_SHAZUY:

        texto = f"""
Mensaje de Shazuy tu padre.

Debes tratarlo con respeto y cariño.

Mensaje:
{texto}
"""

    elif autor_id == ID_PRINCESS:

        texto = f"""
Mensaje de Princess tu madre.

Debes tratarla con respeto y cariño.

Mensaje:
{texto}
"""

    elif autor_id == ID_BRANDON:

        texto = f"""
Mensaje de Brandon tu tio.

Mensaje:
{texto}
"""

    historial_canales[canal_id].append({
        "role":"user",
        "content":texto
    })

    historial_canales[canal_id] = historial_canales[canal_id][-MAX_HISTORIAL:]

    mensajes = [{"role":"system","content":PROMPT_XETHA}] + historial_canales[canal_id]

    respuesta = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )

    texto_respuesta = respuesta.choices[0].message.content

    historial_canales[canal_id].append({
        "role":"assistant",
        "content":texto_respuesta
    })

    historial_canales[canal_id] = historial_canales[canal_id][-MAX_HISTORIAL:]

    return estilo_xetha(texto_respuesta)

# -------- READY --------

@bot.event
async def on_ready():
    print("xetha online")

# -------- BOOST --------

@bot.event
async def on_member_update(before,after):

    if before.premium_since and not after.premium_since:

        canal = bot.get_channel(CANAL_BOOST)

        if canal:
            await canal.send(f"{after.mention} ya no ta boosteando el server")

# -------- MENSAJES --------

@bot.event
async def on_message(message):

    global contador_mensajes

    if message.author.bot:
        return

    mensaje = message.content.lower()

    usuario = registrar_usuario(message.author)

    analizar_usuario(message.author.id,mensaje)

    # -------- DEFENDER PADRES --------

    if "shazuy" in mensaje or "princess" in mensaje:

        if any(p in mensaje for p in MALAS_PALABRAS):

            await message.channel.send(
                f"{message.author.mention} respeta a mis padres 🤨"
            )
            return

    # -------- SHIPS --------

    if message.channel.id == CANAL_SHIPS:

        if len(message.mentions) != 2:
            await message.channel.send("❌ usa: @usuario + @usuario")
            return

        user1,user2 = message.mentions[0],message.mentions[1]

        ship_key = "-".join(sorted([str(user1.id),str(user2.id)]))

        with open("ships.json","r") as f:
            data = json.load(f)

        if ship_key not in data:
            data[ship_key] = {"count":0}

        data[ship_key]["count"] += 1

        with open("ships.json","w") as f:
            json.dump(data,f)

        canal = bot.get_channel(CANAL_REGISTRO)

        if canal:
            await canal.send(
                f"📌 nuevo ship\n{user1.mention} ❤️ {user2.mention}\n"
                f"Votos: {data[ship_key]['count']}"
            )

        await message.add_reaction("❤️")

        return

    # -------- IA SOLO CANAL IA --------

    if message.channel.id != CANAL_IA:
        return

    contador_mensajes += 1

    activar = False

    if bot.user in message.mentions:
        activar = True

    if contador_mensajes >= MENSAJES_PARA_RESPUESTA:
        activar = True
        contador_mensajes = 0

    if activar:

        respuesta = await generar_respuesta(
            message.channel.id,
            message.content,
            message.author.id
        )

        emojis = detectar_emojis(message.content)

        if emojis and random.random() < 0.4:
            respuesta += " " + random.choice(emojis)

        await message.channel.send(
            f"{message.author.mention} {respuesta}"
        )

    await bot.process_commands(message)

bot.run(TOKEN)
