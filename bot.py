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
        await ctx.send(f"{member.display_name} no estaba siendo seguid@.")

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

    # Obtener el tiempo actual para calcular sesiones en curso
    now = datetime.now(timezone.utc)
    
    response = f"Tiempo de juego de {member.display_name}:\n"
    for game, data in game_times.items():
        # Calcular el tiempo total incluyendo la sesión actual si está jugando
        total_time = data["total_time"]
        
        # Si hay una sesión activa, añadir el tiempo transcurrido
        if data["start_time"] is not None:
            current_session = now - data["start_time"]
            print(f"[DEBUG] Juego {game} en sesión activa. Tiempo actual: {current_session}")
            current_total = total_time + current_session
            response += f"- **{game}**: {str(total_time)} + {str(current_session)} (sesión actual) = {str(current_total)}\n"
        else:
            response += f"- **{game}**: {str(total_time)}\n"

    await ctx.send(response)


@bot.event
async def on_presence_update(before, after):
    if after.id in tracked_users:
        changes = []
        if before.status != after.status:
            changes.append(f"cambió su **estado** de `{before.status}` a `{after.status}`")
        
        # Verificar si el usuario dejó de jugar a algún juego
        before_games = set()
        after_games = set()
        
        for activity in before.activities:
            if activity.type == discord.ActivityType.playing:
                before_games.add(activity.name)
        
        for activity in after.activities:
            if activity.type == discord.ActivityType.playing:
                after_games.add(activity.name)
        
        # Si hay juegos que estaban antes pero no están ahora, detener su seguimiento
        stopped_games = before_games - after_games
        if stopped_games:
            print(f"[DEBUG] Usuario {after.id} dejó de jugar a: {stopped_games}")
            stop_all_games(after.id)
        
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
                    # [resto del código para otros tipos de actividades]
                
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
            channel = discord.utils.get(after.guild.text_channels, name="botargas")
            if channel:
                await channel.send(f"{after.display_name} " + " y ".join(changes))

def track_game_time(user_id, game_name):
    now = datetime.now(timezone.utc)
    print(f"[DEBUG] Iniciando seguimiento para usuario {user_id}, juego {game_name} a las {now}")
    
    if user_id not in user_game_times:
        print(f"[DEBUG] Usuario {user_id} no estaba en el diccionario, inicializando")
        user_game_times[user_id] = {}
    
    user_games = user_game_times[user_id]
    
    if game_name not in user_games:
        print(f"[DEBUG] Juego {game_name} no estaba siendo seguido, inicializando con tiempo 0")
        user_games[game_name] = {"start_time": now, "total_time": timedelta()}
        print(f"[DEBUG] Estado actual: {user_games[game_name]}")
    else:
        print(f"[DEBUG] Juego {game_name} ya estaba en seguimiento, estado actual: {user_games[game_name]}")
        # If already tracking, update the start time
        if user_games[game_name]["start_time"] is None:
            print(f"[DEBUG] Reiniciando seguimiento para {game_name}")
            user_games[game_name]["start_time"] = now
            print(f"[DEBUG] Nuevo estado: {user_games[game_name]}")

def stop_all_games(user_id):
    now = datetime.now(timezone.utc)
    print(f"[DEBUG] Deteniendo todos los juegos para usuario {user_id} a las {now}")
    
    if user_id in user_game_times:
        print(f"[DEBUG] Juegos activos para usuario {user_id}: {user_game_times[user_id]}")
        for game, data in user_game_times[user_id].items():
            if data["start_time"] is not None:
                elapsed = now - data["start_time"]
                print(f"[DEBUG] Juego {game}: tiempo transcurrido {elapsed}")
                data["total_time"] += elapsed
                data["start_time"] = None
                print(f"[DEBUG] Nuevo tiempo total para {game}: {data['total_time']}")
            else:
                print(f"[DEBUG] Juego {game} no estaba activo (start_time es None)")
    else:
        print(f"[DEBUG] Usuario {user_id} no tiene juegos en seguimiento")

@bot.event
async def on_member_update(before, after):
    # Stop tracking playtime if the user stops playing a game
    if before.activities != after.activities:
        stop_all_games(after.id)

load_dotenv()
# Reemplaza 'TU_TOKEN_AQUI' por tu token real de bot
bot.run(os.getenv('BOT_TOKEN'))
