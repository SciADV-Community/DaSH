import sqlite3, os, json, logging
from datetime import datetime
from discord.utils import get

path = "./guilds/"
dbPath = path + "{}" + ".sqlite"

# Logger
log = logging.getLogger()
con = logging.StreamHandler()

log.addHandler(con)
log.setLevel(logging.WARN)

## DB Functions ##

# REWRITE COMPLETE
# Add game to database
def addGame(guild, gameName, gameAlias, complRole, chnlSuffix, playCat, complCat, purgeRole):
    conn, c = openDB(guild.id)

    c.execute("SELECT gameName FROM games WHERE gameName=?", (gameName,))
    result = c.fetchone()

    if result is None:
        c.execute('''INSERT INTO 'games' VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (gameName, gameAlias, complRole, chnlSuffix, playCat, complCat, purgeRole))
        conn.commit()
        c.close()

        return 0
    else:
        c.close()

        return 1

# REWRITE COMPLETE
def getGames(guild, gameName: str = None):
    conn, c = openDB(guild.id)

    if gameName is None:
        c.execute('''SELECT * from games''')
        gameList = c.fetchall()

    else:
        c.execute('''SELECT * from games where gameName=?''', (gameName,))
        gameList = c.fetchone()

    c.close()
    return gameList

# REWRITE COMPLETE
def rmGame(guild, gameName):
    conn, c = openDB(guild.id)
    gameName = gameName

    try:
        c.execute('''DELETE FROM games WHERE gameNAME=?''', (gameName, ))
        gamesRows = c.rowcount
    except(sqlite3.OperationalError):
        gamesRows = 0

    try:
        c.execute('''DELETE from roles where gameNAME=?''', (gameName, ))
    except(sqlite3.OperationalError):
        pass

    conn.commit()
    c.close()

    return gamesRows

# REWRITE COMPLETE
def addRole(guild, gameName, role, reqs):
    conn, c = openDB(guild.id)

    # reqs is a list, so we dump it to JSON for later retrieval.
    # this is more effective than attempting to grow and shrink rows.
    c.execute('''INSERT INTO 'roles' VALUES (?, ?, ?)''', (str(gameName), role, json.dumps(reqs)))

    rows = c.rowcount
    conn.commit()

    c.close()
    return rows


def getRole(guild, gameName: str = None):
    conn, c = openDB(guild.id)

    try:
        if gameName == None:
            c.execute('''SELECT * FROM roles''')
        else:
            c.execute('''SELECT * FROM roles where gameName=(?)''', (gameName,))

        roleTup = list(c.fetchall())

    except IndexError:
        print("INDEX ERROR")
        return []

    # Convert the Final column (reqs) back from JSON
    roleList = []
    for row in roleTup:
        row = list(row)
        if row[2] != "[]":
            row[2] = json.loads(row[2])
        else:
            row[2] = ""
        roleList.append(row)

    return roleList

def rmRole(guild, gameName, role):
    conn, c = openDB(guild.id)

    # asterisk indicates delete-all
    if role != "*":
        c.execute('''DELETE FROM roles WHERE gameName="{}" AND role="{}"'''.format(gameName, role))
    else:
        c.execute('''DELETE FROM roles WHERE gameName="{}"'''.format(gameName))

    rows = c.rowcount
    conn.commit()

    c.close()
    return rows

def setUserGame(guild, userID, game, gameRoom):
    conn, c = openDB(guild.id)

    c.execute('''INSERT INTO rooms VALUES (?, ?, ?)''', (userID, game, gameRoom,))
    status = c.rowcount
    conn.commit()

    c.close()
    return status

def getUserGames(guild, userID):
    conn, c = openDB(guild.id)

    c.execute('''SELECT * FROM rooms WHERE userID=?''', (userID,))
    try:
        status = c.fetchall()
    except IndexError:
        status = []

    c.close()
    return status

def rmUserGame(guild, channelID):
    conn, c = openDB(guild.id)

    c.execute('''DELETE FROM rooms WHERE gameRoom=?''', (channelID,))

    conn.commit()
    c.close()

## Permission Management

def setAuthorized(guild, obj, role):
    conn, c = openDB(guild.id)

    c.execute('''INSERT INTO auth VALUES (?, ?)''', (obj.id, role))

    conn.commit()
    c.close()

def getAuthorized(guild, user=None):
    conn, c = openDB(guild.id)

    # Craft an array so we can pass everything back. We'll use what's needed
    authed= [[], [], []]
    group = c.execute('''SELECT userID FROM auth where role=0''').fetchone()
    owner = c.execute('''SELECT userID FROM auth where role=1''').fetchall()
    admin = c.execute('''SELECT userID FROM auth where role=2''').fetchall()

    # Any of these could be an index error. If it's an error, pass it.
    try:
        if len(group) > 0: authed[0].append(group[0])
    except: pass
    try:
        if len(owner) > 0: authed[1].extend([i[0] for i in owner])
    except: pass
    try:
        if len(admin) > 0: authed[2].extend([i[0] for i in admin])
    except: pass

    return authed

## REWRITE COMPLETE TODO: VERIFY
def rmAuthorized(guild, role):
    conn, c = openDB(guild.id)

    c.execute('''DELETE FROM auth WHERE userID=?''', (role,))

    conn.commit()
    c.close()

async def isAuthorized(ctx, func = None, min = 0):
    conn, c = openDB(ctx.guild.id)

    ##########################
    ## Authorization Levels ##
    ## 0 = Authorized       ##
    ## 1 = Server Owner     ##
    ## 2 = Admin            ##
    ##########################

    # Pull database to memory
    perms = c.execute('''SELECT * from auth''').fetchall()
    user, group = None, None

    if len(perms) > 0:
        # Check if user is in database, return if authorized
        for row in perms:
            if row[0] == ctx.author.id:
                if row[1] > min: return 1

        # If we get here and min is 0, check the auth group
        if min == 0:
            for row in perms:
                if row[1] == 0:
                    # See if user in auth group
                    for role in ctx.author.roles:
                        if role.id == row[0]:
                            return 1

        # User is not authorized
        print("Unauthorized User '{}' in '{}' attempted to call '{}' at {}".format(ctx.author.display_name, ctx.guild.name, func, datetime.utcnow()))
        return 0

## DB initialization ##

def verifyGuild(guild):
    path = dbPath.format(str(guild.id))
    if os.path.exists(path):
        return 0
    else:
        return 1

def initGuild(guild):
    # Table for authorized users and their roles
    authTable = ["userID integer", "role string"]
    # Table for storing games and their settings
    gameTable = ["gameName string", "gameAlias string", "complRole string", "chnlSuffix string", "playCat string", "complCat string",
                "purgeRole integer"]
    # Table for storing user game states
    roomTable = ["userID integer", "gameName string", "gameRoom integer"]
    # Table for role, both for games and for series
    roleTable = ["gameName string", "role string", "reqs string"]

    if not os.path.exists(path): os.makedirs(path)

    conn, c = openDB(guild.id)
    # Initialize databases if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS auth ({});'''.format(", ".join(authTable)))
    c.execute('''CREATE TABLE IF NOT EXISTS games ({});'''.format(", ".join(gameTable)))
    c.execute('''CREATE TABLE IF NOT EXISTS rooms ({});'''.format(", ".join(roomTable)))
    c.execute('''CREATE TABLE IF NOT EXISTS roles ({});'''.format((", ".join((roleTable)))))

    # Add admins from config
    with open("config.json", "r") as f:
            config = json.load(f)

    for i in config["admin"]: c.execute('''INSERT INTO 'auth' VALUES (?, ?)''', (i, 2))
    if guild.owner.id not in config["admin"]:
        c.execute('''INSERT INTO 'auth' VALUES (?, ?)''', (guild.owner.id, 1))

    conn.commit()
    c.close()


def runSQL(guild, cmd):
    conn, c = openDB(guild.id)

    try:
        c.execute(cmd)
    except Exception as e:
        return e

    result = c.fetchall()

    conn.commit()
    c.close()

    return result

## Shorteners ##

def openDB(guildID):
    path = dbPath.format(str(guildID))
    conn = sqlite3.connect(path)
    c = conn.cursor()
    return conn, c

def getAdmin():
    with open("config.json", "r") as f:
        config = json.load(f)
        return config["admin"]
