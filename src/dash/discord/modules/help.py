from discord.ext import commands
from modules.rolesSQL import *
import discord

cmdList = {
    "start": ['<*game>', 'Creates a new game room. Only one can exist per person at a time.', 0],
    "chapter": ['<number>', 'Gives completion role for chapter.', 0],
    "finished": ['', "Closes room, gives completion role for game.", 0],
    "addgame": ['<game> <suffix> <complRole> <playCat> <complCat> <purgeRole>', 'Add game to games list.', 1],
    "listgames": ['', 'Shows list of playable games.', 0],
    "rmgame": ['<game>', 'Removes game and game roles from the server game options.', 1],
    "addrole": ['<game> <role> <*reqs>', 'Add role for a game. Takes multiple reqs. '
                                         'Using * lets you add a series role.', 1],
    "listroles": ['<?game>', 'Lists roles of a game. If no game is specified, shows server roles.', 0],
    "rmrole": ['<game> <role>', 'Removes a role from a game. Using * lets you remove a series role.', 1],
    "auth": ['<role>', 'Adds roles to be authorized for administrative bot commands. Can have multiple.', 2],
    "getauth": ['', 'Lists authorized roles for administrative bot commands.', 2],
    "deauth": ['', 'Removes ALL roles authorized for commands.', 2]
}

class help():
    def __init__(self, client):
        self.client = client
        global modName
        modName = self.__class__.__name__

    @commands.command(pass_context=True)
    async def help(self, ctx):
        authLevel = await isAuthorized(ctx)

        embed = discord.Embed(title="DaSH 1st Edition Ver. 1.19", description="DaSH Command Help", color=0xcb6326)
        embed.set_thumbnail(url="https://i.imgur.com/8ye4OJZ.png")

        for key, value in cmdList.items():
            if authLevel >= value[2]:
                embed.add_field(name=key + ' ' + value[0], value=value[1])

        embed.set_footer(text="Use 'help' with a command for usage info.")
        await ctx.send(embed=embed, delete_after=20)


def setup(client):
    client.add_cog(help(client))