from pathlib import Path

import pytest

data_folder = Path("tests/data/")


@pytest.fixture(scope="module")
def game_in_progress() -> str:
    with (data_folder / "game_in_progress.json").open("r") as f:
        return f.read()


@pytest.fixture(scope="module")
def all_games() -> str:
    with (data_folder / "all_games.json").open("r") as f:
        return f.read()
