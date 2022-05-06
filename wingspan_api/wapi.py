from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import requests
from dataclasses_json import DataClassJsonMixin
from requests import Response

logger = logging.getLogger(__name__)

try:
    # this is only present after installation and not needed for tests
    from steamworks import STEAMWORKS
except ImportError:
    logger.warn("Failed to import steamworks")

HOST = "https://connect.chilliconnect.com"


class MatchState(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    WAITING = "WAITING"  # waiting for the match to start
    COMPLETED = "COMPLETED"  # the match is over


@dataclass
class Score(DataClassJsonMixin):
    ID: str
    Score: int
    BirdPoints: int
    BonusCardPoints: int
    GoalsPoints: int
    EggsPoints: int
    CachedFoodPoints: int
    TuckedCardsPoints: int
    FoodTokens: int


@dataclass
class OutcomeData(DataClassJsonMixin):
    Winner: str


@dataclass
class StateData(DataClassJsonMixin):
    CurrentPlayerID: str
    Scores: str

    @property
    def scores(self) -> list[Score]:
        return Score.schema().load(json.loads(self.Scores)["V"], many=True)


@dataclass
class Timeout(DataClassJsonMixin):
    SecondsRemaining: int
    Expires: str


@dataclass
class Player(DataClassJsonMixin):
    ChilliConnectID: str
    UserName: str


@dataclass
class Match(DataClassJsonMixin):
    MatchID: str
    State: MatchState
    WaitingTimeout: Timeout | None
    TurnTimeout: Timeout | None
    Players: list[Player]
    StateData: StateData | None = None  # not in the data from Matches
    OutcomeData: OutcomeData | None = None  # not in the data from Matches?, null if game not complete

    def is_timed_out(self) -> bool:
        """
        Returns true if the game completed from a timeout, false otherwise or if it doesn't have complete match info
        (and thus it can't be determined whether it ended with a timeout or not)
        """
        return self.State == MatchState.COMPLETED and self.OutcomeData is None and self.StateData is not None

    def get_player(self, player_id: str) -> Player | None:
        for player in self.Players:
            if player.ChilliConnectID == player_id:
                return player
        return None

    def get_player_username(self, player_id: str) -> str | None:
        player = self.get_player(player_id)
        return player.UserName if player is not None else None

    @property
    def current_player(self) -> Player | None:
        if self.StateData is None:
            raise ValueError("No StateData for this match")
        return self.get_player(self.StateData.CurrentPlayerID)

    @property
    def current_player_name(self) -> str | None:
        current_player = self.current_player
        return None if current_player is None else current_player.UserName

    @property
    def hours_remaining(self) -> float | None:
        if self.State == MatchState.IN_PROGRESS:
            if self.TurnTimeout is None:
                raise ValueError("Unexpected game state")
            return self.TurnTimeout.SecondsRemaining / 60 / 60
        if self.State == MatchState.WAITING:
            if self.WaitingTimeout is None:
                raise ValueError("Unexpected game state")
            return self.WaitingTimeout.SecondsRemaining / 60 / 60
        return None

    def __str__(self) -> str:
        return self.MatchID


@dataclass(frozen=True)
class Matches(DataClassJsonMixin):
    Matches: list[Match]


class Wapi:
    def __init__(self, access_token: str | None = None):
        if access_token is not None:
            self.access_token = access_token
        else:
            self.generate_access_token()

    def generate_access_token(self) -> None:
        steamworks = STEAMWORKS()
        steamworks.initialize()

        session_ticket = steamworks.Users.GetAuthSessionTicket()
        resp = self.get_login(session_ticket)
        self.access_token = resp["ConnectAccessToken"]

    def get_login(self, session_ticket: str) -> Any:
        r = requests.post(
            url=f"{HOST}/1.0/player/login/steam",
            data={
                "SessionTicket": session_ticket,
                "CreatePlayer": True,
                "DeviceType": "DESKTOP",
                "Platform": "WINDOWS",
                "Date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            },
            headers={"Game-Token": "xCv44nsmb6bP9q8fAIJn1uy70EzyfJJH"},
        )
        return r.json()

    def _get_info(self, path: str, data: dict[str, str]) -> Response:
        r = requests.post(
            url=f"{HOST}/{path}",
            data=data,
            headers={"Connect-Access-Token": self.access_token},
        )
        if r.status_code != 200 and r.json()["Code"] == 1003:
            # expired connect access token
            logging.info("Access token expired, generating a new one")
            self.generate_access_token()
            r = requests.post(
                url=f"{HOST}/{path}",
                data=data,
                headers={"Connect-Access-Token": self.access_token},
            )
        r.raise_for_status()
        return r

    def get_games(self) -> Matches:
        r = self._get_info("1.0/multiplayer/async/match/player/get", {})
        return Matches.from_dict(r.json())

    def get_game_info(self, match_id: str) -> Match:
        r = self._get_info("1.0/multiplayer/async/match/get", {"MatchID": match_id})
        return Match.from_dict(r.json()["Match"])
