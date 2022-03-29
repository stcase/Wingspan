import argparse
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configs_example import BOT_SECRET_TOKEN, CHANNEL
else:
    from configs import BOT_SECRET_TOKEN, CHANNEL
from wingspan_api.wapi import Wapi
from discord.bot import Bot


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--list", help="Print active games", action="store_true")
    group.add_argument(
        "-i", "--info", help="Print game info for a given match id", type=str
    )
    group.add_argument("-b", "--bot", help="Run discord bot", action="store_true")
    args = parser.parse_args()

    if args.list:
        print_games()
    elif args.info is not None:
        print_game_info(args.info)
    elif args.bot:
        run_bot()


def print_games() -> None:
    wapi = Wapi()
    games = wapi.get_games()
    for game in games.games:
        print(game.match_id)
        for player in game.players:
            print(f" {player.username}")


def print_game_info(match_id: str) -> None:
    wapi = Wapi()
    game_info = wapi.get_game_info(match_id)
    print(game_info.current_turn.username)
    print(game_info.hours_remaining)


def run_bot() -> None:
    wapi = Wapi()
    bot = Bot(wapi=wapi, channel_id=CHANNEL, command_prefix="!")
    bot.run(BOT_SECRET_TOKEN)


if __name__ == "__main__":
    main()
