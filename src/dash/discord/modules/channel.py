import discord
from discord.utils import get
from discord.ext.commands import Cog, command
from dash.discord import utils
from dash.models import Guild, Game, Channel, Category, CompletionRole

logger = utils.get_logger()


class ChannelManagement(Cog):
    def __init__(self, client):
        self.client = client
        logger.info(f"Module {self.__class__.__name__} loaded successfully.")

    @command(pass_context=True)
    async def start(self, context, *, game: str):
        """Command to start a playthrough channel in a particular game.

        Arguments:
            game -- The game to start a playthrough channel for.
        """
        guild = context.guild
        guild_obj = Guild.get(id=context.guild.id)
        user = context.author
        game_obj = Game.get_by_alias(game)

        if not game_obj:  # Game not found
            # TODO Implement start list or maybe have another command
            await context.send(
                "Game does not exist, try again or use `$start list` for game list!"
            )
            return

        if Channel.get(user_id=user.id, game=game_obj, guild=guild_obj):
            await context.send(f"You already have a {game_obj.name} room!")
            return

        # Get first available category for the game
        category_obj = Category.get(
            game=game_obj, guild=guild_obj, full=False, archival=False
        )
        if not category_obj:
            await context.send(
                f"Sorry, all our categories are full right now. Please contact an admin."
            )
            return

        category = get(context.guild.categories, name=category_obj.name)
        channel_name = f"{context.author.display_name}-{game_obj.channel_suffix}"
        channel = await context.guild.create_text_channel(
            name=channel_name, category=category
        )
        Channel.create(
            id=channel.id,
            user_id=user.id,
            game=game_obj,
            guild=guild_obj,
            category=category_obj,
            name=channel.name,
        )

        # Handle persmissions
        permissions_owner = discord.PermissionOverwrite(
            read_messages=True,
            read_message_history=True,
            send_messages=True,
            manage_messages=True,
        )
        await channel.set_permissions(context.author, overwrite=permissions_owner)

        instructions = (
            f"This room has been created for your playthrough of {game_obj.name}.\n"
            "When you have finished the game, type `$finished` and the room will be moved.\n\n"
            "Please note that commands will only function in your playthrough room, "
            "and that you can only have one playthrough room at any given time."
        )

        instructions_msg = await channel.send(instructions)
        await instructions_msg.pin()

        await context.send(f"Game room created: {channel.mention}", delete_after=30)

    @command(pass_context=True)
    async def end(self, context):
        """Command to archive a channel that has been finished."""
        user = context.author
        channel_id = context.channel.id
        guild_id = context.guild.id
        channel = Channel.get(user_id=user.id, id=channel_id, guild_id=guild_id)

        if not channel:
            await context.send(
                "This command must be sent from a proper playthrough room that you own."
            )
            return

        # TODO Check if already archived or not
        archival_category_obj = Category.get(
            guild_id=guild_id, game=channel.game, archival=True, full=False
        )
        if not archival_category_obj:
            await context.send(
                "No archival category is available for this game. Please contact an admin."
            )
            return

        archival_category = get(context.guild.categories, id=archival_category_obj.id)
        await context.channel.edit(category=archival_category, sync_permissions=True)

        completion_role_obj = CompletionRole.get(game=channel.game, guild_id=guild_id)
        if completion_role_obj:
            completion_role = get(context.guild.roles, id=completion_role_obj.id)
            await context.author.add_roles(completion_role)
            await context.send("You have been grantend the completion role.")

        await context.send("The channel has been moved to the archival category.")
        # TODO Meta role handling

    @command(pass_context=True)
    async def finished(self, context, *, game: str):
        if not game:
            await context.send("Please specify a game!")
            return

        game_obj = Game.get_by_alias(game)
        if not game_obj:
            await context.send("Game does not exist!")
            return

        completion_role_obj = CompletionRole.get(
            game=game_obj, guild_id=context.guild.id
        )
        if not completion_role_obj:
            await context.send(
                f"Role for game {game_obj.name} not configured. Please contact an admin."
            )
            return

        role = get(context.guild.roles, id=completion_role_obj.id)
        await context.author.add_roles(role)
        await context.send(f"Role successfully added!")
        # TODO Meta role handling


def setup(client):
    client.add_cog(ChannelManagement(client))
