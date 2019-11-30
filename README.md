# DaSH

A role bot for visual novels, originally designed for the Steins;Gate playthrough server.

## Setup

-   Clone repo
-   Create and set up the environment with `pipenv install`.
-   Enter the environment with `pipenv shell`.
-   Initialize the config with `dash init`.

## Database Management

After making changes to the models, make sure to migrate the database with:
```
dash makemigration
dash migrate
```

When asked for a message to add to the migration, add a short semantically rich message that describes what the migration is about.

## Testing

To run the tests locally, run `dash test`.

---

Additional GNU GPL3 Terms apply to all code within this project(7b & 7c):

-   Requiring preservation of specified reasonable legal notices or
    author attributions in that material or in the Appropriate Legal
    Notices displayed by works containing it

-   Prohibiting misrepresentation of the origin of that material, or
    requiring that modified versions of such material be marked in
    reasonable ways as different from the original version
