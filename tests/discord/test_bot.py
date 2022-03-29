import asyncio
from enum import Enum
from typing import Any, Optional

import pytest

from discord.bot import Bot, Message
from wingspan_api.wapi import Wapi, GameInfo


class BotTest(Bot):
    def save_data(self) -> None:
        pass

    def loead_data(self) -> None:
        pass


class GameState(Enum):
    IN_PROGRESS = 1
    WAITING = 2
    COMPLETED = 3
    ERROR = 4


def generate_game_info(
        player_turn: Optional[str], seconds_remaining: Optional[int], state: GameState, match_id: str) -> GameInfo:
    data: Any = {"Match": {"StateData": {"CurrentPlayerID": "Player1"}}}
    data["Match"]["Players"] = [
        {"ChilliConnectID": "Player1", "UserName": player_turn},
        {"ChilliConnectID": "Player2", "UserName": "Other"},
    ]
    data["Match"]["TurnTimeout"] = {"SecondsRemaining": seconds_remaining}
    data["Match"]["MatchID"] = match_id
    if state == GameState.IN_PROGRESS:
        data["Match"]["State"] = "IN_PROGRESS"
    elif state == GameState.WAITING:
        data["Match"]["State"] = "WAITING"
    elif state == GameState.COMPLETED:
        data["Match"]["State"] = "COMPLETED"
    elif state == GameState.ERROR:
        data["Error"] = "Problem"
    return GameInfo(data)


class TestBot:
    @pytest.mark.parametrize(
        "game_info,expected",
        [
            (generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "message_sent-start"),
             "player's turn"),
            (generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "no_messages_sent_yet"),
             "player's turn"),
            (generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS, "no_messages_sent-lt_24h"),
             ":rotating_light:"),
            (generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS, "message_sent_before_24h-now_less"),
             ":rotating_light:"),
            (generate_game_info("player", 60 * 60 * 25, GameState.IN_PROGRESS, "message_already_sent-req_turn"),
             "player's turn"),
            (generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS, "message_already_sent_lt_24h-req_turn"),
             ":rotating_light:"),
            (generate_game_info("player", 60 * 60 * 25, GameState.IN_PROGRESS, "message_sent-prev_player"),
             "player's turn"),
            (generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "message_sent-prev_player2"),
             "player's turn"),
            (generate_game_info("player", 60 * 60 * 20, GameState.IN_PROGRESS, "message_sent-prev_player-lt24h"),
             ":rotating_light:"),
            (generate_game_info("player", 60 * 60 * 15, GameState.IN_PROGRESS, "message_sent-prev_player-lt24h2"),
             ":rotating_light:"),
            (generate_game_info(None, None, GameState.COMPLETED, "message_sent_prev-end_game"),
             "is Complete"),
            (generate_game_info(None, None, GameState.COMPLETED, "message_sent-end_game-always_send"),
             "is Complete"),
            (generate_game_info(None, None, GameState.WAITING, "no_messages_sent-start"),
             "waiting to start"),
            (generate_game_info(None, None, GameState.WAITING, "message_sent-start-req_turn"),
             "waiting to start"),
        ],
    )
    def test_send_message(
            self, game_info: GameInfo, expected: str) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        wapi = Wapi(access_token="test")
        bot = BotTest(wapi, channel_id=0, command_prefix="!")
        bot.subscriptions = {}
        message = ""

        async def send(msg: str) -> None:
            nonlocal message
            message = msg

        asyncio.run(bot.send_message(send, game_info.game_id, game_info))  # type: ignore[arg-type]
        loop.close()  # TODO: looks like there might be some kind of event loop leak going on, and this doesn't fix it

        assert expected in message
        assert game_info.game_id in message
        assert bot.sent_messages[game_info.game_id] ==\
               Message(player=game_info.current_turn.username, hours_remaining=game_info.hours_remaining)

    @pytest.mark.parametrize(
        "match_id,game_info,sent_message,expected",
        [
            (
                    "message_sent-start",
                    generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "message_sent-start"),
                    Message(None, 0),
                    True,
            ),
            (
                    "no_messages_sent_yet",
                    generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "no_messages_sent_yet"),
                    None,
                    True,
            ),
            (
                    "no_messages_sent-lt_24h",
                    generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS, "no_messages_sent-lt_24h"),
                    None,
                    True,
            ),
            (
                    "message_sent_before_24h-now_less",
                    generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS,
                                       "message_sent_before_24h-now_less"),
                    Message("player", 30),
                    True,
            ),
            (
                    "messge_already_sent",
                    generate_game_info("player", 60 * 60 * 25, GameState.IN_PROGRESS, "messge_already_sent"),
                    Message("player", 60 * 60 * 30),
                    False,
            ),
            (
                    "message_already_sent_lt_24h",
                    generate_game_info("player", 60 * 60 * 10, GameState.IN_PROGRESS, "message_already_sent_lt_24h"),
                    Message("player", 15),
                    False,
            ),
            (
                    "message_sent-prev_player",
                    generate_game_info("player", 60 * 60 * 25, GameState.IN_PROGRESS, "message_sent-prev_player"),
                    Message("prev_player", 30),
                    True,
            ),
            (
                    "message_sent-prev_player2",
                    generate_game_info("player", 60 * 60 * 30, GameState.IN_PROGRESS, "message_sent-prev_player2"),
                    Message("prev_player", 25),
                    True,
            ),
            (
                    "message_sent-prev_player-lt24h",
                    generate_game_info("player", 60 * 60 * 20, GameState.IN_PROGRESS, "message_sent-prev_player-lt24h"),
                    Message("prev_player", 15),
                    True,
            ),
            (
                    "message_sent-prev_player-lt24h2",
                    generate_game_info("player", 60 * 60 * 15, GameState.IN_PROGRESS,
                                       "message_sent-prev_player-lt24h2"),
                    Message("prev_player", 20),
                    True,
            ),
            (
                    "message_sent_prev-end_game",
                    generate_game_info(None, None, GameState.COMPLETED, "message_sent_prev-end_game"),
                    Message("player", 15),
                    True,
            ),
            (
                    "message_sent-end_game",
                    generate_game_info(None, None, GameState.COMPLETED, "message_sent-end_game"),
                    Message(None, None),
                    False,
            ),
            (
                    "no_messages_sent-start",
                    generate_game_info(None, None, GameState.WAITING, "no_messages_sent-start"),
                    None,
                    True,
            ),
            (
                    "message_sent-start",
                    generate_game_info(None, None, GameState.WAITING, "message_sent-start"),
                    Message(None, 0),
                    False,
            ),
        ],
    )
    def test_should_send_message(
            self, match_id: str, game_info: GameInfo, sent_message: Message, expected: bool) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        wapi = Wapi(access_token="test")
        bot = BotTest(wapi, channel_id=0, command_prefix="!")
        bot.sent_messages = {match_id: sent_message}
        bot.subscriptions = {}

        # actual = asyncio.run(bot.should_send_message(game_info.game_id, game_info))
        actual = bot.should_send_message(game_info.game_id, game_info)
        loop.close()  # TODO: looks like there might be some kind of event loop leak going on, and this doesn't fix it

        assert actual == expected
