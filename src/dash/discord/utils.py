import asyncio
from functools import update_wrapper
import logging
from dash import config


def generate_logger():
    """Utility function to create the Logger"""
    logger = logging.getLogger("DaSH")
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(filename="dash-log.log", encoding="utf-8", mode="a")
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )

    logger.addHandler(handler)

    return logger


_logger = generate_logger()


def get_logger():
    """Utility function to give access to the Logger"""
    return _logger


async def send_message(context, message):
    """Utility function to send a message if the the provided context is not None."""
    if context:
        await context.send(message)


async def load_module(client, module, context=None):
    """Utility function to load a certain module. Returns whether or not the loading succeeded."""
    logger = get_logger()

    if context and context.author.id not in config.ADMINS:
        logger.warning(
            "Unauthorized user %s attempted to load module %s",
            context.author.name,
            module,
        )
        await send_message(context, f"You are not authorized to load modules.")
        return False

    if module not in config.MODULES:
        logger.info("Attempted to load invalid module %s", module)
        await send_message(context, f"{module} is not a valid module.")
        return False

    try:
        module = f"dash.discord.modules.{module}"
        client.load_extension(module)
        logger.info("Module %s was successfully loaded.", module)
        await send_message(context, f"{module} was successfully loaded.")
        return True
    except (AttributeError, ImportError) as e:
        logger.error("Failed to load module %s: %s", module, e)
        await send_message(
            context,
            f"{module} could not be loaded due to an error. Please check the logs.",
        )
        return False


async def unload_module(client, module, context=None):
    """Utility function to unload a certain module. Returns whether or not the unloading succeeded."""
    logger = get_logger()

    if context and context.author.id not in config.ADMINS:
        logger.warning(
            "Unauthorized user %s attempted to unload module %s",
            context.author.name,
            module,
        )
        await send_message(context, f"You are not authorized to unload modules.")
        return False

    try:
        module = f"dash.discord.modules.{module}"
        client.unload_extension(module)
        logger.info("Module %s was successfully unloaded.", module)
        await send_message(context, f"{module} was successfully unloaded.")
        return True
    except (AttributeError, ImportError) as e:
        logger.error("Failed to unload module %s: %s", module, e)
        await send_message(
            context,
            f"{module} could not be unloaded due to an error. Please check the logs.",
        )
        return False
