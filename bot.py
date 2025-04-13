import discord
from discord.ext import commands, tasks
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

tracked_users = set()
user_game_times = {}  # Dictionary to track playtime {user_id: {game_name: {"start_time": datetime, "total_time": timedelta}}}

def save_game_data():
    """Guarda los datos de tiempo de juego en un archivo JSON."""
    data_to_save = {}
    
    # Convertir los datos a un formato serializable
    for user_id, games in user_game_times.items():
        data_to_save[str(user_id)] = {}
        for game_name, game_data in games.items():
            # Antes de guardar, actualizar el tiempo total si hay una sesión activa
            total_time = game_data["total_time"]
            if game_data["start_time"] is not None:
                now = datetime.now(timezone.utc)
                current_session = now - game_data["start_time"]
                # Para guardar, sumamos el tiempo actual pero no modificamos el objeto original
                total_time = total_time + current_session
                
            # Convertir timedelta a segundos para poder serializarlo
            total_seconds = total_time.total_seconds()
            # Convertir datetime a string ISO si existe
            start_time = None
            if game_data["start_time"]:
                start_time = game_data["start_time"].isoformat()
                
            data_to_save[str(user_id)][game_name] = {
                "total_time": total_seconds,
                "start_time": start_time
            }
    
    # Guardar en el archivo
    with open("game_data.json", "w") as f:
        json.dump(data_to_save, f, indent=4)  # Añadir indentación para legibilidad
    print(f"[DEBUG] Datos guardados en game_data.json")

def load_game_data():
    """Carga los datos de tiempo de juego desde un archivo JSON."""
    global user_game_times, tracked_users
    
    if not os.path.exists("game_data.json"):
        print("[DEBUG] No existe archivo de datos previo")
        return
    
    try:
        with open("game_data.json", "r") as f:
            data = json.load(f)
        
        # Convertir los datos al formato usado por el bot
        for user_id_str, games in data.items():
            user_id = int(user_id_str)
            tracked_users.add(user_id)  # Añadir usuario a la lista de seguimiento
            user_game_times[user_id] = {}
            
            for game_name, game_data in games.items():
                # Convertir segundos a timedelta
                total_time = timedelta(seconds=game_data["total_time"])
                # Convertir string ISO a datetime si existe
                start_time = None
                if game_data["start_time"]:
                    start_time = datetime.fromisoformat(game_data["start_time"])
                
                user_game_times[user_id][game_name] = {
                    "total_time": total_time,
                    "start_time": start_time
                }
        
        print(f"[DEBUG] Datos cargados desde game_data.json: {len(user_game_times)} usuarios")
    except Exception as e:
        print(f"[ERROR] Error al cargar datos: {e}")


@tasks.loop(minutes=5)
async def backup_data():
    """Guarda los datos cada 5 minutos."""
    save_game_data()
    print(f"[DEBUG] Respaldo automático de datos completado: {datetime.now()}")

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}.")
    # Cargar datos guardados
    load_game_data()
    print(f"[DEBUG] Usuarios cargados: {tracked_users}")
    print(f"[DEBUG] Datos de juego cargados: {user_game_times}")
    # Iniciar la tarea de respaldo
    backup_data.start()

@bot.command()
async def save(ctx):
    """Fuerza el guardado de datos de tiempo de juego."""
    save_game_data()
    await ctx.send("Datos de tiempo de juego guardados correctamente.")

@bot.command()
async def track(ctx, member: discord.Member = None):
    member = member or ctx.author
    tracked_users.add(member.id)
    user_game_times[member.id] = {}  # Initialize game tracking for the user
    
    # Verificar si el usuario está jugando actualmente
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing:
            track_game_time(member.id, activity.name)
            await ctx.send(f"Detectado que {member.display_name} está jugando a {activity.name}. Iniciando seguimiento.")
    
    await ctx.send(f"Ahora estoy siguiendo los cambios de presencia de {member.display_name}.")
    # Guardar datos después de añadir un nuevo usuario
    save_game_data()

@bot.command()
async def untrack(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id in tracked_users:
        # Detener seguimiento de juegos activos
        stop_all_games(member.id)
        tracked_users.remove(member.id)
        # NO eliminamos los datos de juego para mantener el historial
        # user_game_times.pop(member.id, None)  <- Esta línea se elimina
        await ctx.send(f"He dejado de seguir los cambios de presencia de {member.display_name}. Se ha guardado su historial de tiempo de juego.")
        # Guardar datos después de dejar de seguir
        save_game_data()
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
            total_with_current = total_time + current_session
            # Mostrar el tiempo total (acumulado + sesión actual)
            response += f"- **{game}**: {format_time(total_with_current)} (incluye sesión actual de {format_time(current_session)})\n"
        else:
            response += f"- **{game}**: {format_time(total_time)}\n"

    await ctx.send(response)

def format_time(td):
    """Formatea un timedelta en un formato más legible."""
    # Obtener días, horas, minutos y segundos
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Crear una cadena formateada
    parts = []
    if days > 0:
        parts.append(f"{days} día{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
    if seconds > 0 and days == 0 and hours == 0:  # Solo mostrar segundos si no hay días ni horas
        parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")
    
    if not parts:  # Si no hay tiempo (menos de un segundo)
        return "menos de un segundo"
    
    return ", ".join(parts)


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
        # Si ya estamos siguiendo este juego, solo actualizamos el tiempo de inicio si no está activo
        if user_games[game_name]["start_time"] is None:
            print(f"[DEBUG] Reiniciando seguimiento para {game_name}")
            user_games[game_name]["start_time"] = now
            print(f"[DEBUG] Nuevo estado: {user_games[game_name]}")
    
    # Guardar datos después de iniciar seguimiento
    save_game_data()

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
        # Guardar datos después de detener juegos
        save_game_data()
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
