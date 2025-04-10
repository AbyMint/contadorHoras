import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

tracked_users = set()
user_game_times = {}  # Dictionary to track playtime {user_id: {game_name: {"start_time": datetime, "total_time": timedelta}}}

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}.")

@bot.command()
async def track(ctx, member: discord.Member = None):
    member = member or ctx.author
    tracked_users.add(member.id)
    user_game_times[member.id] = {}  # Initialize game tracking for the user
    await ctx.send(f"Ahora estoy siguiendo los cambios de presencia de {member.display_name}.")

@bot.command()
async def untrack(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id in tracked_users:
        tracked_users.remove(member.id)
        user_game_times.pop(member.id, None)  # Remove game tracking for the user
        await ctx.send(f"He dejado de seguir los cambios de presencia de {member.display_name}.")
    else:
        await ctx.send(f"{member.display_name} no estaba siendo seguido.")

@bot.command()
async def playtime(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id not in user_game_times:
        await ctx.send(f"No se está rastreando el tiempo de juego de {member.display_name}.")
        return

    game_times = user_game_times[member.id]
    if not game_times:
        await ctx.send(f"{member.display_name} no ha jugado ningún juego rastreado.")
        return

    response = f"Tiempo de juego de {member.display_name}:\n"
    for game, data in game_times.items():
        total_time = data["total_time"]
        response += f"- **{game}**: {str(total_time)}\n"

    await ctx.send(response)

@bot.event
async def on_presence_update(before, after):
    if after.id in tracked_users:
        changes = []
        if before.status != after.status:
            changes.append(f"cambió su **estado** de `{before.status}` a `{after.status}`")
        
        # Verificar cambios en actividades con más detalle
        if before.activities != after.activities:
            # Si hay actividades actuales
            if after.activities:
                activity_details = []
                for activity in after.activities:
                    if activity.type == discord.ActivityType.playing:
                        activity_details.append(f"jugando a **{activity.name}**")
                        # Track playtime
                        track_game_time(after.id, activity.name)
                    elif activity.type == discord.ActivityType.streaming:
                        activity_details.append(f"transmitiendo **{activity.name}**")
                    elif activity.type == discord.ActivityType.listening:
                        activity_details.append(f"escuchando **{activity.name}**")
                    elif activity.type == discord.ActivityType.watching:
                        activity_details.append(f"viendo **{activity.name}**")
                    elif activity.type == discord.ActivityType.custom:
                        if activity.name:
                            activity_details.append(f"con estado personalizado **{activity.name}**")
                    else:
                        activity_details.append(f"con actividad **{activity.name}**")
                
                if activity_details:
                    changes.append(f"ahora está {', '.join(activity_details)}")
                else:
                    changes.append(f"cambió su **actividad**")
            else:
                # Si no hay actividades actuales pero había antes
                changes.append(f"dejó de realizar actividades")
                # Stop tracking playtime for all games
                stop_all_games(after.id)
        
        if changes:
            channel = discord.utils.get(after.guild.text_channels, name="botargas")  # Cambia esto si quieres usar otro canal
            if channel:
                await channel.send(f"{after.display_name} " + " y ".join(changes))

def track_game_time(user_id, game_name):


    now = datetime.now(timezone.utc)
    if user_id not in user_game_times: 0
    user_games = user_game_times[user_id]
    if game_name not in user_games:
        user_games[game_name] = {"start_time": now, "total_time": timedelta()}
    else:
        # If already tracking, update the start time
        if user_games[game_name]["start_time"] is None:
            user_games[game_name]["start_time"] = now

def stop_all_games(user_id):
    now = datetime.utcnow()
    if user_id in user_game_times:
        for game, data in user_game_times[user_id].items():
            if data["start_time"] is not None:
                elapsed = now - data["start_time"]
                data["total_time"] += elapsed
                data["start_time"] = None

@bot.event
async def on_member_update(before, after):
    # Stop tracking playtime if the user stops playing a game
    if before.activities != after.activities:
        stop_all_games(after.id)

load_dotenv()
# Reemplaza 'TU_TOKEN_AQUI' por tu token real de bot
bot.run(os.getenv('BOT_TOKEN'))
