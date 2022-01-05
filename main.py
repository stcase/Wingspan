import argparse

from wingspan_api.wapi import Wapi


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--list", help="Print active games", action="store_true")
    group.add_argument("-i", "--info", help="Print game info for a given match id", type=str)
    args = parser.parse_args()

    if args.list:
        print_games()
    elif args.info is not None:
        print_game_info(args.info)


def print_games():
    wapi = Wapi()
    games = wapi.get_games()
    for game in games.games:
        print(game.match_id)
        for player in game.players:
            print(f" {player.username}")


def print_game_info(match_id):
    wapi = Wapi()
    game_info = wapi.get_game_info(match_id)
    print(game_info.current_turn.username)
    print(game_info.hours_remaining)


if __name__ == "__main__":
    main()
