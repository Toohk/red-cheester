# bot.py
import os
import random
import discord
from discord import player
from discord.ext import commands
from discord.voice_client import VoiceClient
import MinecraftApi
from discord.utils import get
from discord.utils import get
from dotenv import load_dotenv
import requests
import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import matplotlib.pyplot as plt
import numpy as np
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
STEAM_API_TOKEN = os.getenv('STEAM_API_TOKEN')
HOUR = os.getenv('HOUR')
minecraft = {
        "channel": int(os.getenv('MC_CHANNEL')),
        "host": os.getenv('MC_HOST'),
        "port": os.getenv('MC_PORT'),
        "username": os.getenv("MC_USERNAME"),
        "password": os.getenv("MC_PASSWORD"),
        "cred": os.getenv("MC_CRED")
        }


cred = credentials.Certificate(minecraft["cred"])
firebase_admin.initialize_app(cred)

db = firestore.client()

bot = commands.Bot(command_prefix='!')

song_queue = []
current_question = {}
current_ctx = {}
current_msg = {}
questions_done = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
in_speech = 0

n_q = 0



currencyFile = open('currency.json',)
currency = json.load(currencyFile)["currency"]


FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}


@bot.command(name='getId')
async def nine_nine(ctx):
    
    members = ctx.message.mentions
    result = []
    
    for member in members:
        result.append(member.id)

    response = result
    await ctx.send(response)



async def scoreboard():
    channel = bot.get_channel(minecraft["channel"])
    f = open('user.json')
    users = json.load(f)
    print(channel)
    scoreboard = []
    day = db.collection('minecraft').document('day').get().to_dict()["day"]
    db.collection('minecraft').document('day').set({ "day" : day + 1 })


    for user in users["users"]:

        if "minecraft" in user:

            finances = await getChests(user["minecraft"]["username"])
            icon = {}
            icon["business"] = discord.utils.get(bot.emojis, name = user["minecraft"]["icon-business"])
            score = 0
            line = ""
            for item in currency:
                if "icon" in item:
                    line = f'{line}  {discord.utils.get(bot.emojis, name = item["icon"])}  {finances[item["name"]]}'
                    score = score + (finances[item["name"]] * item["points"])
            embedVar = discord.Embed(title=f"__**{user['minecraft']['username']}**__   ( {score:,} points )", color=user["minecraft"]["color"])
            embedVar.add_field(name=user["minecraft"]["business"]+f"  {icon['business']}",value=line)
            embedVar.set_thumbnail(url=user["minecraft"]["picture"])
            scoreboard.append({"embed": embedVar, "score": score})

            doc = db.collection(u"minecraft").document("scores")
            doc.update({ user["minecraft"]["username"] : firestore.ArrayUnion([{"date":datetime.datetime.now(tz=datetime.timezone.utc), "points": score, "day": day + 1}])})
    
        scoreboard = sorted(scoreboard, key = lambda i: i['score'], reverse=True)
    await channel.purge(limit=1000000)
    for e in scoreboard:
        await channel.send(embed=e["embed"])
    await graph(channel)

@bot.command(name='graph')
async def graph(ctx):
    doc = db.collection('minecraft').document('scores').get().to_dict()
    day = db.collection('minecraft').document('day').get().to_dict()["day"]
    f = open('user.json')
    users = json.load(f)

    for user in users["users"]:
        if "minecraft" in user:
            x = []
            y = []
            i = 0
            last = len(doc[user["minecraft"]["username"]])
            if day == doc[user["minecraft"]["username"]][last-1]["day"]:
                i = 0
            else :
                i = day

            for entry in doc[user["minecraft"]["username"]]:
                i = i + 1
                x.append(entry["day"])
                y.append(entry["points"])
            plt.plot(x, y, color=user["minecraft"]["color-name"], label=user["minecraft"]["username"])
    plt.legend()
    plt.xlabel("Jours")
    plt.ylabel("Points")
    plt.savefig('graph_figure.png')
    plt.clf()
    await ctx.send(file=discord.File('graph_figure.png'))

@bot.event
async def on_ready():


    #initializing scheduler
    scheduler = AsyncIOScheduler()

    #sends "Your Message" at 12PM and 18PM (Local Time)
    scheduler.add_job(scoreboard, CronTrigger(hour=HOUR, minute="0", second="0")) 

    #starting the scheduler
    scheduler.start()

@bot.command(name='score')
async def business(ctx):
    
    members = ctx.message.mentions
    f = open('user.json')
    users = json.load(f)
    for user in users["users"]:
        if user["discord_id"] == members[0].id: 
            if "minecraft" in user:
                finances = await getChests(user["minecraft"]["username"])
                icon = {}
                icon["business"] = discord.utils.get(bot.emojis, name = user["minecraft"]["icon-business"])
                score = 0
                line = ""
                for item in currency:
                    if "icon" in item:
                        line = f'{line}  {discord.utils.get(bot.emojis, name = item["icon"])}  {finances[item["name"]]}'
                        score = score + (finances[item["name"]] * item["points"])
                embedVar = discord.Embed(title=f"__**{user['minecraft']['username']}**__   ( {score:,} points )", color=user["minecraft"]["color"])
                embedVar.add_field(name=user["minecraft"]["business"]+f"  {icon['business']}",value=line)
                embedVar.set_thumbnail(url=user["minecraft"]["picture"])
                await ctx.send(embed=embedVar)
            else:
                await ctx.send("Ce joueur n'est pas coté en bourse.")


async def getChests(minecraftUsername):
    host = minecraft["host"]
    port = minecraft["port"]
    username = minecraft["username"]
    password = minecraft["password"]
    api = MinecraftApi.MinecraftJsonApi(host, port, username, password)
    
    
    f = open('user.json')
    users = json.load(f)

    finalResult = {}
    for user in users['users']:
        if "minecraft" in user:
            if user["minecraft"]["username"] == minecraftUsername:
                chestsData = []
                result = {}
                methods = []
                args = []
                for item in currency:
                    result[item["name"]] = 0
                
                for chest in user["minecraft"]["chests"]:
                    methods.append("world.getChestContents")
                    args.append([chest["maps"], chest["x"], chest["y"], chest["z"]])
                    
                data = api.call_multiple(methods,args)
                dataJson = data.decode('utf-8') 
                for inventory in json.loads(dataJson)["success"]:
                    for slot in inventory["success"]:
                        if slot:
                            for item in currency:
                                if slot["type"] == item["name"]:
                                    result[slot["type"]]= result[item["name"]]+slot["amount"]

                for item in currency:
                    if "parent" in item:
                        nb = result[item["name"]]
                        result[item["parent"]] = int(result[item["parent"]]) + (nb * 9)

                for item in currency:
                    if "icon" in item:
                        finalResult[item["name"]] = result[item["name"]]

                return finalResult


@bot.command(name='init_scoreboard')
async def init_scoreboard(ctx):
     await scoreboard()

@bot.command(name='steam')
async def steam(ctx):
    user =ctx.author.id
    f = open('user.json',)
    users = json.load(f)

    steam_id = 0
    for i in users['users']:
        if i["discord_id"] == user:
            steam_id = i["steam_id"]
        
    r = requests.get(url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="+STEAM_API_TOKEN+"&steamids="+str(steam_id))
    print(r) 
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

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


queues = {}

def check_queues(ctx, id):
    if queues[id] != []:
        voice = ctx.guild.voice_client
        source = queues[id].pop(0)
        player = voice.play(source, after=lambda x=None: check_queues(ctx, ctx.message.guild.id))

def getQuestion(id):
    f = open('questions.json',)
    questions = json.load(f)
    for element in enumerate(questions["questions"]):
        if element[1]["id"] == int(id):
            return element[1]

async def verifAnswer(answer):
    if queues[current_ctx["ctx"].message.guild.id] == []:
        if current_question["q"]["answers"][answer]["correct"]:
            guild_id = current_ctx["ctx"].message.guild.id
            await current_msg["msg"].delete()
            if len(questions_done) == 15:
                await game_win(current_ctx["ctx"])
            else:
                await nextQuestion(current_ctx["ctx"])
        else:
            i = 0
            for qu in current_question["q"]["answers"]:
                i = i+1
                if qu["correct"]:
                    break
            guild_id = current_ctx["ctx"].message.guild.id
            await current_msg["msg"].delete()
            await game_over(current_ctx["ctx"], i)
       
@bot.command()
async def sendQuestion(ctx, n_question):
    question = getQuestion(n_question)
    current_question["q"] = question
    embedVar = discord.Embed(title="__**Question "+str(len(questions_done))+"**__", color=0xcd2626)
    s = "\n :regional_indicator_a: "+question["answers"][0]["text"]+"\n :regional_indicator_b: "+question["answers"][1]["text"]+"\n :regional_indicator_c: "+question["answers"][2]["text"]+"\n :regional_indicator_d: "+question["answers"][3]["text"]
    embedVar.add_field(name=question["question"],value=s)
    embedVar.set_thumbnail(
        url="https://media.discordapp.net/attachments/494557667629727776/901060850180300810/test_pp.png"
    )
    msg = await ctx.send(embed=embedVar)
    current_msg["msg"] = msg


@bot.event
async def on_reaction_add(reaction, user):
    if user == current_ctx["ctx"].message.author:
        if str(reaction.emoji) == "🇦":
            await verifAnswer(0)
        if str(reaction.emoji) == "🇧":
            await verifAnswer(1)
        if str(reaction.emoji) == "🇨":
            await verifAnswer(2)
        if str(reaction.emoji) == "🇩":
            await verifAnswer(3)
 



@bot.command()
async def play(ctx):
    questions_done.clear()
    current_ctx["ctx"] = ctx
    n_question = random.randint(1,140)
    while n_question in questions_done:
        n_question = random.randint(1,140)
    questions_done.append(n_question)
    server = ctx.message.guild
    voice_channel = server.voice_client
    question  = getQuestion(n_question)

    async with ctx.typing():
        in_speech = 1
        filename = "speech/short-hello.mp3"
        voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda x=None: check_queues(ctx, ctx.message.guild.id) )
    await sendQuestion(ctx, n_question)
    await queue(ctx, n_question)
    msg = current_msg["msg"]
    await msg.add_reaction('🇦')
    await msg.add_reaction('🇧')
    await msg.add_reaction('🇨')
    await msg.add_reaction('🇩')




@bot.command()
async def nextQuestion(ctx):
    current_ctx["ctx"] = ctx
    n_question = random.randint(1,140)
    while n_question in questions_done:
        n_question = random.randint(1,140)
    questions_done.append(n_question)
    server = ctx.message.guild
    voice_channel = server.voice_client
    question  = getQuestion(n_question)

    async with ctx.typing():
        filename = "speech/rv.mp3"
        voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda x=None: check_queues(ctx, ctx.message.guild.id) )
    await sendQuestion(ctx, n_question)
    await queue(ctx, n_question)
    msg = current_msg["msg"]
    await msg.add_reaction('🇦')
    await msg.add_reaction('🇧')
    await msg.add_reaction('🇨')
    await msg.add_reaction('🇩')


@bot.command()
async def game_over(ctx, i):
    current_ctx["ctx"] = ctx
    server = ctx.message.guild
    voice_channel = server.voice_client
    filename = "speech/rx.mp3"
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda x=None: check_queues(ctx, ctx.message.guild.id) )
    questions_done.clear()
    await end_queue(ctx, i)

@bot.command()
async def game_win(ctx):
    current_ctx["ctx"] = ctx
    server = ctx.message.guild
    voice_channel = server.voice_client
    filename = "speech/victory.mp3"
    voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=lambda x=None: check_queues(ctx, ctx.message.guild.id) )
    questions_done = []
    await win_queue(ctx)

async def end_queue(ctx, i):
    voice = ctx.guild.voice_client
    song = ["speech/br.mp3", "speech/"+str(current_question["q"]["id"])+"-"+str(i)+".mp3"]
    for s in song:
        source = discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=s)
        guild_id = ctx.message.guild.id
        if guild_id in queues: 
            queues[guild_id].append(source)
        else:
            queues[guild_id] = [source]

async def win_queue(ctx, ):
    voice = ctx.guild.voice_client
    song = ["speech/win.mp3"]
    for s in song:
        source = discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=s)
        guild_id = ctx.message.guild.id
        if guild_id in queues: 
            queues[guild_id].append(source)
        else:
            queues[guild_id] = [source]

async def queue(ctx, n_question):
    voice = ctx.guild.voice_client
    song = ["speech/"+str(n_question)+".mp3", "speech/ra.mp3", "speech/"+str(n_question)+"-1.mp3", "speech/rb.mp3", "speech/"+str(n_question)+"-2.mp3", "speech/rc.mp3", "speech/"+str(n_question)+"-3.mp3", "speech/rd.mp3", "speech/"+str(n_question)+"-4.mp3"]

    for s in song:
        source = discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=s)

        guild_id = ctx.message.guild.id

        if guild_id in queues: 
            queues[guild_id].append(source)
        else:
            queues[guild_id] = [source]
    
        



bot.run(TOKEN)
