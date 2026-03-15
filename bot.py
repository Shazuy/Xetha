import discord
from discord.ext import commands
import json
import os
import time
import random
from openai import OpenAI

# -------- TOKENS --------
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client_ai = OpenAI(api_key=OPENAI_API_KEY)

# -------- INTENTS --------
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

# -------- MEMORIA CONVERSACION --------
historial_canales = {}
MAX_HISTORIAL = 20

# -------- PERSONALIDAD --------
PROMPT_XETHA = """
Eres Xetha, un bot relajado que escribe como usuario normal de Discord.

Hablas corto, informal, con abreviaciones y emojis.
A veces eres sarcástico o bromista.

Familia:
- Shazuy es tu padre
- Princess es tu madre
- Brandon es tu tío

A Shazuy y Princess siempre les hablas con respeto.
A Brandon puedes hablarle con confianza.

No digas que eres una IA.
Responde como si fueras un usuario normal del servidor.
"""

# -------- LISTAS --------
MALAS_PALABRAS = ["puta","mierda","idiota","imbecil","pendejo"]

BROMAS_BRANDON = [
    "brandon otra vez por aki 🤨",
    "si brandon ta aki seguro arma algo 😅",
    "brandon aparece cuando menos lo espero jaja"
]

# -------- ARCHIVO SHIPS --------
if not os.path.exists("ships.json"):
    with open("ships.json","w") as f:
        json.dump({},f)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"xetha conectado como {bot.user}")

# -------- BOOST DETECTOR --------
@bot.event
async def on_member_update(before, after):

    if before.premium_since and not after.premium_since:
        canal = bot.get_channel(CANAL_BOOST)

        if canal:
            await canal.send(f"⚠️ {after.mention} ya no ta boosteando el server")

# -------- FUNCION IA --------
async def generar_respuesta_corta_coloquial(canal_id, texto, respeto=False):

    prompt = PROMPT_XETHA

    if respeto:
        prompt += "\nResponde siempre con respeto, sin bromas ni sarcasmo."

    if canal_id not in historial_canales:
        historial_canales[canal_id] = []

    historial_canales[canal_id].append({
        "role": "user",
        "content": texto
    })

    historial_canales[canal_id] = historial_canales[canal_id][-MAX_HISTORIAL:]

    mensajes = [{"role": "system", "content": prompt}] + historial_canales[canal_id]

    respuesta = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=mensajes,
        max_tokens=60
    )

    texto_respuesta = respuesta.choices[0].message.content

    historial_canales[canal_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    historial_canales[canal_id] = historial_canales[canal_id][-MAX_HISTORIAL:]

    # limpiar memoria si hay demasiados canales
    if len(historial_canales) > 50:
        historial_canales.clear()

    return texto_respuesta

# -------- MENSAJES --------
@bot.event
async def on_message(message):

    global contador_mensajes, silenciado_hasta

    if message.author.bot:
        return

    mensaje = message.content.lower()

    # -------- ORDENES PADRES --------
    if message.author.id == ID_SHAZUY or message.author.id == ID_PRINCESS:

        if mensaje.startswith("xetha silencio"):

            try:
                minutos = int(mensaje.split(" ")[2])
                silenciado_hasta = time.time() + minutos*60

                await message.channel.send(
                    f"ok {message.author.mention} me callo {minutos} min 😎"
                )

            except:
                await message.channel.send("usa: xetha silencio 5")

            return

        if mensaje == "xetha habla":
            silenciado_hasta = 0
            await message.channel.send("ya volví a hablar 😏")
            return

        if ID_BRANDON in [m.id for m in message.mentions]:
            await message.channel.send(
                f"{message.author.mention} ps mi tio brandon 😅"
            )
            return

        respuesta = await generar_respuesta_corta_coloquial(
            message.channel.id,
            message.content,
            respeto=True
        )

        await message.channel.send(f"{message.author.mention} {respuesta}")
        return

    # -------- SI ESTA SILENCIADO --------
    if time.time() < silenciado_hasta:
        return

    # -------- MALAS PALABRAS --------
    if message.channel.id == CANAL_IA and random.random()<0.15:

        for palabra in MALAS_PALABRAS:

            if palabra in mensaje:
                await message.channel.send(
                    f"{message.author.mention} ey tranqui 😅"
                )
                return

    # -------- FAMILIA --------
    if message.author.id == ID_BRANDON and random.random()<0.4:
        await message.channel.send(random.choice(BROMAS_BRANDON))

    if message.author.id == ID_PEPE and random.random()<0.3:
        await message.channel.send("pepe deja algo pa los demas 😆")

    if message.author.id == ID_MIGUELITO and random.random()<0.3:
        await message.channel.send("miguelito dándolo todo 🤖")

    # -------- SHIPS --------
    if message.channel.id == CANAL_SHIPS:

        if len(message.mentions)!=2:
            await message.channel.send("❌ usa: @usuario + @usuario")
            return

        user1,user2 = message.mentions[0], message.mentions[1]

        ship_key = "-".join(sorted([str(user1.id),str(user2.id)]))
        author_id = str(message.author.id)

        with open("ships.json","r") as f:
            data = json.load(f)

        if ship_key not in data:
            data[ship_key] = {"count":0,"cooldowns":{}}

        ahora = time.time()

        if author_id in data[ship_key]["cooldowns"]:

            ultimo = data[ship_key]["cooldowns"][author_id]
            restante = COOLDOWN_SEGUNDOS-(ahora-ultimo)

            if restante>0:

                h = int(restante//3600)
                m = int((restante%3600)//60)

                await message.channel.send(f"⏳ espera {h}h {m}m")
                return

        data[ship_key]["count"]+=1
        data[ship_key]["cooldowns"][author_id]=ahora

        with open("ships.json","w") as f:
            json.dump(data,f)

        canal = bot.get_channel(CANAL_REGISTRO)

        if canal:
            await canal.send(
                f"📌 nuevo ship\n{user1.mention} ❤️ {user2.mention}\n"
                f"Votos: {data[ship_key]['count']}"
            )

        await message.add_reaction("❤️")

    # -------- IA --------
    if message.channel.id == CANAL_IA:

        contador_mensajes +=1
        activar = False

        if "xetha" in mensaje or bot.user in message.mentions:
            activar=True

        if contador_mensajes >= MENSAJES_PARA_RESPUESTA:
            activar=True
            contador_mensajes=0

        if activar:

            respuesta = await generar_respuesta_corta_coloquial(
                message.channel.id,
                message.content
            )

            await message.channel.send(
                f"{message.author.mention} {respuesta}"
            )

    await bot.process_commands(message)

# -------- RUN BOT --------
bot.run(TOKEN)
