import dataclasses
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from wingspan_bot.data.data_controller import DataController
from wingspan_bot.data.db_connection import DBConnection
from wingspan_bot.data.models import Base, MessageType, StatusMessage
from wingspan_api.wapi import Wapi, Match, MatchState

data_folder = Path(__file__).parent / "data"


@pytest.fixture
def game_in_progress() -> str:
    with (data_folder / "game_in_progress.json").open("r") as f:
        return f.read()


@pytest.fixture
def game_timed_out() -> str:
    with (data_folder / "game_timed_out.json").open("r") as f:
        return f.read()


@pytest.fixture
def game_completed() -> str:
    with (data_folder / "game_completed.json").open("r") as f:
        return f.read()


@pytest.fixture
def game_waiting() -> str:
    with (data_folder / "game_waiting.json").open("r") as f:
        return f.read()


@pytest.fixture
def game_waiting_for_join() -> str:
    with (data_folder / "game_waiting_for_join.json").open("r") as f:
        return f.read()


@pytest.fixture
def games() -> str:
    with (data_folder / "games.json").open("r") as f:
        return f.read()


@pytest.fixture
def game_in_progress_obj(game_in_progress: str) -> Match:
    return Match.from_dict(json.loads(game_in_progress)["Match"])


@pytest.fixture
def game_in_progress_low_time_obj(game_in_progress: str) -> Match:
    match = Match.from_dict(json.loads(game_in_progress)["Match"])
    assert match.TurnTimeout is not None
    match.TurnTimeout.SecondsRemaining = 10  # TODO, use real data
    return match


@pytest.fixture
def game_timed_out_obj(game_timed_out: str) -> Match:
    return Match.from_dict(json.loads(game_timed_out)["Match"])


@pytest.fixture
def game_completed_obj(game_completed: str) -> Match:
    return Match.from_dict(json.loads(game_completed)["Match"])


@pytest.fixture
def game_ready_obj(game_in_progress: str) -> Match:
    match = Match.from_dict(json.loads(game_in_progress)["Match"])
    match.State = MatchState.READY  # TODO, use real data
    return match


@pytest.fixture
def game_waiting_obj(game_waiting: str) -> Match:
    return Match.from_dict(json.loads(game_waiting)["Match"])


@pytest.fixture
def game_waiting_for_join_obj(game_waiting_for_join: str) -> Match:
    return Match.from_dict(json.loads(game_waiting_for_join)["Match"])


@pytest.fixture
def db() -> DBConnection:
    db = DBConnection("sqlite://")
    Base.metadata.create_all(db.engine)
    return db


@pytest.fixture
def data_controller(db: DBConnection) -> DataController:
    wapi = Wapi("test-token")
    data_controller = DataController(db, wapi)

    data_controller.wapi.get_game_info = MagicMock()  # type: ignore[assignment]

    return data_controller


@pytest.fixture
def dc_monitor_many(data_controller: DataController) -> DataController:
    with freeze_time("2020-01-01 01:01:01"):
        data_controller.add(1, "game1")
        data_controller.add(1, "game2")
        data_controller.add(1, "game3")
        data_controller.add(2, "game1")
        data_controller.add(2, "game4")
    return data_controller


@dataclasses.dataclass
class MessageTestData:
    match_id: str
    channel: int
    player_id: str
    msg_type: MessageType

    def call_add(self, db: DBConnection) -> None:
        db.add_message(
            match=self.match_id,
            channel=self.channel,
            player=self.player_id,
            message_type=self.msg_type)

    def assert_equal_status_message(self, status_msg: StatusMessage | None) -> None:
        assert status_msg is not None
        assert status_msg.match_id == self.match_id
        assert status_msg.channel == self.channel
        assert status_msg.player_turn == self.player_id
        assert status_msg.message_type == self.msg_type


@pytest.fixture
def message_expecteds() -> MessageTestData:
    return MessageTestData(match_id="match-id", channel=1, player_id="player-id", msg_type=MessageType.REMINDER)
