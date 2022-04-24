from typing import Any

import pytest

from discord.data.data_controller import DataController
from discord.data.models import MessageType
from wingspan_api.wapi import Match, State


def generate_match(
        player_turn: str | None, seconds_remaining: int | None, state: State, match_id: str) -> Match:
    data: Any = {"Match": {"StateData": {"CurrentPlayerID": "Player1"}}}
    data["Match"]["Players"] = [
        {"ChilliConnectID": "Player1", "UserName": player_turn},
        {"ChilliConnectID": "Player2", "UserName": "Other"},
    ]
    data["Match"]["TurnTimeout"] = ({"SecondsRemaining": seconds_remaining, "Expires": ""}
                                    if state == State.IN_PROGRESS else None)
    data["Match"]["WaitingTimeout"] = ({"SecondsRemaining": seconds_remaining, "Expires": ""}
                                       if state == State.WAITING else None)
    data["Match"]["MatchID"] = match_id
    data["Match"]["State"] = state
    return Match.from_dict(data["Match"])  # type: ignore[attr-defined, no-any-return]


class TestDataControllerMessages:
    @pytest.mark.parametrize(
        "match,expected",
        [
            (generate_match("player", 60 * 60 * 30, State.IN_PROGRESS, "new_turn"),
             MessageType.NEW_TURN),
            (generate_match("player", 60 * 60 * 10, State.IN_PROGRESS, "reminder"),
             MessageType.REMINDER),
            (generate_match(None, None, State.COMPLETED, "completed"),
             MessageType.GAME_COMPLETE),
            (generate_match(None, None, State.WAITING, "waiting"),
             MessageType.WAITING),
            (generate_match(None, None, State.READY, "ready"),
             MessageType.READY),
            ("error", MessageType.ERROR),
        ],
    )
    def test_get_message_type(
            self, data_controller: DataController, match: Match | str, expected: MessageType) -> None:
        assert data_controller.get_message_type(match) == expected

    @pytest.mark.parametrize(
        "match,sent_message,expected",
        [
            (
                    generate_match("player", 60 * 60 * 30, State.IN_PROGRESS, "message_sent-start"),
                    (None, MessageType.WAITING),
                    True,
            ),
            (
                    generate_match("player", 60 * 60 * 30, State.IN_PROGRESS, "no_messages_sent_yet"),
                    None,
                    True,
            ),
            (
                    generate_match("player", 60 * 60 * 10, State.IN_PROGRESS, "no_messages_sent-lt_24h"),
                    None,
                    True,
            ),
            (
                    generate_match("player", 60 * 60 * 10, State.IN_PROGRESS, "message_sent_before_24h-now_less"),
                    ("player", MessageType.NEW_TURN),
                    True,
            ),
            (
                    generate_match("player", 60 * 60 * 25, State.IN_PROGRESS, "messge_already_sent"),
                    ("player", MessageType.NEW_TURN),
                    False,
            ),
            (
                    generate_match("player", 60 * 60 * 10, State.IN_PROGRESS, "message_already_sent_lt_24h"),
                    ("player", MessageType.REMINDER),
                    False,
            ),
            (
                    generate_match("player", 60 * 60 * 25, State.IN_PROGRESS, "message_sent-prev_player"),
                    ("prev_player", MessageType.NEW_TURN),
                    True,
            ),
            (
                    generate_match("player", 60 * 60 * 20, State.IN_PROGRESS, "message_sent-prev_player-lt24h"),
                    ("prev_player", MessageType.REMINDER),
                    True,
            ),
            (
                    generate_match(None, None, State.COMPLETED, "message_sent_prev-end_game"),
                    ("player", MessageType.REMINDER),
                    True,
            ),
            (
                    generate_match(None, None, State.COMPLETED, "message_sent-end_game"),
                    (None, MessageType.GAME_COMPLETE),
                    False,
            ),
            (
                    generate_match(None, None, State.WAITING, "no_messages_sent-start"),
                    None,
                    True,
            ),
            (
                    generate_match(None, None, State.WAITING, "message_sent-start"),
                    (None, MessageType.WAITING),
                    False,
            ),
            (
                    generate_match(None, None, State.READY, "no_messages_sent-ready"),
                    None,
                    True,
            ),
            (
                    generate_match(None, None, State.READY, "message_sent-ready"),
                    (None, MessageType.READY),
                    False,
            ),
            (
                    generate_match("player", 60 * 60 * 20, State.IN_PROGRESS, "message_sent-error"),
                    (None, MessageType.ERROR),
                    True,
            ),
            (
                    "error",
                    ("player", MessageType.ERROR),
                    True,
            ),
            (
                    "error",
                    (None, MessageType.ERROR),
                    False,
            ),
            (
                    "error",
                    ("player", MessageType.NEW_TURN),
                    True,
            ),
        ],
    )
    def test_should_send_message(
            self,
            data_controller: DataController,
            match: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        channel = 1
        if sent_message is not None:
            player = sent_message[0]
            message_type = sent_message[1]
            match_id = str(match)
            data_controller.db.add_message(match=match_id, channel=channel, player=player, message_type=message_type)
        assert data_controller.should_send_message(channel_id=channel, match=match) == expected
