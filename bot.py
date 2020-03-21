#BOT invite link: https://discordapp.com/api/oauth2/authorize?client_id=689044268584796177&permissions=8&scope=bot
import discord
from discord.ext import commands
import json
import pprint
import types
import copy
import ftplib
from ftplib import FTP
import os
import http.client
import random
from fixedMcuuidAPI import GetPlayerData 

debug = False

pp = pprint.PrettyPrinter(indent=4)
TOKEN = "Njg5MDQ0MjY4NTg0Nzk2MTc3.XnHDHQ.DXkV6IuB7VKKuhtOg09xSC4es2Y"
db_filename = "alphadb.json"
default_prefix = "!"


class CustomCtx:
  def __init__(self, guild, user):
    self.guild = guild
    self.author = user

def grabDB(name):
    if debug: print("grabDB("+name+")")
    ftp = FTP('ftpupload.net')
    ftp.login(user = 'epiz_24969303', passwd = 'W4qR0HzfL5GK3')
    ftp.cwd('/htdocs/whitelist_test')
    filename = name
    localfile = open(filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    ftp.quit()
    localfile.close()
def placeDB(name):
    if debug: print("placeDB("+name+")")
    ftp = FTP('ftpupload.net')
    ftp.login(user = 'epiz_24969303', passwd = 'W4qR0HzfL5GK3')
    ftp.cwd('/htdocs/whitelist_test')
    filename = name
    ftp.storbinary('STOR '+filename, open(filename, 'rb'))
    ftp.quit()
def grabUuids(name, guild_id):
    if debug: print("grabUuids("+name+", "+str(guild_id)+")")
    minecraftFTP = {}
    grabDB(db_filename)
    with open(db_filename) as json_file:
        data = json.load(json_file)
        minecraftFTP = data["servers"][str(guild_id)]["minecraftFTP"]
    noneCredentialsList = []
    for detail in minecraftFTP:
        if minecraftFTP[detail] == "none":
            noneCredentialsList.append(detail)
    if len(noneCredentialsList) > 0:
        return ["missingCredentials", noneCredentialsList]
    if debug: print("Connecting to ftp with:",minecraftFTP["user"],minecraftFTP["password"],minecraftFTP["path"])
    ftp = FTP(minecraftFTP["host"])
    try:
        ftp.login(user = minecraftFTP["user"], passwd = minecraftFTP["password"])
        ftp.cwd(minecraftFTP["path"])
        filename = name
        localfile = open(filename, 'wb')
        ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
        ftp.quit()
        localfile.close()
        return ["ok"]
    except ftplib.error_perm:
        return ["error"]
        """with open(db_filename) as json_file:
            data = json.load(json_file)
            await bot.get_channel(data["servers"][str(guild_id)]["EN_SUSPENS_CHANNEL"]).send("Erreur de permissions FTP. Les identifiants FTP du serveur Minecraft sont probablement non-valides.")"""
    
def placeUuids(name, guild_id):
    if debug: print("placeUuids("+name+", "+str(guild_id)+")")
    minecraftFTP = {}
    grabDB(db_filename)
    with open(db_filename) as json_file:
        data = json.load(json_file)
        minecraftFTP = data["servers"][str(guild_id)]["minecraftFTP"]
    ftp = FTP(minecraftFTP["host"])
    try:
        ftp.login(user = minecraftFTP["user"], passwd = minecraftFTP["password"])
        ftp.cwd(minecraftFTP["path"])
        filename = name
        ftp.storbinary('STOR '+filename, open(filename, 'rb'))
        ftp.quit()
    except ftplib.error_perm:
        with open(db_filename) as json_file:
            data = json.load(json_file)
            bot.get_channel(data["servers"][str(guild_id)]).send("Erreur de permissions FTP. Les identifiants FTP du serveur Minecraft sont probablement non-valides.")

def writeJSON(data, json_file):
    if debug: print("writingJSON("+pp.pformat(data)+", "+pp.pformat(json_file)+")")
    json_file.seek(0)
    json.dump(data, json_file, indent=4)
    json_file.truncate()

def addHyphensToPlayer(player):
    player.uuid = player.uuid[0:8]+"-"+player.uuid[8:12]+"-"+player.uuid[12:16]+"-"+player.uuid[16:20]+"-"+player.uuid[20:32]
    return player

###############################################################################
grabDB(db_filename)

prefixesDict = {};
prefixesList = []    
with open(db_filename) as json_file:
    data = json.load(json_file)
    for server in data["servers"]: #returns a dict where key is server id and value is its prefix
        prefixesDict[server] = data["servers"][server]["prefix"]
        prefixesList.append(data["servers"][server]["prefix"])


bot = commands.Bot(command_prefix=prefixesList)

def hasPerms(ctx):
    hasPerms = False
    guild = ctx.guild#bot.get_guild(GUILDE_ID)
    grabDB(db_filename)
    with open(db_filename) as json_file:
        data = json.load(json_file)
        for member in guild.members:
            for role in member.roles:
                if role.id in data["servers"][str(guild.id)]["privileged_roles"] and member.id == ctx.author.id:
                    hasPerms = True
    return hasPerms

def getServerFromPrefix(prefix):
    grabDB(db_filename)
    with open(db_filename) as json_file:
        data = json.load(json_file)
        for server in data["servers"]:
            if data["servers"][server]["prefix"] == prefix:
                return int(server)

def isMessageFromDM(ctx):
    if ctx.guild is None:
        return True
    return False

def commandFromGoodServer(ctx):
    if ctx.guild.id == getServerFromPrefix(ctx.prefix):
        return True
    else:
        return False

def toBool(val):
    if str(val) == "True":
        return True
    return False

"""def userHasPendingCommands(user_id):
    grabDB(db_filename)
    with open(db_filename) as json_file:
        data = json.load(json_file)
        ds = data["servers"]
        for s in ds:
            if user_id in ds[s]["usersWaitingForFtpHostConfirmation"] or user_id in ds[s]["usersWaitingForFtpUserConfirmation"] or user_id in ds[s]["usersWaitingForFtpHostConfirmation"] or user_id in ds[s]["usersWaitingForFtpHostConfirmation"] //lastPoint"""

@bot.command(name="s")
async def on_message(ctx):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        await ctx.send(random.choice(["Arrivederci", "Goodnight girl, I'll see you tomorrow", "last seen online: 6 years ago", "stop! you can't ju"]))
        await bot.logout()

@bot.command(pass_context=True)
async def w(ctx):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        #responseString = "Liste de membres dans la whitelist: "
        memberList = []
        grabUuids("whitelist.json", ctx.guild.id)
        grabDB(db_filename)
        with open("whitelist.json") as whitelist_file:
            whitelist = json.load(whitelist_file)
            for i in range(len(whitelist)):
                with open(db_filename) as json_file:
                    data = json.load(json_file)
                    #print("jpp "+pp.pformat(data))
                    for key in data["servers"][str(ctx.guild.id)]["discordToMCdict"]:
                        print("name: "+whitelist[i]["name"])
                        if data["servers"][str(ctx.guild.id)]["discordToMCdict"][key]["username"] == whitelist[i]["name"]:
                            print(pp.pformat(key))
                            memberList.append(bot.get_user(int(key)).name)
                    #memberList.append(data["servers"][str(ctx.guild.id)]["discordToMCdict"])
        joinSeparator = ", "
        await ctx.channel.send("Liste de membres dans la whitelist: "+joinSeparator.join(memberList))

@bot.command(pass_context=True)
async def ftp(ctx):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx):
        await ctx.channel.send("Pour changer le hôte FTP pour le serveur Minecraft, le nom d'utilisateur, le mot de passe et le chemin d'accès, utilisez ces commandes respectives: _host_, _user_, _password_, _path_.\nExemple d'utilisation: ```"+ctx.prefix+"path /htdocs/whitelist_test/minecraft```")

@bot.command(pass_context=True)
async def removeFromWhitelist(ctx):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        if len(ctx.message.mentions) == 0:
            await ctx.channel.send("Vous devez taguer au moins un utilisateur")
            return
        server = str(ctx.guild.id)
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            messageDeDemande = await bot.get_channel(data["servers"][server]["DEMANDER_CHANNEL"]).fetch_message(data["servers"][server]["MESSAGE_DE_DEMANDE_ID"])
            for mention in ctx.message.mentions:
                user = bot.get_user(mention.id)
                userTag = user.name+"#"+user.discriminator
                userRemovedFrom = []
                for reaction in messageDeDemande.reactions:
                    #print("reaction users attributes: "+pp.pformat(dir(reaction.users)))
                    #print("reaction users hmm: "+pp.pformat(reaction.users()))
                    if str(reaction.emoji) == "✅":
                        reactors = await reaction.users().flatten()
                        for i in range(len(reactors)):
                            if debug: print("reactors['key'].id: "+pp.pformat(reactors[i].id))
                            if user.id == reactors[i].id:
                                await messageDeDemande.remove_reaction("✅", user)
                if userTag in data["servers"][server]["whitelistedUsers"]:
                    data["servers"][server]["whitelistedUsers"].remove(userTag)
                    userRemovedFrom = 1
                if str(user.id) in data["servers"][server]["discordToMCdict"]:
                    grabUuids("whitelist.json", server)
                    with open("whitelist.json", 'r+') as json_whitelist:
                        whitelist = json.load(json_whitelist)
                        toRemove = {"uuid":data["servers"][server]["discordToMCdict"][str(user.id)]["uuid"], "name":data["servers"][server]["discordToMCdict"][str(user.id)]["username"]}
                        if toRemove in whitelist:
                            whitelist.remove(toRemove)
                            writeJSON(whitelist, json_whitelist)
                            placeUuids("whitelist.json", ctx.guild.id)
                            del data["servers"][server]["discordToMCdict"][str(user.id)]
                            await ctx.channel.send("L'utilisateur a été supprimé de la whitelist")
                        else:
                            if str(user.id) in data["servers"][server]["discordToMCdict"]:
                                del data["servers"][server]["discordToMCdict"][str(user.id)]
                                userRemovedFrom = 1
                            if userRemovedFrom:
                                await ctx.channel.send("L'utilisateur "+user.name+" n'est pas présent dans la whitelist, mais des éléments liés à lui dans la base de données ont été supprimées")
                            else:
                                await ctx.channel.send("L'utilisateur "+user.name+" n'est pas présent dans la whitelist")
                else:
                    await ctx.channel.send("L'utilisateur "+user.name+" n'est pas présent dans la whitelist")
            writeJSON(data, json_file)
    placeDB(db_filename)
"""@bot.command(pass_context=True)

async def host(ctx,*,message):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            data["servers"][str(ctx.guild.id)]["minecraftFTP"]["host"] = message
            writeJSON(data, json_file)
        placeDB(db_filename)"""

@bot.command(pass_context=True)
async def host(ctx):
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpHostConfirmation"]:
                data["servers"][str(ctx.guild.id)]["usersWaitingForFtpHostConfirmation"].append(ctx.author.id)
                writeJSON(data, json_file)
                placeDB(db_filename)
                ctx.user.send("Veuillez répondre avec le nom d'hôte pour le serveur FTP Minecraft du serveur "+ctx.guild.name)
            else:
                await ctx.channel.send("Vous avez déjà effectué une demande pour cette commande")



"""@bot.command(pass_context=True)
async def host(ctx,*,message):
    if commandFromGoodServer(ctx) and hasPerms(ctx):
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            data["servers"][str(ctx.guild.id)]["minecraftFTP"]["host"] = message
            writeJSON(data, json_file)
        placeDB(db_filename)"""
    
@host.error
async def info_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.channel.send("Veuillez indiquer un nom d'hôte")
"""@bot.event
async def on_guild_join(guild):
    grabDB(db_filename)
    with open(db_filename, 'r+') as json_file:
        data = json.load(json_file)"""


@bot.event
async def on_ready():
    print(f'{bot.user} shall serve his master!')


#handle reactions
@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.user_id == bot.user.id:
        return
    if debug: print("on_raw_reaction_add triggered")

    user = bot.get_user(reaction.user_id)
    
    #member = bot.get_member(reaction.user_id)
    if user == bot.user:
        return
    fullUsername = user.name+"#"+user.discriminator

    #pm user if reacts in demandes
    grabDB(db_filename)
    """with open(db_filename) as test:
        test2 = json.load(test)
        print("have written JSON, alphadb is: "+pp.pformat(test2))"""
    with open(db_filename) as json_file2:
        data2 = json.load(json_file2)
        data = data2
        if debug: print("Entering the on_react conditions with this json: "+pp.pformat(data))
        for server in data["servers"]:
            #print("channel id: "+str(reaction.channel_id))
            #print("hmm data data: "+pp.pformat(data))
            #print("hmm data servers: "+pp.pformat(data["servers"][server]["DEMANDER_CHANNEL"]))
            #print("hmm data servers server: "+pp.pformat(data["servers"][server]["DEMANDER_CHANNEL"]))
            #print("hmm data all: "+pp.pformat(data["servers"][server]["DEMANDER_CHANNEL"]))
            #print(str(reaction.channel_id)+" and "+str(data["servers"][server]["DEMANDER_CHANNEL"]))
            if reaction.channel_id == data2["servers"][server]["DEMANDER_CHANNEL"]:
                if debug: print("le channel de la reaction est DEMANDER_CHANNEL")
                messagee = await bot.get_channel(data["servers"][server]["DEMANDER_CHANNEL"]).fetch_message(reaction.message_id)
            #print("channel: "+pp.pformat(reaction))
            #reaction attributes: <RawReactionActionEvent message_id=688538146106900539 user_id=435446721485733908 channel_id=688454404621205584 guild_id=688445594125074501 emoji=<PartialEmoji animated=False name='✅' id=None>>
                #check if username not alrady in usersWaitingForNicknameConfirmation
                if fullUsername not in data["servers"][str(reaction.guild_id)]["usersWaitingForNicknameConfirmation"] and str(user.id) not in data["servers"][server]["discordToMCdict"]:
                    print("user "+fullUsername+" not in UWFNC, adding")
                    #append that to usersWaitingForNicknameConfirmation
                    with open(db_filename, 'r+') as json_file:
                        data = json.load(json_file)
                        #data['hasPosted'] = "True"
                        data["servers"][str(reaction.guild_id)]["usersWaitingForNicknameConfirmation"].append(fullUsername)
                        writeJSON(data, json_file)
                    placeDB(db_filename)
                    await user.send("Vous avez fait une demande de whitelist, veuillez répondre par votre nom d'utilisateur Minecraft exact")
            #demandes en suspens, annuler
            elif reaction.channel_id == data["servers"][server]["EN_SUSPENS_CHANNEL"]:
                if debug: print("le channel de la reaction est EN_SUSPENS_CHANNEL")
                messagee = await bot.get_channel(data["servers"][server]["EN_SUSPENS_CHANNEL"]).fetch_message(reaction.message_id)
                if str(reaction.emoji) == "🚫":
                    if debug: print("emoji of reaction is 🚫 (the no entry sign)")
                    #await bot.get_channel(EN_SUSPENS_CHANNEL).send("vous avez réagi avec: "+pp.pformat(reaction.emoji))
                    #await bot.get_channel(EN_SUSPENS_CHANNEL).send("reaction.user_id is: "+pp.pformat(reaction.user_id))
                    if user.mention in messagee.content:
                        messageDeDemande = await bot.get_channel(data["servers"][server]["DEMANDER_CHANNEL"]).fetch_message(data["servers"][server]["MESSAGE_DE_DEMANDE_ID"])
                        await messageDeDemande.remove_reaction("✅", user)
                        print("The right user clicked on that")
                        grabDB(db_filename)
                        with open(db_filename, 'r+') as json_file:
                            data = json.load(json_file)
                            data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(fullUsername)
                            data["servers"][server]["hasRespondedWithValidUname"].remove(fullUsername)
                            del data["servers"][server]["hasRespondedWithValidUnameDict"][fullUsername]
                            writeJSON(data, json_file)
                        placeDB(db_filename)
                        await messagee.delete()
                        await bot.get_channel(reaction.channel_id).send("L'utilisateur " + bot.get_user(reaction.user_id).name + " a annulé sa demande.")
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)
                #reject by an admin
                elif str(reaction.emoji) == "❌":
                    if debug: print("emoji of reaction is ❌ (the cross)")
                    guild = bot.get_guild(reaction.guild_id)
                    if hasPerms(CustomCtx(guild, user)):
                        for member in guild.members:
                            tempUser = bot.get_user(member.id)
                            if tempUser.mention in messagee.content:
                                uname = tempUser.name+"#"+tempUser.discriminator
                                grabDB(db_filename)
                                with open(db_filename, 'r+') as json_file:
                                    data = json.load(json_file)
                                    data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(uname)
                                    data["servers"][server]["hasRespondedWithValidUname"].remove(uname)
                                    del data["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                    writeJSON(data, json_file)
                                placeDB(db_filename)
                                with open(db_filename) as json_file:
                                    data = json.load(json_file)
                                    await messagee.channel.send(tempUser.mention+", votre demande de whitelist a été rejetée. Veuillez vous addresser aux modérateurs avant de réappliquer. Plusieurs demandes consécutives peuvent mener à un ban.")
                                    await messagee.delete()
                                    messageDeDemande = await bot.get_channel(data["servers"][server]["DEMANDER_CHANNEL"]).fetch_message(data["servers"][server]["MESSAGE_DE_DEMANDE_ID"])
                                    await messageDeDemande.remove_reaction("✅", tempUser)
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)
                    #user attributes: <User id=435446721485733908 name='jackowski626' discriminator='0522' bot=False>
                elif str(reaction.emoji) == "✅":
                    if debug: print("emoji of reaction is ✅ (the tick)")
                    guild = bot.get_guild(reaction.guild_id)
                    memberCanAcceptWhitelist = False
                    #customCtx = {"guild":guild, "author":{"id":user.id}}
                    if hasPerms(CustomCtx(guild, user)):
                        grabUuidsResponse = grabUuids("whitelist.json", guild.id)
                        if grabUuidsResponse[0] == "ok":
                            for member in guild.members:
                                tempUser = bot.get_user(member.id)
                                if tempUser.mention in messagee.content:
                                    uname = tempUser.name+"#"+tempUser.discriminator
                                    userid = member.id
                                    playername = ""
                                    grabDB(db_filename)
                                    with open(db_filename) as json_file:
                                        dataPlayer = json.load(json_file)
                                        playername = dataPlayer["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                    player = addHyphensToPlayer(GetPlayerData(playername))

                                    ingameName = player.username
                                    uuid = player.uuid
                                    with open(db_filename, 'r+') as json_file:
                                        data = json.load(json_file)
                                        data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(uname)
                                        data["servers"][server]["hasRespondedWithValidUname"].remove(uname)
                                        data["servers"][server]["whitelistedUsers"].append(uname)
                                        del data["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                        data["servers"][server]["discordToMCdict"][userid] = {"DiscordTag":uname,"username":ingameName,"uuid":uuid}
                                        writeJSON(data, json_file)
                                    placeDB(db_filename)
                                    
                                    
                                    await messagee.channel.send(tempUser.mention+", votre demande de whitelist a été acceptée.")
                                    await messagee.delete()
                                #print("grabbed uuids, whitelist is: "+pp.pformat())
                                    with open('whitelist.json', 'r+') as whitelist_file:
                                        #textfile = str()
                                        whitelist = json.load(whitelist_file)
                                        whitelist.append({"uuid":uuid,"name": ingameName})
                                        writeJSON(whitelist, whitelist_file)
                                    placeUuids("whitelist.json", guild.id)
                        elif grabUuidsResponse[0] == "error":
                            await messagee.remove_reaction(reaction.emoji, user)
                            await messagee.channel.send("Erreur de permissions FTP. Les identifiants FTP du serveur Minecraft sont probablement non-valides.")
                        elif grabUuidsResponse[0] == "missingCredentials":
                            await messagee.remove_reaction(reaction.emoji, user)
                            credentialDict = {"host":"hôte","user":"utilisateur","password":"mot de passe","path":"chemin d'accès vers le fichier _whitelist.json_"}
                            missingCredentialsHR = ""
                            for i in range(len(grabUuidsResponse[1])):
                                #print(dir(element))
                                missingCredentialsHR += (" "+credentialDict[grabUuidsResponse[1][i]])
                                if i < len(grabUuidsResponse[1])-1:
                                    missingCredentialsHR += ","

                            await messagee.channel.send("Les données de login FTP Minecraft suivantes sont manquantes: "+missingCredentialsHR+". Utilisez la commande _ftp_ pour en savoir plus")
                        else:
                            await messagee.remove_reaction(reaction.emoji, user)
                            await messagee.channel.send("Erreur d'écriture dans la whitelist, probablement liée à la connection FTP.")
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)
#attendre la réponse en dm
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if str(message.channel)[0:6] == "Direct":
        #await message.channel.send("Ce channel est un DM")
        fullUsername = message.author.name+"#"+message.author.discriminator
        #check if username not alrady in usersWaitingForNicknameConfirmation
        grabDB(db_filename)
        with open(db_filename) as json_file:
            data = json.load(json_file)
            for server in data["servers"]:
                if fullUsername in data["servers"][server]["usersWaitingForNicknameConfirmation"] and fullUsername not in data["servers"][server]["hasRespondedWithValidUname"]:
                    #check if username is valid
                    player = addHyphensToPlayer(GetPlayerData(message.content))
                    if player.valid is True:
                        with open(db_filename, 'r+') as json_file:
                            data = json.load(json_file)
                            data["servers"][server]["hasRespondedWithValidUname"].append(fullUsername)
                            data["servers"][server]["hasRespondedWithValidUnameDict"][fullUsername] = message.content
                            writeJSON(data, json_file)
                        placeDB(db_filename)
                        with open(db_filename) as json_file:
                            data = json.load(json_file)
                            channel = bot.get_channel(data["servers"][server]["EN_SUSPENS_CHANNEL"])
                            msg = await channel.send("L'utilisateur "+message.author.mention+" a demandé a être ajouté à la whitelist en tant que **"+message.content+"**. Il peut réagir avec :no_entry_sign: pour annuler sa demande. Un admin peut réagir avec :white_check_mark: ou :x: pour accepter ou refuser la demande, respectivement.")
                            await msg.add_reaction("✅")
                            await msg.add_reaction("❌")
                            await msg.add_reaction("🚫")
                    else:
                        await message.channel.send("Veuillez saisir un nom valide")
                
    else:
        pass
    await bot.process_commands(message)

@bot.command()
async def resetDemandeJson(ctx):
    grabDB(db_filename)
    with open(db_filename, 'r+') as json_file:
        data = json.load(json_file)
        for server in data["servers"]:
            server = str(server)
            data["servers"][server]["hasPosted"] = "False"
        writeJSON(data, json_file)
        placeDB(db_filename)

@bot.command()
async def demande(ctx): #place a demande message in current channel
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            if toBool(data["servers"][str(ctx.guild.id)]["hasPosted"]):
                msg_de_refus = await ctx.channel.send("Un message de demande de whitelist existe déjà sur ce serveur. Si ce n'est pas le cas, par exemple s'il a été supprimé lorsque le bot était hors-ligne, utilisez la commande _demandeOverride_")
                data["servers"][str(ctx.guild.id)]["CHANNEL_DES_MSGS_REFUSES"] = ctx.channel.id
                data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_COMMANDE_DEMANDE_REFUSEE"] = ctx.message.id
                data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_DE_REFUS_DE_COMMANDE_DU_BOT"] = msg_de_refus.id
            else:
                data["servers"][str(ctx.guild.id)]["hasPosted"] = "True"
                data["servers"][str(ctx.guild.id)]["MESSAGE_DE_DEMANDE_ID"] = ctx.message.id   
                await ctx.message.delete()
                msg = await ctx.channel.send("Pour faire une demande de whitelist sur le serveur, réagis avec :white_check_mark:")
                data["servers"][str(ctx.guild.id)]["MESSAGE_DE_DEMANDE_ID"] = msg.id
                await msg.add_reaction("✅")
            writeJSON(data, json_file)
        placeDB(db_filename)

@bot.command()
async def demandeOverride(ctx): #place a demande message in current channel
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        grabDB(db_filename)
        with open(db_filename, 'r+') as json_file:
            data = json.load(json_file)
            data["servers"][str(ctx.guild.id)]["hasPosted"] = "True"
            #data["servers"][str(ctx.guild.id)]["MESSAGE_DE_DEMANDE_ID"] = ctx.message.id
            if data["servers"][str(ctx.guild.id)]["CHANNEL_DES_MSGS_REFUSES"] != "none":
                if data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_COMMANDE_DEMANDE_REFUSEE"] != "none":
                    #print("askip coroutine: "+pp.pformat(dir(bot.get_channel(data["servers"][str(ctx.guild.id)]["CHANNEL_DES_MSGS_REFUSES"]).fetch_message(data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_COMMANDE_DEMANDE_REFUSEE"]))))
                    try:
                        msg_to_delete = await bot.get_channel(data["servers"][str(ctx.guild.id)]["CHANNEL_DES_MSGS_REFUSES"]).fetch_message(data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_COMMANDE_DEMANDE_REFUSEE"])
                        await msg_to_delete.delete()
                    except discord.errors.NotFound:
                        print("message not found")
                if data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_DE_REFUS_DE_COMMANDE_DU_BOT"] != "none":
                    try:
                        msg_to_delete = await bot.get_channel(data["servers"][str(ctx.guild.id)]["CHANNEL_DES_MSGS_REFUSES"]).fetch_message(data["servers"][str(ctx.guild.id)]["DERNIER_MESSAGE_DE_REFUS_DE_COMMANDE_DU_BOT"])
                        await msg_to_delete.delete()
                    except discord.errors.NotFound:
                        print("message not found")
            await ctx.message.delete()
            msg = await ctx.channel.send("Pour faire une demande de whitelist sur le serveur, réagis avec :white_check_mark:")
            data["servers"][str(ctx.guild.id)]["MESSAGE_DE_DEMANDE_ID"] = msg.id
            writeJSON(data, json_file)
            await msg.add_reaction("✅")
            #print("id before placing: "+str(data["servers"][str(ctx.guild.id)]["MESSAGE_DE_DEMANDE_ID"]))
        placeDB(db_filename)
                    

@bot.command(pass_context=True)
async def say(ctx):
    print("ctx: "+pp.pformat(dir(ctx.channel)))
    #print("ctx prefix"+ctx.prefix)
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx):
        await ctx.channel.send("hello")

@bot.command(pass_context=True)
async def prefix(ctx,*,message):
    """hasPerms = False
    guild = bot.get_guild(GUILDE_ID)        
    for member in guild.members:
        for role in member.roles:
            if role.id == techicienRoleID or role.id == administrateurRoleID or role.id == ModerateurRoleID:
                if member.id == ctx.author.id:
                    hasPerms = True"""
    if not isMessageFromDM(ctx) and commandFromGoodServer(ctx) and hasPerms(ctx):
        if not " " in message:
            bot.command_prefix = message
            grabDB(db_filename)
            with open(db_filename, 'r+') as json_file:
                data = json.load(json_file)
                data["prefix"] = message
                writeJSON(data, json_file)
            placeDB(db_filename)
            await ctx.channel.send("Le préfixe a été changé en "+message)
        else:
            await ctx.channel.send("Le nouveau préfixe ne doit pas comporter d'espaces")
    else:
        await ctx.channel.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande")

@prefix.error
async def info_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        print("Bad argument(s) for prefix command")
        #await ctx.send('I could not find that member...')

bot.run(TOKEN)
