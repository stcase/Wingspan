from pathlib import Path
from unittest.mock import MagicMock

import pytest

from discord.data.data_controller import DataController
from discord.data.db_connection import DBConnection
from discord.data.models import Base
from wingspan_api.wapi import Wapi

data_folder = Path("tests/data/")


@pytest.fixture
def game_in_progress() -> str:
    with (data_folder / "game_in_progress.json").open("r") as f:
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
def data_controller() -> DataController:
    wapi = Wapi("test-token")
    db = DBConnection("sqlite://")
    data_controller = DataController(db, wapi)
    Base.metadata.create_all(db.engine)

    data_controller.wapi.get_game_info = MagicMock()  # type: ignore[assignment]

    return data_controller
