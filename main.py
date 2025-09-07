import os
import discord
from discord.ext import commands
import requests
import asyncio

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def start():
    port = int(os.environ.get("PORT", 10000))  # Port imposé par Render
    app.run(host="0.0.0.0", port=port)

intents = discord.Intents.default()
intents.message_content = True
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

PECHEURS_ROLE = "Pécheurs"
PECHE_S_CAPITAUX = [
    "Luxure", "Colère", "Envie", "Paresse", "Orgueil", "Gourmandise", "Avarice"
]


def send_data_to_api(owner_name, players_dict):
    url = "https://siteapi-2.onrender.com/update"
    payload = {
        "owner": owner_name,
        "players": players_dict  # 👈 On regroupe tout dans une clé "players"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[API] ✅ Envoyé : owner={owner_name}")
        else:
            print(f"[API] ⚠️ Code {response.status_code} : {response.text}")
    except requests.exceptions.Timeout:
        print(f"[API] ⏱️ Timeout vers l'API")
    except requests.exceptions.ConnectionError:
        print(f"[API] 🔌 Erreur de connexion vers l'API")
    except Exception as e:
        print(f"[API] ❌ Erreur lors de l'envoi : {e}")


async def periodic_task():
    await bot.wait_until_ready()
    print("[Bot] Tâche périodique démarrée")

    while not bot.is_closed():
        try:
            # Vérifier que le bot est toujours connecté
            if not bot.is_ready():
                print("[Bot] Bot non prêt, attente...")
                await asyncio.sleep(10)
                continue

            # Vérifier qu'il y a au moins un serveur
            if not bot.guilds:
                print("[Bot] Aucun serveur trouvé, attente...")
                await asyncio.sleep(30)
                continue

            app_info = await bot.application_info()
            owner_name = app_info.owner.name

            guild = bot.guilds[0]
            role_pecheurs = discord.utils.get(guild.roles, name=PECHEURS_ROLE)

            players = {}
            for peche in PECHE_S_CAPITAUX:
                role_peche = discord.utils.get(guild.roles, name=peche)
                if not role_peche:
                    players[peche] = {"name": "Place vacante", "avatar": None}
                    continue
                    
                joueur = None
                for member in guild.members:
                    if role_pecheurs in member.roles and role_peche in member.roles:
                        joueur = member
                        break
                        
                    if joueur:
                        players[peche] = {
                        "name": joueur.display_name,
                        "avatar": joueur.avatar.url if joueur.avatar else joueur.default_avatar.url
                    }
                else:
                    players[peche] = {"name": "Place vacante", "avatar": None}
            send_data_to_api(owner_name, players)
            print(
                f"[Bot] Données envoyées avec succès - {len(players)} péchés traités"
            )

        except discord.errors.HTTPException as e:
            print(f"[Erreur Discord] HTTP : {e}")
            await asyncio.sleep(
                30)  # Attendre plus longtemps en cas d'erreur Discord
        except Exception as e:
            print(f"[Erreur] tâche périodique : {e}")
            print(f"[Debug] Type d'erreur : {type(e).__name__}")

        await asyncio.sleep(60)

async def auto_bump():
    await bot.wait_until_ready()  # On attend que le bot soit prêt
    while not bot.is_closed():
        # Récupère le serveur et le salon "bot"
        for guild in bot.guilds:
            channel = discord.utils.get(guild.text_channels, name="「🤖」bot")
            if channel:
                try:
                    await channel.send("/bump")
                    print(f"[BUMP] /bump envoyé dans {guild.name}")
                except Exception as e:
                    print(f"[BUMP] Erreur : {e}")
            else:
                print(f"[BUMP] Erreur :channel pas trouvé")
        # Attend 2 heures et 10 minutes (2*3600 + 10*60 = 7800 secondes)
        await asyncio.sleep(7800)


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    print(f"Connecté à {len(bot.guilds)} serveur(s)")
    bot.loop.create_task(periodic_task())
    bot.loop.create_task(auto_bump()) 
            
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"[Erreur Bot] Événement {event} : {args}")


@bot.event
async def on_disconnect():
    print("[Bot] Déconnecté de Discord")


@bot.event
async def on_resumed():
    print("[Bot] Reconnecté à Discord")
    
@bot.event
async def on_message(message):
    # Empêche le bot de répondre à lui-même
    if message.author == bot.user:
        return

    if "bonjour" in message.content.lower():
        await message.channel.send(f"Bonjour {message.author} ! 🤗")

    if "fafa" in message.content.lower():
        await message.add_reaction("🍆")  # Correction ici
        
    if "zeleph" in message.content.lower():
        await message.add_reaction("🦊")  # Correction ici

    if "killian" in message.content.lower():
        await message.add_reaction("🥵")  # Correction ici

    if "nuggets" in message.content.lower():
        await message.add_reaction("🐔")  # Correction ici

    if "kuzoki" in message.content.lower():
        await message.add_reaction("🐺")  # Correction ici

    if "noisette" in message.content.lower():
        await message.add_reaction("🌰")  # Correction ici

    if "pigeon" in message.content.lower():
        await message.add_reaction("🐤")  # Correction ici

    if "piaf" in message.content.lower():
        await message.add_reaction("🐤")  # Correction ici
        
    if "sakir" in message.content.lower():
        await message.add_reaction("🦝")
        
    # Si le bot est mentionné
    if bot.user in message.mentions:
        await message.channel.send(
            f"Oui {message.author.mention} ?"
        )

    # Permet au bot de traiter les commandes si besoin
    await bot.process_commands(message)
    
@bot.command(name="classement")
async def classement(ctx):
    guild = ctx.guild

    classement = []

    for peche in PECHE_S_CAPITAUX:
        role_peche = discord.utils.get(guild.roles, name=peche)
        if not role_peche:
            classement.append((peche, 0))
            continue

        count = len(role_peche.members)
        classement.append((peche, count))

    # Trie le classement par nombre décroissant
    classement.sort(key=lambda x: x[1], reverse=True)

    # Formatage du message
    msg = "**Classement des péchés capitaux (par nombre de membres) :**\n"
    for i, (peche, count) in enumerate(classement, 1):
        msg += f"**{i}. {peche}** — {count} membre(s)\n"

    await ctx.send(msg)      
    
@bot.command()
@commands.is_owner()  # seule la personne propriétaire du bot peut utiliser
async def reload(ctx, extension: str = None):
    """Recharge une extension ou toutes"""
    if extension:
        try:
            await bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"✅ Extension `{extension}` rechargée.")
        except Exception as e:
            await ctx.send(f"❌ Erreur en rechargant `{extension}`: `{e}`")
    else:
        reloaded = []
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.reload_extension(f"cogs.{filename[:-3]}")
                    reloaded.append(filename)
                except Exception as e:
                    await ctx.send(f"❌ Erreur dans `{filename}`: `{e}`")
        await ctx.send(f"✅ Extensions rechargées : {', '.join(reloaded)}")

token = os.environ.get('TOKEN')
print("TOKEN chargé ? ", 'TOKEN' in os.environ)
print("Longueur du token :", len(os.environ.get('TOKEN', '')))
if not token:
    print("Erreur : variable d'environnement TOKEN absente ou vide.")
    exit(1)
    
import threading
threading.Thread(target=start).start()

bot.run(token)










