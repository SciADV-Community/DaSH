from discord import Embed
from discord.ext import commands
from modules.rolesSQL import *

modName = ""

# Logger
log = logging.getLogger()
con = logging.StreamHandler()

log.addHandler(con)
log.setLevel(logging.WARN)

class rolesAdmin():
    def __init__(self, client):
        self.client = client
        global modName
        modName = self.__class__.__name__


        # Check that each guild has its own database already
        for i in client.guilds:
            result = verifyGuild(i)
            if result == 1:
                initGuild(i)


        #[verifyPath(i) for i in client.guilds]

        print("{}: loaded successfully".format(modName))

##########################
## Authorization Levels ##
## 0 = Authorized       ##
## 1 = Server Owner     ##
## 2 = Admin            ##
##########################

## Game Commands ##

## TODO: Add "verify" for DB check as well as commands to modify games on the back end

    #REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def addgame(self, ctx, gameName, gameAlias, complRole, chnlSuffix, playCat, complCat, purgeRole):
        if await isAuthorized(ctx, "addgame") == 0: return

        result = addGame(ctx.guild, gameName, gameAlias.lower(), complRole, chnlSuffix.lower(), playCat, complCat, purgeRole)

        if result is 0:
            if get(ctx.guild.roles, name=complRole) is None: await ctx.guild.create_role(name=complRole)
            if get(ctx.guild.categories, name=playCat) is None: await ctx.guild.create_category(name=playCat)
            if get(ctx.guild.categories, name=complCat) is None: await ctx.guild.create_category(name=complCat)

            log.info("Added game {} in guild {}.".format(gameName, ctx.guild.name))
            await ctx.send("{} added successfully!".format(gameName))

        else:
            await ctx.send("{} already exists!".format(gameName))

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def listgames(self,ctx):
        if await isAuthorized(ctx, "listgames") == 0: return

        games = "\n ".join(listGames(ctx.guild, 0))

        # If there are games...
        if len(games) is not 0:
            await ctx.send(embed=embedMSG("Configured games on {}".format(ctx.guild.name), games, 0xe98530))
        else:
            await ctx.send("No games currently configured for this server!")

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def rmgame(self, ctx, *gameName):
        if await isAuthorized(ctx, "rmgame") == 0: return

        gameName = " ".join(gameName)

        rmRole(ctx.guild, gameName, "*")
        rows = rmGame(ctx.guild, gameName)

        if rows is not 0:
            await ctx.send("{} removed successfully!".format(gameName))
        else:
            await ctx.send("Game does not exist, try again!")

## Role Commands ##
    # REWRITE COMPLETE
    @commands.command(pass_content=True)
    async def addrole(self, ctx, gameName, roleName, *reqs):
        if await isAuthorized(ctx, "addrole") == 0: return

        reqs = list(reqs)

        try:
            if gameName == "*":
                gameObj = gameName
            else:
                gameObj = getGame(ctx.guild, gameName)

            if gameObj is not None:
                roles = [roleName] + reqs

                for role in roles:
                    if get(ctx.guild.roles, name=role) == None:
                        await ctx.guild.create_role(name=role)
                        await ctx.send('Created "{}" role as it did not exist'.format(role))

                result = addRole(ctx.guild, gameName, roleName, reqs)

                if result == 1:
                    await ctx.send('Role "{}" added successfully!'.format(roleName))
                else:
                    await ctx.send('Role "{}" could not be added.'.format(roleName))

            else:
                await ctx.send('"{}" is not a valid game. Please check gamelist and try again.'.format(gameName))
                return

        except Exception as e:
            print(e)

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def listroles(self, ctx, *gameName):
        if await isAuthorized(ctx, "listroles") == 0: return
        gameName = " ".join(gameName)

        roleList = getRoles(ctx.guild, gameName)

        if len(roleList) != 0:
            if gameName == "*": gameName = "Series Roles"

            embed = Embed(title=gameName, description="Role list", color=0xcb6326)
            embed.set_thumbnail(url="https://i.imgur.com/8ye4OJZ.png")

            for row in roleList:
                if row[2] == "":
                    embed.add_field(name=row[1], value="None", inline=False)
                else:
                    embed.add_field(name=row[1], value=", ".join(row[2]), inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send('No roles found for game "{}"!'.format(gameName))

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def rmrole(self, ctx, gameName, role):
        if await isAuthorized(ctx, "rmrole") == 0: return

        rows = rmRole(ctx.guild, gameName, role)

        if rows == 0:
            await ctx.send("{} does not contain {} or the {} has no roles added.".format(gameName, role, gameName))
        else:
            if role == "*": role = "All roles"
            await ctx.send("{} removed from {} roles.".format(role, gameName))

## Permission Commands ##

    @commands.command(pass_context=True)
    async def auth(self, ctx, role):
        if await isAuthorized(ctx, "auth") != 2:
            await ctx.send("Only Admin/Owner can set auth!")
            return

        print('break 1')

        try: oldRole = getAuthorized(ctx.guild)[1]
        except IndexError: oldRole = None

        authRole = await objByName(ctx.guild.roles, role)
        if not authRole:
            await ctx.send("Invalid role specified for authorized group!")
            return
        else:
            if oldRole:
                rmAuthorized(ctx.guild, oldRole[0][0])
            setAuthorized(ctx.guild, authRole, 'group')
            await ctx.send("**{}** set as authorized group.".format(authRole.name))


    @commands.command(pass_context=True)
    async def getauth(self, ctx):
        if await isAuthorized(ctx, "auth") != 2:
            await ctx.send("Only Admin/Owner can get auth!")
            return

        try: authRole = getAuthorized(ctx.guild)[1]
        except IndexError: authRole = None

        if authRole:
            await ctx.send("Current authorized group is **{}**.".format(authRole[0]))
        else:
            await ctx.send("No current authorized group.")

    @commands.command(pass_context=True)
    async def deauth(self, ctx):
        if await isAuthorized(ctx, "auth") != 2:
            await ctx.send("Only Admin/Owner can deauth!")
            return

        try: authRole = getAuthorized(ctx.guild)[1]
        except IndexError: authRole = None

        if authRole:
            print(authRole[0][0])
            rmAuthorized(ctx.guild, authRole[0])
            await ctx.send("Deauthorized **{}**.".format(authRole[0]))
        else:
            await ctx.send("Currently no authorized group.")


## TODO: Add function for manually adding user games

## Functions ##
async def objByID(obj, objID):
    for i in obj:
        if i.id == objID:
            return i
    return None

async def objByName(obj, objName):
    for i in obj:
        if i.name == objName:
            return i
    return None

async def verifyName(ctx, type, obj, objName):
    result = await objByName(obj, objName)
    if not result:
        if type == "category": obj = await ctx.guild.create_category(name=objName)
        if type == "role"    : obj = await ctx.guild.create_role(name=objName)
        await ctx.send("Created {} as it did not exist".format(objName))
        return obj
    else:
        return 1

def embedMSG(msgName, msg, msgColor):
    embed = Embed(color=msgColor)
    embed.add_field(name=msgName, value=msg, inline=False)
    return embed

def setup(client):
    client.add_cog(rolesAdmin(client))