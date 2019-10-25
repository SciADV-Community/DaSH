import os
import shutil
import sqlite3
import discord
from discord.ext import commands
from discord.utils import get
from .rolesSQL import *

modName = ""

instructions = "This room has been created for your playthrough of {}.\n" \
               "For a list of chapters type `$chapter` list.\n" \
                "When you have finished the game, type `$finished` and the room will be moved.\n\n" \
                "Please note that commands will only function in your playthrough room, " \
                "and that you can only have one playthrough room at any given time."


class rolesUser(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.instructions = instructions
        global modName
        modName = self.__class__.__name__

        print("{}: loaded successfully".format(modName))

    # REWRITE COMPLETE
    @commands.command(pass_context=True)
    async def start(self, ctx, *game):
        game = (" ".join(game))

        # TODO: Set up a process for games made only to "$finished" (like for anime)
        # Get list of games (name only)
        gameTable = getGames(ctx.guild)

        if game == "list" or game == "":
            await ctx.send("Configured games are: \n" + ", ".join([gameName[0] for gameName in gameTable]))
            return
        else: # If game is the gameName or gameAlias for a game
            if (game.lower() in (gameName[0].lower() for gameName in gameTable)) or (game.lower() in (gameName[1].lower() for gameName in gameTable)):
                activeGames = [game[1] for game in getUserGames(ctx.guild, ctx.author.id)]
                if game not in activeGames:
                    # Get the row where the user specifies either gameName or gameAlias
                    for gameRow in gameTable:
                        if game.lower() == gameRow[0].lower() or game.lower() == gameRow[1].lower():
                            gameInst = gameRow

                    # Verify game category exists
                    categories = [category.name for category in ctx.guild.categories]

                    if gameInst[4] not in categories:
                        await ctx.send("N O P E ! Category {} doesn't exist!".format(gameInst[4]))
                        return

                    # Get category, make room, set perms, pin instructions
                    category = get(ctx.guild.categories, name=gameInst[4])
                    room = await ctx.guild.create_text_channel(name=ctx.author.display_name + gameInst[3], category=category)

                    ownerPerm = discord.PermissionOverwrite(read_messages=True, read_message_history=True, send_messages=True, manage_messages=True)
                    await room.set_permissions(ctx.author, overwrite=ownerPerm)

                    instructions = await room.send(self.instructions.format(gameInst[1]))
                    await instructions.pin()

                    # Assign room, confirm with user
                    setUserGame(ctx.guild, ctx.author.id, gameInst[0], room.id)
                    await ctx.send("Game room has been created: " + room.mention, delete_after=30)
                    return
                else:
                    await ctx.send("You already have a {} room!".format(game))
                    return
            else:
                await ctx.send("Game does not exist, try again or `$start list` for game list!")
                return

    @commands.command(pass_context=True)
    async def chapter(self, ctx, *chapter: str):
        chapter = str(" ".join(chapter))

        # Get game for context channel.
        activeGames = getUserGames(ctx.guild, ctx.author.id)
        activeGame = [game[1] for game in activeGames if game[2] == ctx.channel.id]

        if len(activeGame) == 1:
            gameRoles = getRole(ctx.guild, activeGame[0])

            if chapter == "" or chapter == "list":
                # Build embed out of roles
                embed = discord.Embed(title="Role List for {}".format(activeGame[0]),
                                      description="-"*len("Role List for {}".format(activeGame[0])) ,
                                      color=0xcb6326)
                # Loop through each role, make listing for role and reqs
                for role in gameRoles:
                    if len(role[2]) == 0:
                        embed.add_field(name=role[1], value="Requires: None", inline=False)
                    else:
                        embed.add_field(name=role[1], value="Requires: " + ", ".join(role[2]), inline=False)

                await ctx.send(embed=embed)
                return

            else:
                if len(activeGame) == 1:
                    # TODO: Clear out string fixes for role[1] once sqlite direct read is gone

                    # TODO: Verify this isn't broken
                    # Get whether requirement roles are purged on assignment
                    purgeRoles = bool(getGames(ctx.guild, activeGame[0])[6])

                    # Extract game, role and req row out of gameRoles. IndexError means not found.
                    try:
                        # comparison converts role[1] to string to fix sqlite issue with number chapters
                        role = [role for role in gameRoles if str(role[1]).lower() == chapter.lower()][0]
                    except IndexError:
                        await ctx.send("{} is not a valid chapter for this game".format(chapter))
                        return

                    # Get chapter object
                    roleObj = get(ctx.guild.roles, name=chapter)

                    if roleObj is not None:
                        # If the chapter has requirements
                        if len(role[2]) > 0:
                            # Get role reqs the user has
                            userRoles = [role.name for role in ctx.author.roles]
                            result = all(role in userRoles for role in role[2])

                            # If user has all the role reqs
                            if result == True:
                                await ctx.author.add_roles(roleObj)
                                await ctx.send("Role assigned!")

                                # if purge is set to on for this game
                                for roleObj in role[2]:
                                    roleObj = get(ctx.guild.roles, name=roleObj)
                                    await ctx.author.remove_roles(get(ctx.guild.roles, name=roleObj))
                                return

                            elif result == False:
                                # Retrieve all missing roles and inform user
                                missingRoles = [role for role in role[2] if role not in userRoles]
                                embed = discord.Embed(title="Missing Role Requirement", color=0xcb6326)
                                embed.add_field(name=chapter , value="\n".join(missingRoles), inline=False)
                                await ctx.send(embed=embed)
                                return

                        else:
                            await ctx.author.add_roles(roleObj)
                            await ctx.send("Role assigned!")

                            # if purge is set to on for this game
                            for roleObj in role[2]:
                                roleObj = get(ctx.guild.roles, name=roleObj)
                                await ctx.author.remove_roles(roleObj)
                            return
                    else:
                        # Catch for instances where a game role has been removed
                        await ctx.send('Error: role "{}" not found on server!'.format(chapter))
                        return

        else:
            await ctx.send("This command must be sent from one of your playthrough channels.")
            return

    @commands.command(pass_context=True)
    async def end(self, ctx):
        # Get game for context channel
        activeGame = [game[1] for game in getUserGames(ctx.guild, ctx.author.id) if game[2] == ctx.channel.id]

        # Get server games, roles, meta roles
        # Meta roles are a role that encompasses completion of several games
        gameList = getGames(ctx.guild)
        gameRoles = getRole(ctx.guild)
        metaRoles = [role for role in gameRoles if role[0] == "*"]

        # Decide whether the user is finishing an 'active playthrough'
        if activeGame:
            # Get activeGame's roles and game param
            gameRoles = getRole(ctx.guild, activeGame[0])
            activeGame = [row for row in gameList if activeGame[0] == row[0]]

            # Get Finished Category Object for activeGame
            complCatObj = get(ctx.guild.categories, name=activeGame[0][5])
            complRoleObj = get(ctx.guild.roles, name=activeGame[0][2])

            # Verify variables prior to utilizing
            await ctx.author.add_roles(complRoleObj)
            await ctx.channel.edit(category=complCatObj, sync_permissions=True)
            rmUserGame(ctx.guild, ctx.channel.id)

            await ctx.send("You have been granted the completion role.\n"
                   "The channel has been moved to the finished category.")

            # Purge all relevant roles from the user
            for role in gameRoles:
                try: # Attempt to remove any stray roles
                    roleObj = get(ctx.guild.roles, name=str(role[1]))
                    await ctx.author.remove_roles(roleObj)
                except AttributeError:
                    pass

            # Extract role names for comparison. Direct comparison makes list comprehension too complex
            roleList = [role.name for role in ctx.author.roles]

            # If user meets requirements for a Meta role, assign it
            for metaRole in metaRoles:
                if metaRole[1] not in roleList:
                    if all(role in roleList for role in metaRole[2]):
                        roleObj = get(ctx.guild.roles, name=metaRole[1])
                        await ctx.author.add_roles(roleObj)

        else:
            await ctx.send("This command must be sent from a playthrough room")
            return


    @commands.command(pass_context=True)
    async def finished(self, ctx, *game):
        game = " ".join(game).lower()

        # Get server games, roles, meta roles
        # Meta roles are a role that encompasses completion of several games
        gameList = getGames(ctx.guild)
        gameRoles = getRole(ctx.guild)
        metaRoles = [role for role in gameRoles if role[0] == "*"]

        if game == "":
            await ctx.send("Please specify a game!")
            return

        # Get info for game, get object for role
        # Validate database info in case either column is a number
        try:
            game = next(row for row in gameList if game == str(row[0]) or game == str(row[1]))
            complRoleObj = get(ctx.guild.roles, name=game[2])
            if complRoleObj == None: raise Exception
        except Exception:
            await ctx.send("Game does not exist!")
            return

        # Get roles for this game only
        gameRoles = getRole(ctx.guild, game[0])

        await ctx.author.add_roles(complRoleObj)
        await ctx.send("Game assigned!")

        # Extract role names for comparison. Direct comparison makes list comprehension too complex
        roleList = [role.name for role in ctx.author.roles]

        # If user meets requirements for a Meta role, assign it
        for metaRole in metaRoles:
            if metaRole[1] not in roleList:
                if all(role in roleList for role in metaRole[2]):
                    roleObj = get(ctx.guild.roles, name=metaRole[1])
                    await ctx.author.add_roles(roleObj)

def setup(client):
    client.add_cog(rolesUser(client))