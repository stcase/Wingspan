import argparse
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from wingspan_api.wapi import Wapi
from wingspan_bot.bot import Bot
from wingspan_bot.data.db_connection import DBConnection
from wingspan_bot.data.data_controller import DataController

if TYPE_CHECKING:
    from configs_example import BOT_SECRET_TOKEN, DB_CONNECTION
else:
    from configs import BOT_SECRET_TOKEN, DB_CONNECTION


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--list", help="Print active games", action="store_true")
    group.add_argument(
        "-i", "--info", help="Print game info for a given match id", type=str, metavar="MATCHID"
    )
    group.add_argument(
        "-s",
        "--save",
        help="Save game info for a given match id and file name",
        nargs=2,
        type=str,
        metavar=("MATCHID, FILENAME")
    )
    group.add_argument("-b", "--bot", help="Run discord bot", action="store_true")
    args = parser.parse_args()

    if args.list:
        print_games()
    elif args.info is not None:
        print_game_info(args.info)
    elif args.save is not None:
        save_game_info(args.save[0], args.save[1])
    elif args.bot:
        run_bot()


def print_games() -> None:
    wapi = Wapi()
    matches = wapi.get_games()
    for match in matches.Matches:
        print(match.MatchID)
        for player in match.Players:
            print(f" {player.UserName}")


def print_game_info(match_id: str) -> None:
    wapi = Wapi()
    game_info = wapi.get_game_info(match_id)
    if game_info.current_player is not None:
        print(game_info.current_player.UserName)
        print(game_info.hours_remaining)
    else:
        print(game_info.State)


def save_game_info(match_id: str, file_name: str) -> None:
    wapi = Wapi()
    game_info = wapi.get_game_info(match_id)
    with Path(file_name).open("w") as f:
        f.write(game_info.to_json())


def run_bot() -> None:
    wapi = Wapi()
    db_conn = DBConnection(DB_CONNECTION)
    data_controller = DataController(db_connection=db_conn, wapi=wapi)
    bot = Bot(data_controller=data_controller, command_prefix="!")
    bot.run(BOT_SECRET_TOKEN)


if __name__ == "__main__":
    main()
