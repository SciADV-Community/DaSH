import json, sys, logging
from discord.ext import commands

# Load bot config
with open("bot.json", "r") as f:
    bot = json.load(f)
# Load bot settings
with open("config.json", "r") as f:
    settings = json.load(f)

# Init bot
client = commands.Bot(command_prefix=bot["prefix"], description=bot["desc"], case_insensitive=True)
admins = settings["admin"]

# Enable logging
log = logging.getLogger()
con = logging.StreamHandler()

log.addHandler(con)
log.setLevel(logging.WARN)

## Clear help command
client.remove_command("help")

## Module list
modList = settings["modules"]
enabledMods = settings["startup"]
runningMods = []

## Command Functions
@client.command(pass_context=True)
async def load(ctx, mod: str = None):
    if ctx.author.id in admins:
        if mod is not None:
            status = await modLoad(client, mod, ctx)
            if status == 0:
                await ctx.send("{} loaded.".format(mod))
                log.info("{} loaded.".format(mod))
        else:
            await ctx.send("Load command requires module as argument")
    else:
        log.warning('Unauthorized user {} attempted to load module'.format(ctx.author.display_name))

@client.command(pass_context=True)
async def unload(ctx, mod: str = None):
    if ctx.author.id in admins:
        if mod is not None:
            status = await modUnload(client, mod, ctx)
            if status == 0:
                await ctx.send("{} unloaded.".format(mod))
                log.info("{} unloaded.".format(mod))
        else:
            await ctx.send("unload command requires module as argument")
    else:
        log.warning('Unauthorized user {} attempted to unload module'.format(ctx.author.display_name))

@client.command(pass_context=True)
async def reload(ctx, mod = None):
    if ctx.author.id in admins:
        if mod is not None:
            if mod in runningMods:
                await modUnload(client, mod, ctx)
                await modLoad(client, mod, ctx)
                await ctx.send(mod + " reloaded.")
                log.info("{} reloaded.".format(mod))
            else:
                await ctx.send(mod + " not currently loaded.")
        else:
            for mod in runningMods:
                await modUnload(client, mod, ctx)
                await modLoad(client, mod, ctx)
            await ctx.send("All modules reloaded.")
            log.info("Reloaded all modules.")
        print('------')
    else:
        log.warning('Unauthorized user {} attempted to reload module'.format(ctx.author.display_name))

@client.command(pass_context=True)
async def listmods(ctx, mod: str = None):
    if ctx.author.id in admins:
        await ctx.send("Loaded modules:")
        await ctx.send(runningMods)
    else: log.warning('Unauthorized user {} attempted to list modules'.format(ctx.author.display_name))

## Message Functions
@client.event
async def on_message(msg):
    if msg.author is not client:
        await client.process_commands(msg)

@client.event
async def on_command_error(ctx, error):
    # Sorry Davixxa, I totally stole this. Couldn't find a more efficient way
    if type(error).__name__ == "MissingRequiredArgument":
        await ctx.send("Command-tan experienced an error! Check your arguments or utilize `{}help {}`".
                       format(bot["prefix"], ctx.message.content.split()[0][1:]))

## Load Functions
@client.event
async def on_ready():
    print(client.user.name + "( " + str(client.user.id) + ")" + " has logged in.")
    print('------')

    for mod in enabledMods:
        await modLoad(client, mod, None)

    try:
        client.load_extension("modules.help")
    except(AttributeError, ImportError) as e:
        sys.exit("Fatal Error: Unable to load 'mod.help'")

    print('------')

## Module Functions
async def modLoad(client, mod, ctx = None):
    if mod not in runningMods and mod in modList:
        try:
            client.load_extension(mod)
        except(AttributeError, ImportError) as e:
            errorStr = "{} load failed. \n {}: {}".format(mod, type(e).__name__, e)
            log.error(errorStr)
            if ctx:
                await ctx.send(errorStr)
            return 1
        runningMods.append(mod)
        return 0
    else:
        await ctx.send("{} is not a valid module.".format(mod))
        print("Attempted to load module {}".format(mod))

async def modUnload(client, mod, ctx = None):
    if mod in runningMods:
        try:
            client.unload_extension(mod)
        except(AttributeError, ImportError) as e:
            errorStr = "{} unload failed. \n {}: {}".format(mod, type(e).__name__,e)
            log.error(errorStr)
            if ctx:
                await ctx.send(errorStr)
            return 1
        runningMods.remove(mod)
        return 0

## Run Function
client.run(bot["id"])