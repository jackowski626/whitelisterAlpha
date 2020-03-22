from variables import *
import ftplib
from ftplib import FTP
import json
import pprint
import copy
import os
import http.client
import random
import paramiko
from fixedMcuuidAPI import GetPlayerData

#There are situations in which functions which require a ctx object are needed but no ctx is present. In that case, a "fake" ctx is created and passed as argument instead
class CustomCtx:
  def __init__(self, guild, user):
    self.guild = guild
    self.author = user

#Function that gets the bot configuration JSON file from a remote FTP location
def grabDB(name):
    if DEBUG: print("grabDB("+name+")")
    ftp = FTP('ftpupload.net')
    ftp.login(user = 'epiz_24969303', passwd = 'W4qR0HzfL5GK3')
    ftp.cwd('/htdocs/whitelist_test')
    filename = name
    localfile = open(filename, 'wb')
    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)
    ftp.quit()
    localfile.close()

#Function that sends the bot configuration JSON file to a remote FTP location
def placeDB(name):
    if DEBUG: print("placeDB("+name+")")
    ftp = FTP('ftpupload.net')
    ftp.login(user = 'epiz_24969303', passwd = 'W4qR0HzfL5GK3')
    ftp.cwd('/htdocs/whitelist_test')
    filename = name
    ftp.storbinary('STOR '+filename, open(filename, 'rb'))
    ftp.quit()

#Function that gets the whitelist JSON file from a remote FTP location. Ii uses configurable credentials and connects to an FTP server with Minecraft server files, usually
def grabUuids(name, guild_id):
    if DEBUG: print("grabUuids("+name+", "+str(guild_id)+")")
    minecraftFTP = {}
    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        minecraftFTP = data["servers"][str(guild_id)]["minecraftFTP"]
    noneCredentialsList = []
    for detail in minecraftFTP:
        if minecraftFTP[detail] == "none":
            noneCredentialsList.append(detail)
    if len(noneCredentialsList) > 0:
        return ["missingCredentials", noneCredentialsList]
    if DEBUG: print("Connecting to ftp with:",minecraftFTP["user"],minecraftFTP["password"],minecraftFTP["path"])
    if minecraftFTP["mode"] == "ftp":
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
    elif minecraftFTP["mode"] == "sftp":
        host, port = minecraftFTP["host"], minecraftFTP["port"]
        transport = paramiko.Transport((host,port))
        sftp = paramiko.SFTPClient.from_transport(transport)
        filepath = ""
        if minecraftFTP["path"][-1] == "/":
            filepath = minecraftFTP["path"]+WHITELIST_FILENAME
        else:
            filepath = minecraftFTP["path"]+"/"+WHITELIST_FILENAME
        localpath = "./"+WHITELIST_FILENAME
        sftp.get(filepath, localpath)

#Function that sends the whitelist JSON file to a remote FTP location. Ii uses configurable credentials and connects to an FTP server with Minecraft server files, usually
def placeUuids(name, guild_id):
    if DEBUG: print("placeUuids("+name+", "+str(guild_id)+")")
    minecraftFTP = {}
    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        minecraftFTP = data["servers"][str(guild_id)]["minecraftFTP"]
    if minecraftFTP["mode"] == "ftp":
        ftp = FTP(minecraftFTP["host"])
        try:
            ftp.login(user = minecraftFTP["user"], passwd = minecraftFTP["password"])
            ftp.cwd(minecraftFTP["path"])
            filename = name
            ftp.storbinary('STOR '+filename, open(filename, 'rb'))
            ftp.quit()
        except ftplib.error_perm:
            with open(DB_FILENAME) as json_file:
                data = json.load(json_file)
                bot.get_channel(data["servers"][str(guild_id)]).send("Erreur de permissions FTP. Les identifiants FTP du serveur Minecraft sont probablement non-valides.")
    elif minecraftFTP["mode"] == "sftp":
        host, port = minecraftFTP["host"], minecraftFTP["port"]
        transport = paramiko.Transport((host,port))
        sftp = paramiko.SFTPClient.from_transport(transport)
        filepath = ""
        if minecraftFTP["path"][-1] == "/":
            filepath = minecraftFTP["path"]+WHITELIST_FILENAME
        else:
            filepath = minecraftFTP["path"]+"/"+WHITELIST_FILENAME
        localpath = "./"+WHITELIST_FILENAME
        sftp.get(localpath, filepath)

#Function that writes from variable to file on the disk. It is called writeJSON because for now, each use of it writes to a JSON file.
def writeJSON(data, json_file):
    if DEBUG: print("writingJSON("+pp.pformat(data)+", "+pp.pformat(json_file)+")")
    json_file.seek(0)
    json.dump(data, json_file, indent=4)
    json_file.truncate()

#The GetPlayerData function returns uuids without hyphens. The whitelist.json that a Minecraft server uses, however, needs it to have hyphens at specific places and addHyphensToPlayer adds them
def addHyphensToPlayer(player):
    player.uuid = player.uuid[0:8]+"-"+player.uuid[8:12]+"-"+player.uuid[12:16]+"-"+player.uuid[16:20]+"-"+player.uuid[20:32]
    return player

#Function that returns T/F depending if the user that issued the ctx has a role that is in the list of roles with privileges. In the JSON file, this entry is "privileged_roles"
def hasPerms(ctx):
    if ctx.author == ctx.guild.owner:
        return True
    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        for member in ctx.guild.members:
            for role in member.roles:
                if role.id in data["servers"][str(ctx.guild.id)]["privileged_roles"] and member.id == ctx.author.id:
                    return True
    return False

#Function that checks if the message was sent as direct message to the bot
def isMessageFromDM(ctx):
    if ctx.guild is None:
        return True
    return False

#Function that pseudo-casts a string to boolean
def toBool(val):
    if str(val) == "True":
        return True
    return False

#Functions that checks if the prefix which a command has been issued with is the prefix in a given guild
def guildHasThisPrefix(guild_id, prefix):
    guild_id = str(guild_id)
    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        if prefix == data["servers"][guild_id]["prefix"]:
            return True
    return False

#WIP #Function that checks if the user does not have a pending response to the bot (for example issued the host command but didn't respond to the bot)
waitingResponsesDict = {"usersWaitingForNicknameConfirmation":"nom d'utilisateur Minecraft", "usersWaitingForFtpModeConfirmation":"mode ftp ou sftp","usersWaitingForFtpHostConfirmation":"hôte FTP","usersWaitingForFtpUserConfirmation":"nom d'utilisateur FTP","usersWaitingForFtpPasswordConfirmation":"mot de passe FTP","usersWaitingForFtpPathConfirmation":"chemin d'accès au fichier whitelist.json"}
def hasPendingResponses(user_id):
    grabDB(DB_FILENAME)
    with open(DB_FILENAME) as json_file:
        data = json.load(json_file)
        for server in data["servers"]:
            for key in waitingResponsesDict:
                if user_id in data["servers"][server][key]:
                    print("the user has pending stuff",waitingResponsesDict[key], bot.get_guild(int(server)).name)
                    return (waitingResponsesDict[key], bot.get_guild(int(server)).name)
    return False