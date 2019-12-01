# pylint: disable=unexpected-keyword-arg
import shlex
import click
import discord
from discord.utils import get
from discord.ext.commands import Cog, command
from dash import config
from dash.discord import utils
from dash.models import Game, GameAlias, Guild, Role, CompletionRole, Category, Channel

logger = utils.get_logger()


@click.group()
@click.pass_context
def admin(context):
    """Command line tool for administration of the server."""
    pass


@admin.group()
@click.pass_context
def game(context):
    """Manage game operations"""
    pass


@game.command()
@click.argument("game", type=str)
@click.option("--alias", "-a", type=str, help="alias for the game")
@click.option(
    "--completion_role", "-c", type=int, help="role id of the completion role"
)
@click.option("--channel_suffix", "-s", type=str, help="suffix of playthrough channels")
@click.option(
    "--active_category", "-a", type=int, help="category id to put active channels in"
)
@click.option(
    "--finished_category",
    "-f",
    type=int,
    help="category id to put finished channels in",
)
@click.pass_context
async def add(
    context,
    game,
    alias=None,
    completion_role=None,
    channel_suffix=None,
    active_category=None,
    finished_category=None,
):
    """Command to add a game"""
    discord_context = context.obj["discord_context"]
    guild_obj = Guild.get(id=discord_context.guild.id)

    async with discord_context.typing():
        if Game.get(name=game):
            await discord_context.send(f"{game} already exists.")
            return

        if not channel_suffix:
            channel_suffix = f"plays-{game.lower().strip()}"

        game_obj = Game.create(name=game, channel_suffix=channel_suffix)
        if alias:
            GameAlias.create(name=alias, game=game_obj)

        if completion_role:
            role = get(discord_context.guild.roles, id=role)
        else:
            role = await discord_context.guild.create_role(name=game)
        CompletionRole.create(
            id=role.id, guild=guild_obj, name=role.name, game=game_obj
        )

        if active_category:
            category = get(discord_context.guild.categories, id=active_category)
        else:
            category = await discord_context.guild.create_category(
                name=f"{game} Playthroughs"
            )
        Category.create(
            id=category.id, guild=guild_obj, name=category.name, game_id=game_obj.id,
        )

        if finished_category:
            category = get(discord_context.guild.categories, id=finished_category)
        else:
            category = await discord_context.guild.create_category(
                name=f"{game} Archived"
            )
        Category.create(
            id=category.id,
            guild=guild_obj,
            name=category.name,
            game_id=game_obj.id,
            archival=True,
        )

        await discord_context.send(f"Successfully added {game}!")


@game.command()
@click.argument("game", type=str)
@click.pass_context
async def remove(context, game):
    """Command to remove a game"""
    discord_context = context.obj["discord_context"]
    guild_id = discord_context.guild.id
    game_obj = Game.get_by_alias(game)
    if not game_obj:
        await discord_context.send(f"Game {game} not found. Try again!")
        return

    game_obj.delete()
    await discord_context.send(f"Game {game} successfully removed!")


@admin.group()
@click.pass_context
def channel(context):
    """Manage channels"""
    pass


@channel.command()
@click.argument("channel_id", type=int)
@click.pass_context
async def delete(context, channel_id):
    """Command to delete a specific channel"""
    discord_context = context.obj["discord_context"]
    guild_id = discord_context.guild.id
    channel = Channel.get(guild_id=guild_id, id=channel_id)
    if channel:
        channel.delete()

    channel = get(discord_context.guild.channels, id=channel_id)
    if channel:
        await channel.delete(reason=f"Admin command by: {discord_context.author.name}")

    await discord_context.send("Successfully deleted channel.")


class Admin(Cog):
    def __init__(self, client):
        self.client = client
        logger.info(f"Module {self.__class__.__name__} loaded successfully.")

    @command(pass_context=True)
    async def admin(self, context, *, args):
        if context.author.id not in config.ADMINS:
            logger.info("Unauthorized user %s attempted to invoke admin command.", context.author.name)
            await context.send("You are not authorizeid to use the admin command.")
            return

        args = shlex.split(args)
        try:
            call = admin(args, standalone_mode=False, obj={"discord_context": context})
            status = await call if type(call) != int else call
            if status == 0:  # Click returns 0 if --help was called directly
                # Hack to get help at the right level
                target = admin
                info_name = f"{config.PREFIX}admin"
                for arg in args:
                    if arg != "--help" and not arg.startswith("-"):
                        target = globals()[arg]
                        info_name += f" {arg}"
                    else:
                        break

                # Get help string
                with click.Context(target, info_name=info_name) as ctx:
                    await context.send(target.get_help(ctx))
        except click.exceptions.UsageError as e:
            print(e)
            await context.send(
                "Incorrect command use. Use the `--help` flag to get more info."
            )
        except Exception as e:
            logger.warning(f"Exception occurred in admin command: {e}")
            await context.send(f"An error occurred when using the command: ```{e}```")


def setup(client):
    client.add_cog(Admin(client))

