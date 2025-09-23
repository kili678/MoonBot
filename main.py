# bot.py
import os
import discord
from discord.ext import commands
import requests
import asyncio
import threading
from flask import Flask

# --- KEEP-ALIVE (optionnel) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"
def start():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=start).start()
# -------------------------------

# Intents (IMPORTANT: active Server Members Intent dans le portail Discord)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

PECHEURS_ROLE = "Pécheurs"
PECHE_S_CAPITAUX = [
    "Luxure", "Colère", "Envie", "Paresse", "Orgueil", "Gourmandise", "Avarice"
]
JEUX_ROLES = ["Valorant", "Genshin Impact", "Resident evil", "Minecraft", "Red Dead", "Roblox", "Jeux indépendants"]

def find_role_by_name(guild, name):
    """Recherche role case-insensitive"""
    return discord.utils.find(lambda r: r.name.lower() == name.lower(), guild.roles)

async def fetch_annonces_messages():
    """Récupère les 3 derniers messages du salon '「📆」annonces' (texte + avatar + attachments)"""
    await bot.wait_until_ready()
    if not bot.guilds:
        print("[fetch_annonces] Aucun serveur connecté.")
        return []

    guild = bot.guilds[0]
    channel = discord.utils.get(guild.text_channels, name="「📆」annonces")
    if not channel:
        print("[fetch_annonces] Salon '「📆」annonces' introuvable.")
        return []

    messages_data = []
    async for msg in channel.history(limit=3):
        try:
            avatar = msg.author.display_avatar.url
        except Exception:
            avatar = msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url
        attachments = [a.url for a in msg.attachments] if msg.attachments else []
        messages_data.append({
            "author_name": msg.author.display_name,
            "author_avatar": avatar,
            "content": msg.content,
            "attachments": attachments
        })
    return messages_data

async def build_players(guild):
    """Construit le dict players (nom + avatar) en cherchant les membres ayant les deux rôles."""
    role_pecheurs = find_role_by_name(guild, PECHEURS_ROLE)
    if not role_pecheurs:
        print("[build_players] Role 'Pécheurs' introuvable sur le serveur !")

    players = {}
    for peche in PECHE_S_CAPITAUX:
        role_peche = find_role_by_name(guild, peche)
        if not role_peche:
            print(f"[build_players] Role '{peche}' introuvable.")
            players[peche] = {"name": "Place vacante", "avatar": None}
            continue

        joueur = None

        # 1) essaye cache
        for member in guild.members:
            if role_pecheurs in member.roles and role_peche in member.roles:
                joueur = member
                break

        # 2) fallback fetch si pas trouvé (nécessite intent membres activé)
        if not joueur:
            try:
                async for member in guild.fetch_members(limit=None):
                    if role_pecheurs in member.roles and role_peche in member.roles:
                        joueur = member
                        break
            except Exception as e:
                print(f"[build_players] Erreur fetch_members: {e}")

        if joueur:
            try:
                avatar = joueur.display_avatar.url
            except Exception:
                avatar = joueur.avatar.url if joueur.avatar else joueur.default_avatar.url
            players[peche] = {"name": joueur.display_name, "avatar": avatar}
        else:
            players[peche] = {"name": "Place vacante", "avatar": None}

    return players

async def build_classement(guild):
    """Construit le classement des péchés capitaux (comme la commande !classement)"""
    classement = []
    for peche in PECHE_S_CAPITAUX:
        role_peche = find_role_by_name(guild, peche)
        if not role_peche:
            classement.append({"peche": peche, "count": 0})
            continue
        count = len(role_peche.members)
        if count == 0:
            # fallback : fetch members
            try:
                async for m in guild.fetch_members(limit=None):
                    if role_peche in m.roles:
                        count += 1
            except Exception as e:
                print(f"[build_classement] fetch_members erreur: {e}")
        classement.append({"peche": peche, "count": count})
    # tri décroissant
    classement.sort(key=lambda x: x["count"], reverse=True)
    return classement

async def build_classement_jeux(guild):
    """Construit le classement des jeux (par nombre de membres dans chaque rôle)"""
    classement = []
    for jeu in JEUX_ROLES:
        role_jeu = find_role_by_name(guild, jeu)
        if not role_jeu:
            classement.append({"jeu": jeu, "count": 0})
            continue
        count = len(role_jeu.members)
        if count == 0:
            # fallback si jamais
            try:
                async for m in guild.fetch_members(limit=None):
                    if role_jeu in m.roles:
                        count += 1
            except Exception as e:
                print(f"[build_classement_jeux] fetch_members erreur: {e}")
        classement.append({"jeu": jeu, "count": count})
    classement.sort(key=lambda x: x["count"], reverse=True)
    return classement
    
async def periodic_task():
    await bot.wait_until_ready()
    print("[Bot] Tâche périodique démarrée")
    while not bot.is_closed():
        try:
            if not bot.is_ready():
                await asyncio.sleep(10)
                continue
            if not bot.guilds:
                await asyncio.sleep(30)
                continue

            app_info = await bot.application_info()
            owner_name = app_info.owner.name

            guild = bot.guilds[0]

            # build players (robuste)
            players = await build_players(guild)

            # récupérer 3 dernières annonces
            annonces = await fetch_annonces_messages()

            classement = await build_classement(guild)

            classement_jeux = await build_classement_jeux(guild)

            payload = {
                "owner": owner_name,
                "players": players,
                "annonces": annonces,
                "ClassementPeche": classement,
                "ClassementJeux": classement_jeux,
            }

            url = os.environ.get("API_URL", "https://siteapi-2.onrender.com/update")
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print("[API] ✅ Données envoyées (avec annonces)")
                else:
                    print(f"[API] ⚠️ Code {response.status_code} : {response.text}")
            except Exception as e:
                print(f"[API] ❌ Erreur envoi annonces : {e}")

        except Exception as e:
            print(f"[Erreur] tâche périodique : {e}")

        await asyncio.sleep(60)

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    print(f"Connecté à {len(bot.guilds)} serveur(s)")
    bot.loop.create_task(periodic_task())

@bot.command(name="classement")
async def classement(ctx):
    guild = ctx.guild
    classement = []
    for peche in PECHE_S_CAPITAUX:
        role_peche = find_role_by_name(guild, peche)
        if not role_peche:
            classement.append((peche, 0))
            continue
        count = len(role_peche.members)
        if count == 0:
            # fallback : fetch members
            count = 0
            try:
                async for m in guild.fetch_members(limit=None):
                    if role_peche in m.roles:
                        count += 1
            except Exception as e:
                print(f"[classement] fetch_members erreur: {e}")
        classement.append((peche, count))
    classement.sort(key=lambda x: x[1], reverse=True)
    msg = "**Classement des péchés capitaux (par nombre de membres) :**\n"
    for i, (peche, count) in enumerate(classement, 1):
        msg += f"**{i}. {peche}** — {count} membre(s)\n"
    await ctx.send(msg)
    
@bot.command(name="classement-jeux")
async def classement_jeux(ctx):
    guild = ctx.guild
    classement = await build_classement_jeux(guild)
    msg = "**Classement des jeux (par nombre de membres) :**\n"
    for i, entry in enumerate(classement, 1):
        msg += f"**{i}. {entry['jeu']}** — {entry['count']} membre(s)\n"
    await ctx.send(msg)
    
@bot.command(name="tg")
async def tg(ctx):
    guild = ctx.guild
    classement = await build_classement_jeux(guild)
    msg = "**tg avec ton goumin de con tfaçon c'est qu'une pute**\n"
    await ctx.send(msg)
@bot.command(name ="love")
async def love(ctx, member: discord.Member):
    # Générer un pourcentage aléatoire
    pourcentage = random.randint(0, 100)

    # Message de réponse
    await ctx.send(f"💖 Test d'amour entre **{ctx.author.display_name}** et **{member.display_name}** : {pourcentage}% 💖")
# Optional: commande manuelle pour forcer l'envoi et debug
@bot.command(name="moon.update")
@commands.is_owner()
async def force_update(ctx):
    await ctx.send("Envoi manuel en cours...")
    guild = ctx.guild or (bot.guilds[0] if bot.guilds else None)
    if not guild:
        await ctx.send("Aucun serveur disponible.")
        return
    app_info = await bot.application_info()
    owner_name = app_info.owner.name
    players = await build_players(guild)
    annonces = await fetch_annonces_messages()
    classement = await build_classement(guild)
    payload = {"owner": owner_name, "players": players, "annonces": annonces, "ClassementPeche": classement}
    url = os.environ.get("API_URL", "https://siteapi-2.onrender.com/update")
    try:
        r = requests.post(url, json=payload, timeout=10)
        await ctx.send(f"API status: {r.status_code}")
    except Exception as e:
        await ctx.send(f"Erreur envoi: {e}")

# Token & run
token = os.environ.get('TOKEN')
if not token:
    print("Erreur : variable d'environnement TOKEN absente ou vide.")
    exit(1)
bot.run(token)





