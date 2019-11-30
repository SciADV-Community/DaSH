import json, sys, logging
from discord.ext import commands
from dash import config
from dash.discord import utils


# Init bot
client = commands.Bot(
    command_prefix=config.PREFIX, description=config.DESCRIPTION, case_insensitive=True
)
admins = config.ADMINS

# Enable logging
log = utils.get_logger()

## Clear help command
client.remove_command("help")

## Module list
modList = config.MODULES
enabledMods = config.STARTUP
runningMods = []

## Command Functions
@client.command(pass_context=True)
async def load(ctx, mod: str = None):
    if not mod:
        await ctx.send("Load requires the name of the module to load.")
    elif mod not in runningMods:
        if await utils.load_module(client, mod, ctx):
            runningMods.append(mod)
    else:
        await ctx.send(f"Module {mod} already loaded.")


@client.command(pass_context=True)
async def unload(ctx, mod: str = None):
    if not mod:
        await ctx.send("Unload requires the name of the module to unload.")
    elif mod in runningMods:
        if await utils.unload_module(client, mod, ctx):
            runningMods.remove(mod)
    else:
        await ctx.send(f"Module {mod} not loaded.")


@client.command(pass_context=True)
async def reload(ctx, mod=None):
    if mod:
        if mod in runningMods:
            if await utils.unload_module(client, mod, ctx) and await utils.load_module(
                client, mod, ctx
            ):
                await ctx.send(f"{mod} reload complete.")
        else:
            await ctx.send(f"Module {mod} not reloaded.")
    else:
        for mod in runningMods:
            unloaded = await utils.unload_module(client, mod, ctx)
            if unloaded:
                await utils.load_module(client, mod, ctx)
        else:
            log.warning(
                "Unauthorized user %s attempted to reload all modules.",
                ctx.author.username,
            )


@client.command(pass_context=True)
async def listmods(ctx, mod: str = None):
    if ctx.author.id in admins:
        await ctx.send(f"Loaded modules:\n {runningMods}")
    else:
        log.warning(
            "Unauthorized user %s attempted to list modules", ctx.author.username
        )


## Message Functions
@client.event
async def on_message(msg):
    if msg.author is not client:
        await client.process_commands(msg)


@client.event
async def on_command_error(ctx, error):
    if not isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(
            f"Command-tan experienced an error! Check your arguments or utilize `{config.PREFIX}help {config.PREFIX, ctx.message.content.split()[0][1:]}`"
        )


## Load Functions
@client.event
async def on_ready():
    print(f"{client.user.name} ({client.user.id}) has logged in.")
    print("------")

    for mod in enabledMods:
        await utils.load_module(client, mod)

    try:
        client.load_extension("modules.help")
    except (AttributeError, ImportError) as e:
        log.error("Error loading the help module: %s", e)
        sys.exit("Fatal Error: Unable to load 'mod.help'")

    print("------")


## Run Function
client.run(config.TOKEN)
