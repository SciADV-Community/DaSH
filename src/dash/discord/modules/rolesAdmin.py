import logging
from discord import Embed, PermissionOverwrite
from discord.ext import commands
from dash.discord.modules.rolesSQL import *

modName = ""

# Logger
log = logging.getLogger()
con = logging.StreamHandler()

log.addHandler(con)
log.setLevel(logging.WARN)
# TODO: Finish converting to log on modules

class rolesAdmin(commands.Cog):
    def __init__(self, client):
        self.client = client
        global modName
        modName = self.__class__.__name__

        # Check that each guild has its own database already
        for i in client.guilds:
            result = verifyGuild(i)
            if result == 1:
                initGuild(i)

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
        if not await isAuthorized(ctx, "addgame", 0): return

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
        if not await isAuthorized(ctx, "getgames", 0): return

        # Extract names from the game list
        games = getGames(ctx.guild)
        games = [game[0] for game in games]

        # If there are games...
        if len(games) is not 0:
            embed = Embed(color=0xe98530)
            embed.add_field(name="Configured games on {}".format(ctx.guild.name), value="\n".join(games), inline=False)
            # TODO: Sort Database descending
            await ctx.send(embed=embed)
        else:
            await ctx.send("No games currently configured for this server!")

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def rmgame(self, ctx, *gameName):
        if not await isAuthorized(ctx, "rmgame", 0): return

        gameName = " ".join(gameName)

        rmRole(ctx.guild, gameName, "*")
        rows = rmGame(ctx.guild, gameName)

        if rows is not 0:
            await ctx.send("{} removed successfully!".format(gameName))
        else:
            await ctx.send("Game does not exist, try again!")

## Role Commands ##
    # REWRITE COMPLETE
    # TODO: Address bug where roleName without quotes will create multiple roles. May need to turn creation off.
    @commands.command(pass_content=True)
    async def addrole(self, ctx, gameName, roleName, *reqs):
        if not await isAuthorized(ctx, "addrole", 0): return

        reqs = list(reqs)

        if gameName == "*":
            gameObj = gameName
        else:
            gameObj = getGames(ctx.guild, gameName)

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

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def listroles(self, ctx, *gameName):
        if not await isAuthorized(ctx, "getroles", 0): return
        gameName = " ".join(gameName)

        roleList = getRole(ctx.guild, gameName)

        if len(roleList) != 0:
            if gameName == "*": gameName = "Series Roles"

            embed = Embed(title=gameName, description="Role list", color=0xcb6326)

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
        if not await isAuthorized(ctx, "rmrole", 0): return

        rows = rmRole(ctx.guild, gameName, role)

        if rows == 0:
            await ctx.send("{} does not contain {} or the {} has no roles added.".format(gameName, role, gameName))
        else:
            if role == "*": role = "All roles"
            await ctx.send("{} removed from {} roles.".format(role, gameName))

    @commands.command(pass_context=True)
    async def repair(self, ctx, gameName, user):
        try:
            userID = int(''.join(num for num in user if num.isdigit()))
            user = get(ctx.guild.members, id=userID)

            if user == None:
                await ctx.send("User ID lookup failed.")
                return

            game = getGames(ctx.guild, gameName)

            if game == None:
                await ctx.send("Game not found. Please try again.")
                return

            gameList = getUserGames(ctx.guild, userID)
            gameList = [session for session in gameList if session[1] == gameName]

            if not gameList:
                playCatObj = get(ctx.guild.categories, name=game[4])
                await ctx.channel.edit(category=playCatObj, sync_permissions=True)

                overwrite = PermissionOverwrite()
                overwrite.update(read_messages=True, send_message_history=True, send_messages=True, manage_messages=True)
                await ctx.channel.set_permissions(user, overwrite=overwrite)

                setUserGame(ctx.guild, str(userID), gameName, str(ctx.channel.id))
                await ctx.send("Channel added to active games for {}".format(user.name))
            else:
                await ctx.send("Game already exists:\n" +
                               "UserID = "+ str(gameList[0][0]) + "\n" +
                               "Game Name = " + str(gameList[0][1]) + "\n" +
                               "RoomID = " + str(gameList[0][2]))
        except Exception as e:
            print(e)

## Permission Commands ##
## Permissions are stored as [UserID][PermissionValue]

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def auth(self, ctx, *role):
        if not await isAuthorized(ctx, "auth", 1): return

        # Retrieve role from database, get obj
        oldRole = getAuthorized(ctx.guild)[0]
        role = " ".join(role)
        authRole = get(ctx.guild.roles, name=role)

        if not authRole:
            await ctx.send("Invalid role specified for authorized group!")
            return
        else:
            if oldRole:
                rmAuthorized(ctx.guild, oldRole[0][0])
            setAuthorized(ctx.guild, authRole, 0)
            await ctx.send("**{}** set as authorized group.".format(authRole.name))

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def getauth(self, ctx):
        if not await isAuthorized(ctx, "getauth", 1): return

        # 0=role, 1=owner, 2=admin
        authID = getAuthorized(ctx.guild)
        idList = [[], [], []]

        # Get role name
        if len(authID[0]) > 0:
            role = get(ctx.guild.roles, id=authID[0][0])
            idList[0].append(role.name)
        else:
            idList[0].append(None)

        # Get owner name
        if len(authID[1]) > 1:
            owner = get(ctx.guild.members, id=authID[1][0])
            idList[1].append(owner.nick)
        else:
            idList[1].append(None)


        # Get admin name(s)
        if len(authID[2]) > 1:
            for user in authID[2]:
                admin = get(ctx.guild.members, id=user)
                if admin is not None:
                    idList[2].append(admin.nick)
        else:
            idList[2].append(None)
            log.warning("NO ADMIN FOUND IN DATABASE."
                        " YOU MAY WANT TO CHECK YOUR LOG FILE")

        # If this table is large, we don't want the duplicate
        del authID

        # Craft embed
        embed = Embed(title="Authorized Users", color=0xcb6326)
        if idList[2] is not None:
            embed.add_field(name="Admin(s)", value="\n".join(idList[2]), inline=False)
        else:
            embed.add_field(name="Admin(s)", value="None", inline=False)

        if idList[1] is not None:
            embed.add_field(name="Owner", value=idList[1][0], inline=False)
        else:
            embed.add_field(name="Owner", value="None", inline=False)

        if idList[2] is not None:
            embed.add_field(name="Role", value=idList[0][0], inline=False)
        else:
            embed.add_field(name="Role", value="None", inline=False)

        await ctx.send(embed=embed)

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def deauth(self, ctx):
        if not await isAuthorized(ctx, "deauth", 1): return

        authRole = getAuthorized(ctx.guild)[0]

        if len(authRole) > 0:
            roleName = get(ctx.guild.roles, id=authRole[0])
            rmAuthorized(ctx.guild, authRole[0])
            await ctx.send("Deauthorized **{}**.".format(roleName))
        else:
            await ctx.send("Currently no authorized group.")

def setup(client):
    client.add_cog(rolesAdmin(client))