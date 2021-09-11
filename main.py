# bot.py
import os
import random
import discord
from discord.ext import commands
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
import requests
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
STEAM_API_TOKEN = os.getenv('STEAM_API_TOKEN')

bot = commands.Bot(command_prefix='!')

@bot.command(name='getId')
async def nine_nine(ctx):
    
    members = ctx.message.mentions
    result = []
    
    for member in members:
        result.append(member.id)

    response = result
    await ctx.send(response)

@bot.command(name='join')
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

@bot.command(name='p')
async def play(ctx):
    guild = ctx.guild
    voice_client: discord.VoiceClient = discord.utils.get(bot.voice_clients, guild=guild)
    print('1')

@bot.command(name='steam')
async def steam(ctx):
    user = ctx.author.id
    f = open('user.json',)
    users = json.load(f)

    steam_id = 0
    for i in users['users']:
        if i["discord_id"] == user:
            steam_id = i["steam_id"]
        
    r = requests.get(url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+STEAM_API_TOKEN+"&steamids="+str(steam_id))
  
    data = r.json()

    await ctx.send(data["response"]["players"][0]["profileurl"])

@bot.command(name='games')
async def games(ctx):
    f = open('user.json',)
    users = json.load(f)
    members = ctx.message.mentions

    if len(members) >= 2:
        targets = []
        steam_id = []
        playersGames = []
        for member in members:
            targets.append(member)
            
        
        for target in targets:
            link = 0
            games = []
            for index, element in enumerate(users["users"]):
                if element["discord_id"] == target.id:
                    link = element["steam_id"]
            
            if link == 0:
                await ctx.send("Erreur: "+member.name+ " n'a pas de compte Steam lié!")
            else :
                r = requests.get(url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="+STEAM_API_TOKEN+"&steamid="+str(link)+"&format=json&include_appinfo=1")
                for game in r.json()["response"]["games"]:
                    games.append(game["name"])
            playersGames.append(games)

       
        samesGames = playersGames[0]
        i = 0
        for listGames in playersGames:
            samesGames = list(set(samesGames).intersection(set(playersGames[i])))
            i = i+1
        
        embedVar = discord.Embed(title="__**Jeux en communs**__", color=0xcd2626)
        s = ""
        for g in samesGames:
            s =s+g+'\n' \
          
        embedVar.add_field(name="Steam : "+str(len(samesGames))+" résultats",value=s)
        embedVar.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/502115424121528320/hTQzj_-R.png"
        )
        await ctx.send(embed=embedVar)
     
    else :
        await ctx.send("Erreur : Nombre d'utilisateur insuffisants")

bot.run(TOKEN)