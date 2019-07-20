# DaSH

A role bot for visual novels, originally designed for the Steins;Gate playthrough server.

Setup:

- Clone repo
- Create config files

There are two config files, `bot.json` and `config.json`. These files MUST be filled out prior to running the bot.

`bot.json`
- Prefix is used for commands
- Description is the bot description
- id is the ID for the bot account

```
{"prefix": "",
"desc": "",
"id": ""}
```

`config.json`
- admin is the user ID for those who will have administrative access to the bot via command
- modules are valid modules that can be loaded or unloaded
- startup are modules, from modules, that are to be loaded on startup

```
{"admin": [],
"modules": ["mod.rolesAdmin", "mod.rolesUser"],
"startup": ["mod.rolesAdmin", "mod.rolesUser"]}
```

Python requirements to be published at a later point.

- - - -

Additional GNU GPL3 Terms apply to all code within this project(7b & 7c):
-  Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it

- Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version
