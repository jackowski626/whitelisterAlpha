#BOT invite link: https://discordapp.com/api/oauth2/authorize?client_id=689044268584796177&permissions=537918672&scope=bot
import discord
from discord.ext import commands
import json
import pprint
import types
import copy
import os
import http.client
import random
import paramiko
from fixedMcuuidAPI import GetPlayerData
from variables import *
from functions import *

#----------------------------------------------------
#Terminology and specific variables
##Guild: a Discord server, often, though, "server"/"servers" in the code indicate a Guild class variable or its id
##ctx: refers the most of the time to the "context" of an event. The context contains various informations on the event, like for example the user who issued it
##ASK_CHANNEL: This is a channel which should only contain the messsage of the bot where users can react to ask for being whitelisted
##WAITING_CHANNEL: The channel in which inquiries for being whitelisted are posted by the bot
##ASK_MESSAGE: The message in ASK_CHANNEL
##REFUSED_ASK_COMMAND_MESSAGE: If the user issues a !ask command while an ASK_MESSAGE is already present, the bot refuses to repost it. If the user issues !askOverride, the bot deletes all his refusal messages and the original !ask command. This is one of the messages he has to delete.
##REFUSED_ASK_COMMAND_CHANNEL: Related to REFUSED_ASK_COMMAND_ID
##REFUSED_BOT_ASK_COMMAND_MESSAGE: Related to REFUSED_ASK_COMMAND_ID
#----------------------------------------------------


#Initial steps of the bot
#Getting bots config file from FTP server
grabDB(DB_FILENAME)

#Getting prefixes from all registered guilds
prefixesDict = {};
prefixesList = []    
with open(DB_FILENAME) as json_file:
    data = json.load(json_file)
    for server in data["servers"]: #returns a dict where key is server id and value is its prefix
        prefixesDict[server] = data["servers"][server]["prefix"]
        prefixesList.append(data["servers"][server]["prefix"])

#Instantiating the bot with the prefix ist
bot = commands.Bot(command_prefix=prefixesList)

#WIP #The bot has (will have) a custom help command so the original one is removed
bot.remove_command("help")

#print("bot properties: "+pp.pformat(dir(bot)))
if DEBUG: print("bot properties: "+pp.pformat(bot.command_prefix))


########---------
#EVENTS
########---------

#Bot logs into console when ready
@bot.event
async def on_ready():
    if DEBUG: print(f'{bot.user} shall serve his master!'); return
    print(f'{bot.user} has connected to Discord!')

#An event that triggers when the bot is invited to a guild. The bot then pings the first admin role it can find and the owner of the guild in the first available text channel to inform about stuff. It also creates a new dictionnary in the database json for the server
@bot.event
async def on_guild_join(guild):
    grabDB(DB_FILENAME)
    with open(DB_FILENAME, 'r+') as json_file:
        data = json.load(json_file)
        #Add a new server entry to the json
        data["servers"][str(guild.id)] = {"server_id":guild.id,"prefix":DEFAULT_PREFIX,"hasPosted":"False","ASK_CHANNEL":"none","WAITING_CHANNEL":"none","ASK_MESSAGE":"none","REFUSED_ASK_COMMAND_CHANNEL":"none","REFUSED_ASK_COMMAND_MESSAGE":"none","REFUSED_BOT_ASK_COMMAND_MESSAGE":"none","privileged_roles":[],"usersWaitingForFtpHostConfirmation":[],"usersWaitingForFtpUserConfirmation":[],"usersWaitingForFtpPasswordConfirmation":[],"usersWaitingForFtpPathConfirmation":[],"usersWaitingForFtpPortConfirmation": [],"minecraftFTP":{"mode":"none","host":"none","user":"none","password":"none","path":"none","port":21},"usersWaitingForNicknameConfirmation":[],"hasRespondedWithValidUname":[],"hasRespondedWithValidUnameDict":{},"whitelistedUsers":[],"discordToMCdict":{}}
        #Send message which pings a role with admin privileges and says that the bot should be configured
        validRole = None
        for role in guild.roles:
            if role.permissions.administrator:
                data["servers"][str(guild.id)]["privileged_roles"].append(role.id)
                validRole = role
                break
        if validRole:
            await guild.text_channels[0].send(guild.owner.mention+" "+role.mention+" Bonjour, je viens d'arriver sur le serveur. Avant de pouvoir whitelister les membres de ce serveur, je devrai être configuré. Le rôle mentionné a été automatiquement ajouté aux rôles permettant d'exécuter les commandes administratives du bot, ainsi que whitelister les membres. Utilisez la commande _!addPrivileged_ ou _!removePrivileged_ pour ajouter ou supprimer des rôles de la liste des rôles privilégiés. Pour vous renseigner d'avantage sur ma configuration, exécutez la commande _!config_")
        else:
            await guild.text_channels[0].send(guild.owner.mention+" Bonjour, je viens d'arriver sur le serveur. Avant de pouvoir whitelister les membres de ce serveur, je devrai être configuré. Utilisez la commande _!addPrivileged_ ou _!removePrivileged_ pour ajouter ou supprimer des rôles de la liste des rôles privilégiés, ceux-ci pourront configurer le bot et ajouter ou supprimer des utilisateurs de la whitelist. Pour vous renseigner d'avantage sur ma configuration, exécutez la commande _!config_")
                #ping the owner
        writeJSON(data, json_file)
    placeDB(DB_FILENAME)

#An event that triggers when the bot gets kicked from a guild
@bot.event
async def on_guild_remove(guild):
    grabDB(DB_FILENAME)
    with open(DB_FILENAME, 'r+') as json_file:
        data = json.load(json_file)
        del data["servers"][str(guild.id)]
        writeJSON(data, json_file)
    placeDB(DB_FILENAME)

#Event that is triggered each time a reaction is added in a guild or private messages it can access
@bot.event
async def on_raw_reaction_add(reaction):
    #reaction object attributes: <RawReactionActionEvent message_id=688538146106900539 user_id=435446721485733908 channel_id=688454404621205584 guild_id=688445594125074501 emoji=<PartialEmoji animated=False name='✅' id=None>>

    #Ignore reactions added by the bot
    if reaction.user_id == bot.user.id:
        return

    if DEBUG: print("on_raw_reaction_add triggered")

    #Getting user object that made the reaction
    user = bot.get_user(reaction.user_id)
    
    #String, Discord tag of a user. Ex: johnSmith#1234
    fullUsername = user.name+"#"+user.discriminator

    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        if DEBUG: pass #print("Entering the on_react conditions with this json: "+pp.pformat(data))
        for server in data["servers"]:
            #If the reaction is in the ASK channnell, if yes, PM the user
            if reaction.channel_id == data["servers"][server]["ASK_CHANNEL"]:
                if DEBUG: print("le channel de la reaction est ASK_CHANNEL"+str(reaction.channel_id))
                messagee = await bot.get_channel(data["servers"][server]["ASK_CHANNEL"]).fetch_message(reaction.message_id)
                #Check if username not alrady in usersWaitingForNicknameConfirmation
                if user.id not in data["servers"][str(reaction.guild_id)]["usersWaitingForNicknameConfirmation"] and str(user.id) not in data["servers"][server]["discordToMCdict"]:
                    if DEBUG: print("user "+fullUsername+" not in UWFNC, adding")
                    #Append fullUsername to usersWaitingForNicknameConfirmation
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][str(reaction.guild_id)]["usersWaitingForNicknameConfirmation"].append(user.id)
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await user.send("Vous avez fait une demande de whitelist, veuillez répondre par votre nom d'utilisateur Minecraft exact")
            #If the reaction is in the WAITING_CHANNEL
            elif reaction.channel_id == data["servers"][server]["WAITING_CHANNEL"]:
                if DEBUG: print("le channel de la reaction est WAITING_CHANNEL"+str(reaction.channel_id))
                messagee = await bot.get_channel(data["servers"][server]["WAITING_CHANNEL"]).fetch_message(reaction.message_id)
                #Handle the case when the user cancels his whitelist request with the :no_entry_sign: emoji
                if str(reaction.emoji) == "🚫":
                    if DEBUG: print("emoji of reaction is 🚫 (the no entry sign)")
                    if user.mention in messagee.content:
                        messageDeDemande = await bot.get_channel(data["servers"][server]["ASK_CHANNEL"]).fetch_message(data["servers"][server]["ASK_MESSAGE"])
                        await messageDeDemande.remove_reaction("✅", user)
                        if DEBUG: print("The right user clicked on that")
                        grabDB(DB_FILENAME)
                        with open(DB_FILENAME, 'r+') as json_file:
                            data = json.load(json_file)
                            data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(user.id)
                            data["servers"][server]["hasRespondedWithValidUname"].remove(fullUsername)
                            del data["servers"][server]["hasRespondedWithValidUnameDict"][fullUsername]
                            writeJSON(data, json_file)
                        placeDB(DB_FILENAME)
                        await messagee.delete()
                        await bot.get_channel(reaction.channel_id).send("L'utilisateur " + bot.get_user(reaction.user_id).name + " a annulé sa demande.")
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)
                #Handle the case when a privileged role user rejects a whitelist request with the :x: emoji
                elif str(reaction.emoji) == "❌":
                    if DEBUG: print("emoji of reaction is ❌ (the cross)")
                    guild = bot.get_guild(reaction.guild_id)
                    if hasPerms(CustomCtx(guild, user)):
                        for member in guild.members:
                            tempUser = bot.get_user(member.id)
                            if tempUser.mention in messagee.content:
                                uname = tempUser.name+"#"+tempUser.discriminator
                                grabDB(DB_FILENAME)
                                with open(DB_FILENAME, 'r+') as json_file:
                                    data = json.load(json_file)
                                    data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(tempUser.id)
                                    data["servers"][server]["hasRespondedWithValidUname"].remove(uname)
                                    del data["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                    writeJSON(data, json_file)
                                placeDB(DB_FILENAME)
                                with open(DB_FILENAME) as json_file:
                                    data = json.load(json_file)
                                    await messagee.channel.send(tempUser.mention+", votre demande de whitelist a été rejetée. Veuillez vous addresser aux modérateurs avant de réappliquer. Plusieurs demandes consécutives peuvent mener à un ban.")
                                    await messagee.delete()
                                    messageDeDemande = await bot.get_channel(data["servers"][server]["ASK_CHANNEL"]).fetch_message(data["servers"][server]["ASK_MESSAGE"])
                                    await messageDeDemande.remove_reaction("✅", tempUser)
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)
                    #user attributes: <User id=435446721485733908 name='jackowski626' discriminator='0522' bot=False>
                #Handle the case when a privileged role user accepts a whitelist request with the :white_check_mark: emoji
                elif str(reaction.emoji) == "✅":
                    if DEBUG: print("emoji of reaction is ✅ (the tick)")
                    guild = bot.get_guild(reaction.guild_id)
                    memberCanAcceptWhitelist = False
                    if hasPerms(CustomCtx(guild, user)):
                        grabUuidsResponse = grabUuids(WHITELIST_FILENAME, guild.id)
                        if grabUuidsResponse[0] == "ok":
                            for member in guild.members:
                                tempUser = bot.get_user(member.id)
                                if tempUser.mention in messagee.content:
                                    uname = tempUser.name+"#"+tempUser.discriminator
                                    userid = member.id
                                    playername = ""
                                    grabDB(DB_FILENAME)
                                    with open(DB_FILENAME) as json_file:
                                        dataPlayer = json.load(json_file)
                                        playername = dataPlayer["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                    player = addHyphensToPlayer(GetPlayerData(playername))
                                    ingameName = player.username
                                    uuid = player.uuid
                                    with open(DB_FILENAME, 'r+') as json_file:
                                        data = json.load(json_file)
                                        data["servers"][server]["usersWaitingForNicknameConfirmation"].remove(tempUser.id)
                                        data["servers"][server]["hasRespondedWithValidUname"].remove(uname)
                                        data["servers"][server]["whitelistedUsers"].append(uname)
                                        del data["servers"][server]["hasRespondedWithValidUnameDict"][uname]
                                        data["servers"][server]["discordToMCdict"][userid] = {"DiscordTag":uname,"username":ingameName,"uuid":uuid}
                                        writeJSON(data, json_file)
                                    placeDB(DB_FILENAME)
                                    await messagee.channel.send(tempUser.mention+", votre demande de whitelist a été acceptée.")
                                    await messagee.delete()
                                    with open('whitelist.json', 'r+') as whitelist_file:
                                        whitelist = json.load(whitelist_file)
                                        whitelist.append({"uuid":uuid,"name": ingameName})
                                        writeJSON(whitelist, whitelist_file)
                                    placeUuids(WHITELIST_FILENAME, guild.id)
                        elif grabUuidsResponse[0] == "error":
                            await messagee.remove_reaction(reaction.emoji, user)
                            await messagee.channel.send("Erreur de permissions FTP. Les identifiants FTP du serveur Minecraft sont probablement non-valides.")
                        elif grabUuidsResponse[0] == "missingCredentials":
                            await messagee.remove_reaction(reaction.emoji, user)
                            credentialDict = {"host":"hôte","user":"utilisateur","password":"mot de passe","path":"chemin d'accès vers le fichier _whitelist.json_"}
                            missingCredentialsHR = ""
                            for i in range(len(grabUuidsResponse[1])):
                                missingCredentialsHR += (" "+credentialDict[grabUuidsResponse[1][i]])
                                if i < len(grabUuidsResponse[1])-1:
                                    missingCredentialsHR += ","
                            await messagee.channel.send("Les données de login FTP Minecraft suivantes sont manquantes: "+missingCredentialsHR+". Utilisez la commande _ftp_ pour en savoir plus")
                        else:
                            await messagee.remove_reaction(reaction.emoji, user)
                            await messagee.channel.send("Erreur d'écriture dans la whitelist, probablement liée à la connection FTP.")
                    else:
                        await messagee.remove_reaction(reaction.emoji, user)

#Reacting to regular messages, usef for direct message responses
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if isMessageFromDM(CustomCtx(message.guild, message.author)):
        fullUsername = message.author.name+"#"+message.author.discriminator
        #Check if username not alrady in usersWaitingForNicknameConfirmation
        grabDB(DB_FILENAME)
        with open(DB_FILENAME) as json_file:
            data = json.load(json_file)
            for server in data["servers"]:
                if message.author.id in data["servers"][server]["usersWaitingForNicknameConfirmation"] and fullUsername not in data["servers"][server]["hasRespondedWithValidUname"]:
                    #Check if username is registered at Mojang
                    player = addHyphensToPlayer(GetPlayerData(message.content))
                    if player.valid is True:
                        with open(DB_FILENAME, 'r+') as json_file:
                            data = json.load(json_file)
                            data["servers"][server]["hasRespondedWithValidUname"].append(fullUsername)
                            data["servers"][server]["hasRespondedWithValidUnameDict"][fullUsername] = message.content
                            writeJSON(data, json_file)
                        placeDB(DB_FILENAME)
                        with open(DB_FILENAME) as json_file:
                            data = json.load(json_file)
                            channel = bot.get_channel(data["servers"][server]["WAITING_CHANNEL"])
                            msg = await channel.send("L'utilisateur "+message.author.mention+" a demandé a être ajouté à la whitelist en tant que **"+message.content+"**. Il peut réagir avec :no_entry_sign: pour annuler sa demande. Un admin peut réagir avec :white_check_mark: ou :x: pour accepter ou refuser la demande, respectivement.")
                            await msg.add_reaction("✅")
                            await msg.add_reaction("❌")
                            await msg.add_reaction("🚫")
                    else:
                        await message.channel.send("Veuillez saisir un nom valide")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpModeConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpModeConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["mode"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("Le mode FTP a été changé en _"+message.content+"_")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpHostConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpHostConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["host"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("Le hôte FTP a été changé en _"+message.content+"_")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpUserConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpUserConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["user"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("L'utilisateur FTP a été changé en _"+message.content+"_")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpPasswordConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpPasswordConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["password"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("Le mot de passe FTP a été changé en _"+message.content[0]+"*"*len(message.content)+message.content[-1]+"_")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpPathConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpPathConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["path"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("Le chemin d'accès FTP au fichier whitelist.json a été changé en _"+message.content+"_")
                elif message.author.id in data["servers"][server]["usersWaitingForFtpPortConfirmation"]:
                    with open(DB_FILENAME, 'r+') as json_file:
                        data = json.load(json_file)
                        data["servers"][server]["usersWaitingForFtpPortConfirmation"].remove(message.author.id)
                        data["servers"][server]["minecraftFTP"]["port"] = message.content
                        writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await message.author.send("Le port FTP a été changé en _"+message.content+"_")
    else:
        pass
    await bot.process_commands(message)


########---------
#COMMANDS
########---------

#[Used for debugging] Command that logs the bot out
@bot.command(name="s")
async def on_message(ctx):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        await ctx.send(random.choice(["Arrivederci", "Goodnight girl, I'll see you tomorrow", "last seen online: 6 years ago", "stop! you can't ju"]))
        await bot.logout()

#Command which sends a message with Minecraft usernames present in the whitelist.json file
@bot.command(pass_context=True)
async def whitelist(ctx):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        #responseString = "Liste de membres dans la whitelist: "
        memberList = []
        grabUuids(WHITELIST_FILENAME, ctx.guild.id)
        grabDB(DB_FILENAME)
        with open(WHITELIST_FILENAME) as whitelist_file:
            whitelist = json.load(whitelist_file)
            for i in range(len(whitelist)):
                with open(DB_FILENAME) as json_file:
                    data = json.load(json_file)
                    for key in data["servers"][str(ctx.guild.id)]["discordToMCdict"]:
                        if DEBUG: print("name: "+whitelist[i]["name"])
                        if data["servers"][str(ctx.guild.id)]["discordToMCdict"][key]["username"] == whitelist[i]["name"]:
                            if DEBUG: print(pp.pformat(key))
                            if bot.get_user(int(key)):
                                memberList.append(bot.get_user(int(key)).name)
                            else:
                                memberList.append(data["servers"][str(ctx.guild.id)]["discordToMCdict"][key]["DiscordTag"]+" (user not on server)")
                            
        if len(memberList) > 0:
            joinSeparator = ", "
            await ctx.channel.send("Liste de membres dans la whitelist: "+joinSeparator.join(memberList))
        else:
            await ctx.channel.send("Il n'y pas de membres dans la whitelist")

#Command which sends a message cntaining information on how to change FTP credentials
@bot.command(pass_context=True)
async def ftp(ctx):
    if not isMessageFromDM(ctx):
        await ctx.channel.send("Pour changer le hôte FTP pour le serveur Minecraft, le nom d'utilisateur, le mot de passe et le chemin d'accès, utilisez ces commandes respectives: _host_, _user_, _password_, _path_.\nExemple d'utilisation: ```"+ctx.prefix+"path /htdocs/whitelist_test/minecraft```")

#Command which removes tagged Discord users from Minecraft whitelist.json file
@bot.command(pass_context=True)
async def removeFromWhitelist(ctx):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        if len(ctx.message.mentions) == 0:
            await ctx.channel.send("Vous devez taguer au moins un utilisateur")
            return
        server = str(ctx.guild.id)
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            messageDeDemande = await bot.get_channel(data["servers"][server]["ASK_CHANNEL"]).fetch_message(data["servers"][server]["ASK_MESSAGE"])
            for mention in ctx.message.mentions:
                user = bot.get_user(mention.id)
                userTag = user.name+"#"+user.discriminator
                userRemovedFrom = []
                for reaction in messageDeDemande.reactions:
                    if str(reaction.emoji) == "✅":
                        reactors = await reaction.users().flatten()
                        for i in range(len(reactors)):
                            if DEBUG: print("reactors['key'].id: "+pp.pformat(reactors[i].id))
                            if user.id == reactors[i].id:
                                await messageDeDemande.remove_reaction("✅", user)
                if userTag in data["servers"][server]["whitelistedUsers"]:
                    data["servers"][server]["whitelistedUsers"].remove(userTag)
                    userRemovedFrom = 1
                if str(user.id) in data["servers"][server]["discordToMCdict"]:
                    grabUuids(WHITELIST_FILENAME, server)
                    with open(WHITELIST_FILENAME, 'r+') as json_whitelist:
                        whitelist = json.load(json_whitelist)
                        toRemove = {"uuid":data["servers"][server]["discordToMCdict"][str(user.id)]["uuid"], "name":data["servers"][server]["discordToMCdict"][str(user.id)]["username"]}
                        if toRemove in whitelist:
                            whitelist.remove(toRemove)
                            writeJSON(whitelist, json_whitelist)
                            placeUuids(WHITELIST_FILENAME, ctx.guild.id)
                            del data["servers"][server]["discordToMCdict"][str(user.id)]
                            await ctx.channel.send("L'utilisateur "+user.name+" a été supprimé de la whitelist")
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
    placeDB(DB_FILENAME)

@bot.command(pass_context=True)
async def mode(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpModeConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpModeConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le mode de connection du serveur, _ftp_ ou _sftp_"+ctx.guild.name)
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])
@bot.command(pass_context=True)
async def host(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpHostConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpHostConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le nom d'hôte pour le serveur FTP Minecraft du serveur "+ctx.guild.name)
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])
@bot.command(pass_context=True)
async def user(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpUserConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpUserConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le nom d'utilisateur pour le serveur FTP Minecraft du serveur "+ctx.guild.name)
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])
@bot.command(pass_context=True)
async def password(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPasswordConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPasswordConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le mot de passe pour le serveur FTP Minecraft du serveur "+ctx.guild.name)
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])
@bot.command(pass_context=True)
async def path(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPasswordConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPasswordConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le chemin d'accès vers le fichier whitelist.json pour le serveur FTP Minecraft du serveur "+ctx.guild.name+". Si la whitelist est dans le root, répondez avec _/_")
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])
@bot.command(pass_context=True)
async def port(ctx):
    hasAnyPendingResponses = hasPendingResponses(ctx.author.id)
    if not hasAnyPendingResponses:
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                if ctx.author.id not in data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPortConfirmation"]:
                    data["servers"][str(ctx.guild.id)]["usersWaitingForFtpPortConfirmation"].append(ctx.author.id)
                    writeJSON(data, json_file)
                    placeDB(DB_FILENAME)
                    await ctx.author.send("Veuillez répondre avec le port d'accès pour le serveur FTP Minecraft du serveur "+ctx.guild.name+". Le port FTP par défaut est 21")
    else:
        await ctx.author.send("Vous devez déjà répondre avec un "+hasAnyPendingResponses[0]+" pour le serveur "+hasAnyPendingResponses[1])

#Command used to add roles to the privileged_roles list
@bot.command(pass_context=True)
async def addPrivileged(ctx, *, message):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            print("message "+message)
            for role in ctx.guild.roles:
                #print("hmm role")
                print("mention "+role.mention)
                if role.mention in message:
                    data["servers"][str(ctx.guild.id)]["privileged_roles"].append(role.id)
            writeJSON(data, json_file)
        placeDB(DB_FILENAME)
@addPrivileged.error
async def info_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        pass

#Command used to remove roles from the privileged_roles list
@bot.command(pass_context=True)
async def removePrivileged(ctx, *, message):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            for role in ctx.guild.roles:
                if role.mention in message and role.id in data["servers"][str(ctx.guild.id)]["privileged_roles"]:
                    data["servers"][str(ctx.guild.id)]["privileged_roles"].remove(role.id)
            writeJSON(data, json_file)
        placeDB(DB_FILENAME)
@removePrivileged.error
async def info_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        pass

#[Used for debugging] Command that resets the "hasPosted" field for each server to False
@bot.command()
async def resetAskJson(ctx):
    if DEBUG and not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            for server in data["servers"]:
                server = str(server)
                data["servers"][server]["hasPosted"] = "False"
            writeJSON(data, json_file)
            placeDB(DB_FILENAME)

#Command to send the ASK_MESSAGE message in current channel
@bot.command()
async def ask(ctx):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            if toBool(data["servers"][str(ctx.guild.id)]["hasPosted"]):
                msg_de_refus = await ctx.channel.send("Un message de demande de whitelist existe déjà sur ce serveur. Si ce n'est pas le cas, par exemple s'il a été supprimé lorsque le bot était hors-ligne, utilisez la commande _askOverride_")
                data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_CHANNEL"] = ctx.channel.id
                data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_MESSAGE"] = ctx.message.id
                data["servers"][str(ctx.guild.id)]["REFUSED_BOT_ASK_COMMAND_MESSAGE"] = msg_de_refus.id
            else:
                data["servers"][str(ctx.guild.id)]["hasPosted"] = "True"
                data["servers"][str(ctx.guild.id)]["ASK_MESSAGE"] = ctx.message.id   
                await ctx.message.delete()
                msg = await ctx.channel.send("Pour faire une demande de whitelist sur le serveur, réagis avec :white_check_mark:")
                data["servers"][str(ctx.guild.id)]["ASK_MESSAGE"] = msg.id
                await msg.add_reaction("✅")
            writeJSON(data, json_file)
        placeDB(DB_FILENAME)

#Command to force send the ASK_MESSAGE message in current channel
@bot.command()
async def askOverride(ctx):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        grabDB(DB_FILENAME)
        with open(DB_FILENAME, 'r+') as json_file:
            data = json.load(json_file)
            data["servers"][str(ctx.guild.id)]["hasPosted"] = "True"
            if data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_CHANNEL"] != "none":
                if data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_MESSAGE"] != "none":
                    try:
                        msg_to_delete = await bot.get_channel(data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_CHANNEL"]).fetch_message(data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_MESSAGE"])
                        await msg_to_delete.delete()
                    except discord.errors.NotFound:
                        print("message not found")
                if data["servers"][str(ctx.guild.id)]["REFUSED_BOT_ASK_COMMAND_MESSAGE"] != "none":
                    try:
                        msg_to_delete = await bot.get_channel(data["servers"][str(ctx.guild.id)]["REFUSED_ASK_COMMAND_CHANNEL"]).fetch_message(data["servers"][str(ctx.guild.id)]["REFUSED_BOT_ASK_COMMAND_MESSAGE"])
                        await msg_to_delete.delete()
                    except discord.errors.NotFound:
                        print("message not found")
            await ctx.message.delete()
            msg = await ctx.channel.send("Pour faire une demande de whitelist sur le serveur, réagis avec :white_check_mark:")
            data["servers"][str(ctx.guild.id)]["ASK_MESSAGE"] = msg.id
            writeJSON(data, json_file)
            await msg.add_reaction("✅")
        placeDB(DB_FILENAME)
                    
#[Used for debugging] Command that makes the bot send "hello" in current channel and prints info in the logs
@bot.command(pass_context=True)
async def say(ctx):
    if DEBUG: 
        print("ctx: "+pp.pformat(dir(ctx.channel)))
        if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix):
            await ctx.channel.send("hello")

#Command which lets a user with a privileged role change the prefix for the bot in the current guild
@bot.command(pass_context=True)
async def prefix(ctx, message):
    if not isMessageFromDM(ctx) and guildHasThisPrefix(ctx.guild.id, ctx.prefix) and hasPerms(ctx):
        if not " " in message:
            bot.command_prefix.remove(ctx.prefix)
            bot.command_prefix.append(message)
            if DEBUG: print("bot prefixes: "+pp.pformat(bot.command_prefix))
            grabDB(DB_FILENAME)
            with open(DB_FILENAME, 'r+') as json_file:
                data = json.load(json_file)
                data["servers"][str(ctx.guild.id)]["prefix"] = message
                writeJSON(data, json_file)
            placeDB(DB_FILENAME)
            await ctx.channel.send("Le préfixe a été changé en "+message)
        else:
            await ctx.channel.send("Le nouveau préfixe ne doit pas comporter d'espaces")
    else:
        await ctx.channel.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande")

#Handling the error when no prefix is specified at prefix command use
@prefix.error
async def info_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        print("Bad argument(s) for prefix command")

#Running the bot
bot.run(TOKEN)