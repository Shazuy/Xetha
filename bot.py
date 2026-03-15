import discord
from discord.ext import commands
import json
import os
import time

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🔧 PON AQUÍ TUS IDs
CANAL_SHIPS = 1474938439551025332
CANAL_REGISTRO = 1474938511890059275
CANAL_BOOSTS = 1482525576785956924

COOLDOWN_HORAS = 12
COOLDOWN_SEGUNDOS = COOLDOWN_HORAS * 60 * 60


# Crear archivo si no existe
if not os.path.exists("ships.json"):
    with open("ships.json", "w") as f:
        json.dump({}, f)


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.channel.id == CANAL_SHIPS:

        if len(message.mentions) != 2:
            await message.channel.send("❌ Usa el formato: @usuario @usuario")
            return

        user1 = message.mentions[0]
        user2 = message.mentions[1]

        ship_key = "-".join(sorted([str(user1.id), str(user2.id)]))
        author_id = str(message.author.id)

        with open("ships.json", "r") as f:
            data = json.load(f)

        if ship_key not in data:
            data[ship_key] = {
                "count": 0,
                "cooldowns": {}
            }

        ahora = time.time()

        if author_id in data[ship_key]["cooldowns"]:

            ultimo_voto = data[ship_key]["cooldowns"][author_id]
            tiempo_restante = COOLDOWN_SEGUNDOS - (ahora - ultimo_voto)

            if tiempo_restante > 0:

                horas = int(tiempo_restante // 3600)
                minutos = int((tiempo_restante % 3600) // 60)

                await message.channel.send(
                    f"⏳ Debes esperar {horas}h {minutos}m para volver a votar este ship."
                )
                return

        data[ship_key]["count"] += 1
        data[ship_key]["cooldowns"][author_id] = ahora

        with open("ships.json", "w") as f:
            json.dump(data, f)

        canal_registro = bot.get_channel(CANAL_REGISTRO)

        if canal_registro:
            await canal_registro.send(
                f"📌 Nuevo Ship:\n{user1.mention} ❤️ {user2.mention}\nTotal votos: {data[ship_key]['count']}"
            )

        await message.add_reaction("❤️")

    await bot.process_commands(message)


# Ranking
@bot.command()
async def ranking(ctx):

    if not os.path.exists("ships.json"):
        await ctx.send("No hay ships registrados.")
        return

    with open("ships.json", "r") as f:
        data = json.load(f)

    if not data:
        await ctx.send("No hay ships registrados.")
        return

    sorted_ships = sorted(data.items(), key=lambda x: x[1]["count"], reverse=True)

    embed = discord.Embed(
        title="🏆 Ranking de Ships",
        color=discord.Color.pink()
    )

    for i, (ship, info) in enumerate(sorted_ships[:10], 1):

        ids = ship.split("-")

        try:

            user1 = await bot.fetch_user(int(ids[0]))
            user2 = await bot.fetch_user(int(ids[1]))

            embed.add_field(
                name=f"{i}. {user1.name} ❤️ {user2.name}",
                value=f"{info['count']} votos",
                inline=False
            )

        except:
            continue

    await ctx.send(embed=embed)


# Reset ship específico
@bot.command()
@commands.has_permissions(administrator=True)
async def resetship(ctx, user1: discord.Member, user2: discord.Member):

    ship_key = "-".join(sorted([str(user1.id), str(user2.id)]))

    with open("ships.json", "r") as f:
        data = json.load(f)

    if ship_key not in data:
        await ctx.send("Ese ship no existe.")
        return

    data[ship_key]["count"] = 0
    data[ship_key]["cooldowns"] = {}

    with open("ships.json", "w") as f:
        json.dump(data, f)

    await ctx.send(f"✅ Ship reiniciado: {user1.mention} ❤️ {user2.mention}")


# Reset total
@bot.command()
@commands.has_permissions(administrator=True)
async def resetall(ctx):

    with open("ships.json", "w") as f:
        json.dump({}, f)

    await ctx.send("🔥 Todos los ships han sido reiniciados.")


# Detectar cuando alguien pierde boost
@bot.event
async def on_member_update(before, after):

    booster_role = discord.utils.get(before.guild.roles, name="Server Booster")

    if booster_role is None:
        return

    tenia_boost = booster_role in before.roles
    tiene_boost = booster_role in after.roles

    if tenia_boost and not tiene_boost:

        canal = bot.get_channel(CANAL_BOOSTS)

        if canal:
            await canal.send(
                f"⚠️ {after.mention} ha dejado de boostear el servidor."
            )


bot.run(TOKEN)
