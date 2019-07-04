import sqlite3, os, json, logging
from discord.utils import get

dbPath = "./config/roles/" + "{}" + ".sqlite"

# Logger
log = logging.getLogger()
con = logging.StreamHandler()

log.addHandler(con)
log.setLevel(logging.WARN)

## DB Functions ##

# Add game to database
def addGame(guild, gameName, gameAlias, complRole, chnlSuffix, playCat, complCat, purgeRole):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute("SELECT gameName FROM games WHERE gameName=?", (gameName,))

    result = [i for i in c.fetchall()]
    print("")

    if len(result) is 0:
        c.execute('''INSERT INTO 'games' VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (gameName, gameAlias, complRole, chnlSuffix, playCat, complCat, purgeRole))
        conn.commit()

        c.close()
        return 0
    else:
        c.close()
        return 1

# Return single game
# TODO: MERGE getGame and listGames like getRoles
def getGame(guild, gameName):
    verifyPath(guild)
    conn, c = openDB(guild.id)
    c.execute('''SELECT * FROM games WHERE gameNAME=?''', (gameName, ))

    try:
        rtn = c.fetchall()[0]
    except (IndexError):
        rtn = None

    c.close()
    return rtn

def listGames(guild, pos: int = None):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute("SELECT * from games")

    # If no pos, return all. If pos, return pos
    if pos == None:
        gameList = c.fetchall()

        c.close()
        gameList.sort()
        return gameList
    else:
        gameList = []
        [gameList.append(i[pos]) for i in c.fetchall()]

        c.close()
        gameList.sort()
        return gameList

def rmGame(guild, gameName):
    gameName = gameName

    verifyPath(guild)
    conn, c = openDB(guild.id)

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


def addRole(guild, gameName, role, reqs):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    # reqs is a list, so we dump it to JSON for later retrieval
    c.execute('''INSERT INTO 'roles' VALUES (?, ?, ?)''', (str(gameName), role, json.dumps(reqs)))

    rows = c.rowcount
    conn.commit()

    c.close()
    return rows

def getRoles(guild, gameName):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    try:
        c.execute('''SELECT * FROM roles where gameName=(?)''', (gameName,))
        roleTup = list(c.fetchall())
    except IndexError:
        return []

    c.close()

    # Convert reqs back to a list using JSON, If empty remove brackets.
    roleList = []
    for row in roleTup:
        row = list(row)
        if row[2] != "[]":
            row[2] = json.loads(row[2])
        else:
            row[2] = ""
        roleList.append(row)

    return roleList

def getSRoles(guild, role=None):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    try:
        if role == None: # If role isn't specified we want all the guild roles
            c.execute('''SELECT * FROM "seriesRoles"''')
            roles = c.fetchall()
        else:            # If we specify one, give us that role
            c.execute('''SELECT * FROM "seriesRoles" WHERE role="{}"'''.format(role,))
            roles = c.fetchall()[0]

        # See comments for similar section above. TL;DR: All indexes converted to str, drop null
        roleList = []
        for row in roles:
            row = [str(i) for i in row if str(i) != 'NULL']
            roleList.append(row)

    except (sqlite3.OperationalError, IndexError):
        # If we get this, our return is empty. Either the game has no roles or doesn't exist
        roleList = []

    c.close()
    return roleList

def rmRole(guild, gameName, role):
    verifyPath(guild)
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
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''INSERT INTO players VALUES (?, ?, ?)''', (userID, game, gameRoom,))
    status = c.rowcount
    conn.commit()

    c.close()
    return status

def getUsers(guild):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''SELECT * FROM players''')
    users = c.fetchall()

    c.close()
    return users

def getUserGame(guild, userID):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''SELECT * FROM players WHERE userID=?''', (userID,))
    try:
        status = c.fetchall()[0]
    except IndexError:
        status = []

    c.close()
    return status

def rmUserGame(guild, userID):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''DELETE FROM players WHERE userID=?''', (userID,))

    conn.commit()
    c.close()

## Permission Management

def setAuthorized(guild, user, role):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''INSERT INTO auth VALUES (?, ?)''', (user.name, role))

    conn.commit()
    c.close()

def getAuthorized(guild, user=None):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    try:
        if user == None:
            user= [[], []]
            c.execute('''SELECT userID FROM auth where role!=?''', ('group',))
            for i in c.fetchall(): user[0].append(i[0])
            c.execute('''SELECT userID FROM auth where role=?''', ('group',))
            for i in c.fetchall(): user[1].append(i[0])
        else:
            c.execute('''SELECT * FROM auth where userID=?''', (user.name,))
            user = c.fetchall()[0]

        c.close()
        return user
    except IndexError as e:
        print(e)
        c.close()
        return None
    
def rmAuthorized(guild, role):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    c.execute('''DELETE FROM auth WHERE userID=?''', (role,))

    conn.commit()
    c.close()

async def isAuthorized(ctx, fct = None):
    user = ctx.author
    authed = getAuthorized(ctx.guild)
    authedUser = authed[0]
    authedGroup = []
    for i in authed[1]:
        roleObj = get(ctx.guild.roles, name=i)
        authedGroup.append(roleObj)

    if user.id in authedUser:
        return 2

    for i in authedGroup:
        if user.id in [x.id for x in i.members]:
            return 1

    if fct != None:
        print("Unauthorized User '{}' in '{}' attempted '{}'".format(user.name, ctx.guild.name, fct))
    return 0

## DB initialization ##

def initGuildDB(guild):
    # Table for authorized users and their roles
    AuthCol = ["userID integer", "role string"]
    # Table for storing games and their settings
    gamesCol = ["gameName string", "gameAlias string", "complRole string", "chnlSuffix string", "playCat string", "complCat string",
                "purgeRole integer"]
    # Table for storing user game states
    roomsCol = ["userID integer", "gameName string", "gameRoom integer"]
    # Table for role, both for games and for series
    rolesCol = ["gameName string", "role string", "reqs string"]
    ## TODO: DEPRICATE
    # Table for storing seriesRoles, roles granted for finishing 'all games' of a type
    ## seriesRolesCol = ["role string", "req1 string", "req2 string", "req3 string", "req4 string", "req5 string"]

    # Davixxa, Zips, and the server owner (by default)
    baseChuuni = []
    for i in getAdmin():
        baseChuuni.append([i, "admin"])
    # If guild owner not an admin
    if str(guild.owner.id) != baseChuuni[0][0] and str(guild.owner.id) != baseChuuni[1][0]:
        baseChuuni.append([str(guild.owner.id), 'owner'])

    conn, c = openDB(guild.id)
    # Initialize databases if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS auth ({});'''.format(", ".join(AuthCol)))
    c.execute('''CREATE TABLE IF NOT EXISTS games ({});'''.format(", ".join(gamesCol)))
    c.execute('''CREATE TABLE IF NOT EXISTS rooms ({});'''.format(", ".join(roomsCol)))
    c.execute('''CREATE TABLE IF NOT EXISTS roles ({});'''.format((", ".join((rolesCol)))))

    ## TODO: DEPRICATE
    ##c.execute('''CREATE TABLE IF NOT EXISTS seriesRoles ({});'''.format((", ".join(seriesRolesCol))))

    # Add in admins
    for i in baseChuuni: c.execute('''INSERT INTO 'auth' VALUES (?, ?)''', (i[0], i[1]))
    conn.commit()

    c.close()


def runSQL(guild, cmd):
    verifyPath(guild)
    conn, c = openDB(guild.id)

    try:
        c.execute(cmd)
    except Exception as e:
        return e

    result = c.fetchall()

    conn.commit()
    c.close()

    return result

def verifyPath(guild):
    path = dbPath.format(str(guild.id))
    if not os.path.exists(path):
        initGuildDB(guild)
        return 1
    else:
        return 0

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
