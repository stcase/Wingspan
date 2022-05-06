import dataclasses
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from discord.data.data_controller import DataController
from discord.data.db_connection import DBConnection
from discord.data.models import Base, MessageType, StatusMessage
from wingspan_api.wapi import Wapi, Match, MatchState

data_folder = Path("tests/data/")


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
def game_waiting_obj(game_in_progress: str) -> Match:
    match = Match.from_dict(json.loads(game_in_progress)["Match"])
    match.State = MatchState.WAITING  # TODO, use real data
    return match


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
