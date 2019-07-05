from discord.ext import commands
from discord.utils import get
from modules.rolesSQL import *
import os, shutil, sqlite3, discord

modName = ""

instructions = "This room has been created for your playthrough of {}.\n" \
               "For a list of chapters type `$chapter` list.\n" \
                "When you have finished the game, type `$finished` and the room will be moved.\n\n" \
                "Please note that commands will only function in your playthrough room, " \
                "and that you can only have one playthrough room at any given time."



class rolesUser():
    def __init__(self, client):
        self.client = client
        self.instructions = instructions
        global modName
        modName = self.__class__.__name__

        print("{}: loaded successfully".format(modName))


    @commands.command(pass_context=True)
    async def start(self, ctx, *game):
        game = (" ".join(game)).lower() # Merge args for single string
        games = listGames(ctx.guild, 0) # Get full game list from DB

        # if the 'game' isn't 'list' or empty, and it's a valid game in the DB
        if game != "list" and game != "":
            if game in games:
                if (len(getUserGame(ctx.guild, ctx.author.id)) == 0):
                    inst = getGame(ctx.guild, game) # Get the game from the database

                    # Verify category exists in the guild, get ref objects for them
                    # inst[3] is playCat, the category holding current playthroughs
                    if not await verifyCategory(ctx, inst[3], ctx.guild.categories): return

                    category = get(ctx.guild.categories, name=inst[3])

                    # Create user room role, user room. Grab ref for room
                    room = await ctx.guild.create_text_channel(name=ctx.author.display_name + inst[1], category=category)

                    # Give user access to their own room
                    await room.set_permissions(ctx.author, overwrite=returnOwner(True))

                    # Post instructions in room and pin it
                    instructions = await room.send(self.instructions.format(inst[0]))
                    await instructions.pin()

                    # Set user game in the database, confirm completion to user
                    setUserGame(ctx.guild, ctx.author.id, game, room.id)
                    await ctx.send("Game room has been created: " + room.mention, delete_after=30)
                else:
                    await ctx.send("You already have a room!", delete_after=10)
            else:
                await ctx.send("Game does not exist, try again or `$start list` for game list!", delete_after=10)
        elif len(games) is not 0:
            await ctx.send("Configured games are: \n" + ", ".join(games), delete_after=15)
        elif len(games) is 0:
            await ctx.send("No games currently configured for this server!", delete_after=10)


    @commands.command(pass_context=True)
    async def chapter(self, ctx, *chapter: str):
        chapter = " ".join(chapter)                         # Merge args for single string
        userGame = getUserGame(ctx.guild, ctx.author.id)    # Get sender's game
        gameRoles = []

        # If a valid game entry is returned
        if len(userGame) != 0:
            # If the message is sent from the user's playthrough room
            if (userGame[2] == ctx.channel.id):
                gameRoles = getRoles(ctx.guild, userGame[1])
                purgeRoles = bool(getGame(ctx.guild, userGame[1])[5])

                # Command without args
                if chapter == "list" or not chapter:
                    embed = discord.Embed(title="DaSH 1st Edition Ver. 1.19", description="Chapter list",
                                          color=0xcb6326)
                    embed.set_thumbnail(url="https://i.imgur.com/8ye4OJZ.png")

                    for i in gameRoles:
                        role = i[0]
                        if len(i) > 1:
                            i.pop(0)
                            reqs = "Requires: " +  ", ".join(i)
                        else: reqs = "Requires: None"
                        embed.add_field(name=role, value=reqs,  inline=False)

                    embed.set_footer(text="Use 'help' with a command for usage info.")
                    await ctx.send(embed=embed)

                # Command with args
                else:
                    try: result = [i for i in gameRoles if i[0] == chapter][0]
                    except IndexError: result = None

                    if result:
                        roleObj = []
                        for i in result: roleObj.append(get(ctx.guild.roles, name=i))
                    else:
                        await ctx.send("Chapter {} does not exist!".format(chapter), delete_after=10)
                        return

                    chapter = roleObj[0]

                    if ctx.author in chapter.members:
                        await ctx.send("You already completed this chapter!", delete_after=10)
                        return

                    missing = []
                    possess = []
                    roleObj.pop(0)
                    if len(roleObj) > 0:
                        for i in roleObj:
                            if ctx.author in i.members:
                                possess.append(i)
                            else:
                                missing.append(i)

                    if len(missing) == 0:
                        await ctx.author.add_roles(chapter)
                        await ctx.send("Role assigned!")
                        if purgeRoles == True:
                            for i in possess: await ctx.author.remove_roles(i)
                    else:
                        embed = discord.Embed(title="Missing requirements for role",
                                              color=0xcb6326)
                        for i in missing: embed.add_field(name="Role: " + chapter.name, value="Req: " + i.name,
                                                          inline=False)
                        await ctx.send(embed=embed, delete_after=20)
            else:
                await ctx.send("This command must be sent from your playthrough channel.", delete_after=10)

    @commands.command(pass_context=True)
    async def finished(self, ctx, *game):
        userGame = getUserGame(ctx.guild, ctx.author.id) # Get user's game from DB
        game = " ".join(game).lower()

        # If user has game, and then sending channel matches their game channel
        # TODO: FIX BUG WHEN USER DOES $FINISH <GAME> FROM THEIR PLAY ROOM
        if (len(userGame) != 0):
            if (userGame[2] == ctx.channel.id):
                # Get channels from guild, games from database
                channel =  ctx.channel
                games = listGames(ctx.guild)

                # Get the game the channel is for, then get the object for the finished channel
                game = list(i for i in games if i[0] == userGame[1])[0]
                category = list(i for i in ctx.guild.categories if i.name == game[4])[0]

                # Give user complRole from game in database
                complRoleObj = get(ctx.guild.roles, name=game[2])
                await ctx.author.add_roles(complRoleObj)

                # Remove player from players table
                rmUserGame(ctx.guild, ctx.author.id)

                # Move channel to Finished Category and sync its permissions
                await channel.edit(category=category, sync_permissions=True)
                await ctx.send("You have been granted the completion role.\n"
                               "The channel has been moved to the finished category.")

                # Remove all of the games roles from the user. Try even if they don't have them
                roleList = getRoles(ctx.guild, userGame[1])
                for i in roleList:
                    roleObj = get(ctx.guild.roles, name=str(i[0]))
                    await ctx.author.remove_roles(roleObj)

                # TODO: ASYNC METHOD
                # Check if any series roles are valid for this game
                seriesRoles = getSRoles(ctx.guild)
                if any(complRoleObj.name in row for row in seriesRoles): # Check if obj is in any seriesRoles rows
                    rows = [row for row in seriesRoles if complRoleObj.name in row] # Get list of applicable rows
                    userRoles = [i.name for i in ctx.author.roles] # Clean list of user roles
                    for row in rows:# Loop through rows containing it.
                        seriesRoleObj = get(ctx.guild.roles, name=row[0]) # Get object for parent seriesRole
                        if len(row) > 1:
                            del row[0] # We have this one so remove it for the comparison
                            if all(elem in userRoles for elem in row): # Check if all of the roles in row in user roles
                                await ctx.author.add_roles(seriesRoleObj)

            else:
                await ctx.send("This command must be sent from your playthrough channel.", delete_after=10)
        else:
            # For when user doesn't have a game active
            games = listGames(ctx.guild, 0)
            if game in games:
                game = getGame(ctx.guild, game)
                gameRole = get(ctx.guild.roles, name=game[2])
                await ctx.author.add_roles(gameRole)
                await ctx.send("Game role added!", delete_after=10)

                # Get completion role
                complRoleObj = get(ctx.guild.roles, name=game[2])
                seriesRoles = getSRoles(ctx.guild)

                # Check for completed series roles
                if any(role for role in seriesRoles if complRoleObj.name in role):
                    userRoles = [i.name for i in ctx.author.roles]
                    for i in seriesRoles:
                        role = i.pop(0)
                        if set(i).issubset(userRoles):
                            role = get(ctx.guild.roles, name=role)
                            await ctx.author.add_roles(role)

            else:
                await ctx.send("Game does not exist!", delete_after=10)

async def verifyCategory(ctx, complCat, guildCats):
    if isinstance(complCat, str):
        if not any(complCat == str(guildCats[x]) for x in range(len(guildCats))):
            await ctx.send("N O P E ! Category {} doesn't exist!".format(complCat))
            return False
        else:
            return True
    else: raise  ValueError('complCat not instance of str')

def getObj(obj, objName):
    for i in obj:
        if i.name == objName:
            return i
    return None

def returnOverwrite(type):
    overwrite = discord.PermissionOverwrite()
    if type == True:
        overwrite.update(read_messages=True, send_message_history=True, send_messages=True)
    elif type == False:
        overwrite.update(read_messages=False, send_message_history=False, send_messages=False)
    else:
        raise TypeError

    return overwrite

def returnOwner(type):
    overwrite = discord.PermissionOverwrite()
    if type == True:
        overwrite.update(read_messages=True, send_message_history=True, send_messages=True, manage_messages=True)
    elif type == False:
        overwrite.update(read_messages=True, send_message_history=True, send_messages=False, manage_messages=False)
    else:
        raise TypeError

    return overwrite

def setup(client):
    client.add_cog(rolesUser(client))