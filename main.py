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
bot = commands.Bot(command_prefix='', intents=intents)

PECHEURS_ROLE = "Pécheurs"
PECHE_S_CAPITAUX = [
    "Luxure", "Colère", "Envie", "Paresse", "Orgueil", "Gourmandise", "Avarice"
]


def send_data_to_api(owner_name, players_dict):
    url = "https://siteapi-2.onrender.com/update"
    payload = {
        "owner": owner_name,
        **players_dict  # unpack des joueurs par péché
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
            if not role_pecheurs:
                print("[Erreur] Rôle 'Pécheurs' introuvable.")
                players = {peche: "aucun" for peche in PECHE_S_CAPITAUX}
            else:
                # Pour chaque péché capital, cherche un membre qui a "Pécheurs" + ce rôle
                for peche in PECHE_S_CAPITAUX:
                    role_peche = discord.utils.get(guild.roles, name=peche)
                    if not role_peche:
                        print(f"[Erreur] Rôle '{peche}' introuvable.")
                        players[peche] = "Place vacante"
                        continue
                    # Cherche un membre avec les 2 rôles
                    joueur = None
                    for member in guild.members:
                        if role_pecheurs in member.roles and role_peche in member.roles:
                            joueur = member
                            break
                    players[peche] = joueur.name if joueur else "Place vacante"

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


@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    print(f"Connecté à {len(bot.guilds)} serveur(s)")
    bot.loop.create_task(periodic_task())


@bot.event
async def on_error(event, *args, **kwargs):
    print(f"[Erreur Bot] Événement {event} : {args}")


@bot.event
async def on_disconnect():
    print("[Bot] Déconnecté de Discord")


@bot.event
async def on_resumed():
    print("[Bot] Reconnecté à Discord")


@bot.command()
async def bonjour(ctx):
    await ctx.send(f"ta gueule {ctx.author}")

@bot.command()
async def Bonjour(ctx):
    await ctx.send(f"ta gueule {ctx.author}")
    
@bot.command()
async def zeleph(ctx):
    try:
        # Réagit au message avec l'émoji renard
        await ctx.message.add_reaction("🦊")
    except discord.HTTPException as e:
        print(f"[Erreur] Impossible d'ajouter la réaction : {e}")
        
@bot.command()
async def killian(ctx):
    try:
        # Réagit au message avec l'émoji renard
        await ctx.message.add_reaction("🥵")
    except discord.HTTPException as e:
        print(f"[Erreur] Impossible d'ajouter la réaction : {e}")
        
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
