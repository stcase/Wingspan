from unittest.mock import MagicMock, call

import pytest
from freezegun import freeze_time

from wingspan_bot.data.data_controller import DataController
from wingspan_bot.data.data_objects import FastestPlayer, PlayerStat, PlayerTurnTimings, TurnTiming
from wingspan_bot.data.models import MessageType
from tests.conftest import MessageTestData


class TestDataController:
    @pytest.mark.parametrize("channel,monitored,expected", (
        (None, True, {1: ["game1", "game2", "game3"], 2: ["game1", "game4"]}),
        (1, True, ["game1", "game2", "game3"]),
        (None, False, {1: ["game1", "game2", "game3"], 2: ["game1", "game4"]}),
        (2, False, ["game1", "game4"]),
    ))
    def test_get_monitored_matches(
            self,
            dc_monitor_many: DataController,
            channel: int,
            monitored: bool,
            expected: list[str] | dict[int, list[str]]) -> None:
        assert dc_monitor_many.get_monitored_matches(channel, monitored) == expected

    @pytest.mark.parametrize("channel,monitored,expected", (
        (None, True, {1: ["game2", "game3"], 2: ["game1", "game4"]}),
        (1, True, ["game2", "game3"]),
        (None, False, {1: ["game1", "game2", "game3"], 2: ["game1", "game4"]}),
        (1, False, ["game1", "game2", "game3"]),
    ))
    def test_get_monitored_matches_removed(
            self,
            dc_monitor_many: DataController,
            channel: int,
            monitored: bool,
            expected: list[str] | dict[int, list[str]]) -> None:
        dc_monitor_many.remove(1, "game1")
        assert dc_monitor_many.get_monitored_matches(channel, monitored) == expected

    def test_get_all_matches(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = [  # type: ignore[attr-defined]
            "game1", "game2", "game3", "game1", "game4"]
        matches = set(dc_monitor_many.get_matches())
        assert matches == {(1, "game1"), (1, "game2"), (1, "game3"), (2, "game1"), (2, "game4")}

    def test_get_all_matches_empty(self, data_controller: DataController) -> None:
        matches = list(data_controller.get_matches())
        assert len(matches) == 0

    def test_get_matches(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = ["game 1", "game 2", "game 3"]  # type: ignore[attr-defined]
        dc_monitor_many.db.add_or_update_score = MagicMock()  # type: ignore[assignment]
        matches = set(dc_monitor_many.get_matches(1))
        assert matches == {(1, "game 1"), (1, "game 2"), (1, "game 3")}

    def test_get_matches_updated_score(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = ["game 1", "game 2", "game 3"]  # type: ignore[attr-defined]
        dc_monitor_many.db.add_or_update_score = MagicMock()  # type: ignore[assignment]
        set(dc_monitor_many.get_matches(1))
        dc_monitor_many.db.add_or_update_score.assert_has_calls([call("game 1"), call("game 2"), call("game 3")])
        assert dc_monitor_many.db.add_or_update_score.call_count == 3

    def test_get_matches_empty(self, dc_monitor_many: DataController) -> None:
        matches = list(dc_monitor_many.get_matches(5))
        assert len(matches) == 0

    def test_get_matches_error(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = Exception("test error")  # type: ignore[attr-defined]
        matches = set(dc_monitor_many.get_matches(1))
        assert matches == {(1, "game1"), (1, "game2"), (1, "game3")}

    def test_add_to_empty(self, data_controller: DataController) -> None:
        assert data_controller.add(1, "game1")
        assert len(data_controller.db.get_matches()) == 1

    def test_add_to_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.get_monitored_matches()
        assert dc_monitor_many.add(2, "game2")
        after = dc_monitor_many.get_monitored_matches()
        assert before[1] == after[1]
        assert before[2] != after[2]

    def test_add_already_present(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.get_monitored_matches()
        assert not dc_monitor_many.add(1, "game3")
        after = dc_monitor_many.get_monitored_matches()
        assert before == after

    def test_remove_empty(self, data_controller: DataController) -> None:
        assert not data_controller.remove(1, "game1")

    def test_remove_from_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.db.get_matches()
        assert dc_monitor_many.remove(1, "game2")
        after = dc_monitor_many.db.get_matches()
        assert before != after

    def test_remove_nonexistent_from_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.get_monitored_matches()
        assert not dc_monitor_many.remove(5, "game2")
        after = dc_monitor_many.get_monitored_matches()
        assert before == after

    def test_add_remove_add(self, data_controller: DataController) -> None:
        assert data_controller.add(1, "game1")
        assert data_controller.remove(1, "game1")
        assert not data_controller.remove(1, "game1")
        assert data_controller.add(1, "game1")
        assert not data_controller.add(1, "game1")
        assert data_controller.remove(1, "game1")
        assert not data_controller.remove(1, "game1")

    @pytest.fixture
    def dc_many_subscriptions(self, data_controller: DataController) -> DataController:
        data_controller.subscribe(1, 1, "user1")
        data_controller.subscribe(1, 2, "user2")
        data_controller.subscribe(1, 21, "user2")
        data_controller.subscribe(2, 2, "user2")
        return data_controller

    def test_subscribe_already_present(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.subscribe(1, 2, "user2")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_subscribe_to_many(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert dc_many_subscriptions.subscribe(1, 3, "user3")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before != after

    def test_subscribe_to_empty(self, data_controller: DataController) -> None:
        assert data_controller.subscribe(1, 1, "user1")
        assert len(data_controller.get_subscriptions(1)) == 1

    def test_unsubscribe_from_many(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert dc_many_subscriptions.unsubscribe(1, 2, "user2")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before != after

    def test_unsubscribe_from_one(self, data_controller: DataController) -> None:
        data_controller.subscribe(1, 1, "user1")
        assert data_controller.unsubscribe(1, 1, "user1")
        assert len(data_controller.db.get_subscriptions(1)) == 0

    def test_unsubscribe_different_channel(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.unsubscribe(2, 1, "user1")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_unsubscribe_not_present(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.unsubscribe(1, 1, "user3")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_unsubscribe_empty(self, data_controller: DataController) -> None:
        assert not data_controller.unsubscribe(1, 1, "user1")

    def test_add_message_empty(self, data_controller: DataController, message_expecteds: MessageTestData) -> None:
        data_controller.add_message(
            match=message_expecteds.match_id,
            channel=message_expecteds.channel,
            player=message_expecteds.player_id,
            message_type=message_expecteds.msg_type)
        actual = data_controller.db.get_previous_message(message_expecteds.channel, message_expecteds.match_id)
        message_expecteds.assert_equal_status_message(actual)

    def test_fastest_player(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match-id", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match-id", 1, "player2", MessageType.NEW_TURN)
        assert (data_controller.get_fastest_player(1, "match-id") ==
                FastestPlayer(PlayerStat(wingspan_names=["player1"], score=24)))

    def test_fastest_player_completed(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match-id", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match-id", 1, None, MessageType.GAME_COMPLETE)
        assert (data_controller.get_fastest_player(1) ==
                FastestPlayer(PlayerStat(wingspan_names=["player1"], score=24)))

    def test_fastest_player_error(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match-id", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match-id", 1, None, MessageType.ERROR)
        assert (data_controller.get_fastest_player(1) ==
                FastestPlayer(PlayerStat(wingspan_names=[], score=0)))

    def test_fastest_player_incomplete(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match1", 1, "player1", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match2", 1, "player2", MessageType.NEW_TURN)

        assert (data_controller.get_fastest_player(1, "match1") ==
                FastestPlayer(PlayerStat(wingspan_names=[], score=0)))

    def test_fastest_player_many(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match1", 1, "player1", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match1", 1, "player2", MessageType.NEW_TURN)
        with freeze_time("2022-1-3"):
            data_controller.add_message("match1", 1, "player1", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player2", MessageType.NEW_TURN)
        with freeze_time("2022-1-4"):
            data_controller.add_message("match1", 1, "player2", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player1", MessageType.NEW_TURN)

        assert data_controller.get_fastest_player(1) == FastestPlayer(PlayerStat(wingspan_names=["player2"], score=24))

    def test_fastest_player_tie(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1"):
            data_controller.add_message("match1", 1, "player1", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-2"):
            data_controller.add_message("match1", 1, "player2", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player2", MessageType.NEW_TURN)
        with freeze_time("2022-1-3"):
            data_controller.add_message("match1", 1, "player1", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player1", MessageType.NEW_TURN)
        with freeze_time("2022-1-4"):
            data_controller.add_message("match1", 1, "player2", MessageType.NEW_TURN)
            data_controller.add_message("match2", 1, "player2", MessageType.NEW_TURN)

        assert (data_controller.get_fastest_player(1) ==
                FastestPlayer(PlayerStat(wingspan_names=["player1", "player2"], score=24)))

    def test_get_player_turn_timings_all(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1 1:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player1", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-1 2:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.REMINDER)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-1 3:10"):
            data_controller.add_message(match="match1", channel=1, player=None, message_type=MessageType.ERROR)
        with freeze_time("2022-1-1 4:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-1 5:10"):
            data_controller.add_message(match="match1", channel=1, player="player2", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player1", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-2 2:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-2 3:10"):
            data_controller.add_message(match="match1", channel=1, player=None, message_type=MessageType.GAME_COMPLETE)
        with freeze_time("2022-1-2 4:10"):
            data_controller.add_message(match="match1", channel=1, player=None, message_type=MessageType.ERROR)
            data_controller.add_message(match="match2", channel=1, player=None, message_type=MessageType.ERROR)
        with freeze_time("2022-1-2 5:10"):
            data_controller.add_message(match="match1", channel=1, player=None, message_type=MessageType.GAME_COMPLETE)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)

        assert (data_controller.get_player_turn_timings(channel_id=1) ==
               PlayerTurnTimings({"player1": TurnTiming({2: 2, 3: 1, 5: 1}), "player2": TurnTiming({2: 1, 5: 1})}))

    def test_get_player_turn_timings_match(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1 1:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player1", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-1 2:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.REMINDER)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-1 3:10"):
            data_controller.add_message(match="match1", channel=1, player="player2", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player1", message_type=MessageType.NEW_TURN)
        with freeze_time("2022-1-2 2:10"):
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)

        assert (data_controller.get_player_turn_timings(channel_id=1, match="match1") ==
                PlayerTurnTimings({"player1": TurnTiming({3: 1}), "player2": TurnTiming({2: 1})}))

    def test_get_player_turn_timings_none(self, data_controller: DataController) -> None:
        with freeze_time("2022-1-1 13:20"):
            data_controller.add_message(match="match2", channel=1, player="player1", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match2", channel=1, player="player2", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match1", channel=2, player="player2", message_type=MessageType.NEW_TURN)
            data_controller.add_message(match="match1", channel=1, player="player1", message_type=MessageType.REMINDER)
        assert data_controller.get_player_turn_timings(channel_id=1, match="match3") == PlayerTurnTimings()
