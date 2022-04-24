from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import requests
from dataclasses_json import dataclass_json
from requests import Response

if TYPE_CHECKING:
    from steamworks_types import STEAMWORKS
else:
    from steamworks import STEAMWORKS

HOST = "https://connect.chilliconnect.com"

logger = logging.getLogger(__name__)


class State(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    WAITING = "WAITING"  # waiting for the match to start
    COMPLETED = "COMPLETED"  # the match is over


@dataclass_json
@dataclass
class StateData:
    CurrentPlayerID: str


@dataclass_json()
@dataclass
class Timeout:
    SecondsRemaining: int
    Expires: str


@dataclass_json()
@dataclass
class Player:
    ChilliConnectID: str
    UserName: str


@dataclass_json()
@dataclass
class Match:
    MatchID: str
    State: State
    WaitingTimeout: Timeout | None
    TurnTimeout: Timeout | None
    Players: list[Player]
    StateData: StateData | None = None  # not in the data from Matches

    @property
    def current_player(self) -> Player | None:
        if self.StateData is None:
            raise ValueError("No StateData for this match")
        for player in self.Players:
            if player.ChilliConnectID == self.StateData.CurrentPlayerID:
                return player
        return None

    @property
    def current_player_name(self) -> str | None:
        current_player = self.current_player
        return None if current_player is None else current_player.UserName

    @property
    def hours_remaining(self) -> float | None:
        if self.State == State.IN_PROGRESS:
            if self.TurnTimeout is None:
                raise ValueError("Unexpected game state")
            return self.TurnTimeout.SecondsRemaining / 60 / 60
        if self.State == State.WAITING:
            if self.WaitingTimeout is None:
                raise ValueError("Unexpected game state")
            return self.WaitingTimeout.SecondsRemaining / 60 / 60
        return None

    def __str__(self) -> str:
        return self.MatchID


@dataclass_json()
@dataclass
class Matches:
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
        return Matches.from_dict(r.json())  # type: ignore

    def get_game_info(self, match_id: str) -> Match:
        r = self._get_info("1.0/multiplayer/async/match/get", {"MatchID": match_id})
        return Match.from_dict(r.json()["Match"])  # type: ignore
