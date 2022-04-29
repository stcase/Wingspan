![Workflow Status](https://github.com/stcase/Wingspan/actions/workflows/run-tests.yml/badge.svg)

# Wingspan Bot

A discord bot that posts whose turn it is for your Wingspan games.
Because it's easy to miss the Steam notifications, and annoying to launch the game only to see that it's not your turn.

## Setup
1. Get a local enlistment of this project
2. Install [Poetry](https://python-poetry.org/)
3. Setup SteamworksPy (see below)
4. Get the bot's token [from here](https://discord.com/developers/applications/), if you're the owner
5. Copy `configs_exmaple.py` to `configs.py` and update the contents
6. Install git hooks with `poetry run pre-commit install`
7. Setup the database with the command `poetry run alembic upgrade head`

### Setting up SteamworksPy on Windows-64
1. Download the [Steamworks SDK](https://partner.steamgames.com/)
2. Copy the following files from the steamworks sdk to the enlistment root
   1. `sdk\redistributable_bin\win64\steam_api64.dll`
   2. `sdk\redistributable_bin\win64\steam_api64.lib`
3. Copy the latest `SteamworksPy.dll` to the enlistment root from the
   [pre-built versions](https://github.com/philippj/SteamworksPy/releases)
4. Copy the `steamworks` folder for the corresponding version to the enlistment root from the SteamworksPy source code

## Testing

Run `poetry run pytest --cov discord --cov wingspan_api` from the root of the enlistment.

## Running

1. Ensure the Steam client is running
2. Run `poetry run python main.py -h` for next steps

## TODO

- Move user tagging to the data controller
- Fix tagged users text (add parenthesis and spacing)
- Caching in get_matches
- Better handling of config file when type checking
- Get match test data for WAITING, READY, and REMINDER
- Filter highest score stats on channel

## References
Steam
- https://partner.steamgames.com/doc/features/auth#client_to_client
- https://partner.steamgames.com/doc/sdk/api#thirdparty
- https://steamdb.info/app/1054490/
- https://github.com/philippj/SteamworksPy/

Discord
- https://github.com/nextcord/nextcord
- https://nextcord.readthedocs.io/en/latest/index.html
- https://discord.com/developers/docs/intro
- https://discordpy.readthedocs.io/en/stable/discord.html

SQLAlchemy
- https://docs.sqlalchemy.org/en/14/orm/queryguide.html
