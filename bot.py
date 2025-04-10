import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

tracked_users = set()

@bot.event
async def on_ready():
    print(f"Conectado como {bot.user}.")

@bot.command()
async def track(ctx, member: discord.Member = None):
    member = member or ctx.author
    tracked_users.add(member.id)
    await ctx.send(f"Ahora estoy siguiendo los cambios de presencia de {member.display_name}.")
@bot.command()
async def untrack(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id in tracked_users:
        tracked_users.remove(member.id)
        await ctx.send(f"He dejado de seguir los cambios de presencia de {member.display_name}.")
    else:
        await ctx.send(f"{member.display_name} no estaba siendo seguido.")
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
        
        if changes:
            channel = discord.utils.get(after.guild.text_channels, name="botargas")  # Cambia esto si quieres usar otro canal
            if channel:
                await channel.send(f"{after.display_name} " + " y ".join(changes))

load_dotenv()
# Reemplaza 'TU_TOKEN_AQUI' por tu token real de bot
bot.run(os.getenv('BOT_TOKEN'))
