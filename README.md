# Wingspan Bot

## Setup
1. Get a local enlistment of this project
2. Setup SteamworksPy (see below)
2. Get the bot's token [from here](https://discord.com/developers/applications/), if you're the owner
3. Copy `configs_exmaple.py` to `configs.py` and update the contents

### Setting up SteamworksPy on Windows-64
1. Download the [Steamworks SDK](https://partner.steamgames.com/)
2. Copy the following files from the steamworks sdk to the enlistment root
   1. `sdk\redistributable_bin\win64\steam_api64.dll`
   2. `sdk\redistributable_bin\win64\steam_api64.lib`
3. Copy the latest `SteamworksPy.dll` to the enlistment root from the
   [pre-built versions](https://github.com/philippj/SteamworksPy/releases)
4. Copy the `steamworks` folder for the corresponding version to the enlistment root from the SteamworksPy source code

## Running

1. Ensure the Steam client is running
2. Run `poetry run python main.py -h` for next steps

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
