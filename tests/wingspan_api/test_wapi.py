import json
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch

from wingspan_api.wapi import Player, Wapi

in_progress_players = [Player(UserName="jeff", ChilliConnectID="jeff_id"),
                       Player(UserName="shuai", ChilliConnectID="shuai_id"),
                       Player(UserName="steven", ChilliConnectID="steven_id"),
                       Player(UserName="victor", ChilliConnectID="victor_id")]


class TestWapi:
    @pytest.fixture
    def wapi(self, monkeypatch: MonkeyPatch, game_in_progress: str, game_completed: str, games: str) -> Wapi:
        class MockRequest:
            def __init__(self, path: str, data: dict[str, str]) -> None:
                if len(data) == 0:
                    self.result = json.loads(games)
                else:
                    if data["MatchID"] == "in-progress-match-id":
                        self.result = json.loads(game_in_progress)
                    else:
                        self.result = json.loads(game_completed)

            def json(self) -> Any:
                return self.result

        monkeypatch.setattr(Wapi, "_get_info", MockRequest)
        wapi = Wapi("test_token")
        return wapi

    def test_get_games(self, wapi: Wapi) -> None:
        assert len(wapi.get_games().Matches) == 2

    def test_players_in_game(self, wapi: Wapi) -> None:
        assert wapi.get_game_info("in-progress-match-id").Players == in_progress_players

    def test_get_player(self, wapi: Wapi) -> None:
        expected = Player(UserName="steven", ChilliConnectID="steven_id")
        actual = wapi.get_game_info("in-progress-match-id").get_player(expected.ChilliConnectID)
        assert actual == expected

    def test_current_player(self, wapi: Wapi) -> None:
        expected = Player(UserName="victor", ChilliConnectID="victor_id")
        actual = wapi.get_game_info("in-progress-match-id").current_player
        assert actual == expected

    def test_current_player_name_in_progress(self, wapi: Wapi) -> None:
        assert wapi.get_game_info("in-progress-match-id").current_player_name == "victor"

    def test_current_player_name_completed(self, wapi: Wapi) -> None:
        assert wapi.get_game_info("completed-match-id").current_player_name is None

    def test_hours_remaining_in_progress(self, wapi: Wapi) -> None:
        assert wapi.get_game_info("in-progress-match-id").hours_remaining == 42
