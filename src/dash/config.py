import os
from dash.consts import Engines

DATABASE_CONFIG = {"engine": Engines.SQLite, "options": {"filename": "playthrough.db"}}

PREFIX = os.getenv("BOT_PREFIX", "$")
DESCRIPTION = os.getenv("BOT_DESCRIPTION", "")
TOKEN = os.getenv("BOT_TOKEN")

ADMINS = [int(admin) for admin in os.getenv("BOT_ADMINS", "").split(";")]
MODULES = os.getenv("BOT_MODULES", "").split(";")
STARTUP = os.getenv("BOT_STARTUP_MODULES", "").split(";")
