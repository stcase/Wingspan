from datetime import datetime
from typing import Any, Tuple, Sequence

import requests

from steamworks import STEAMWORKS

HOST = "https://connect.chilliconnect.com"


class JSONData:
    def __init__(self, data: Any):
        self.data = data


class Player(JSONData):
    @property
    def username(self) -> str:
        return self.data["UserName"]


class GameInfo(JSONData):
    @property
    def current_turn(self) -> Player:
        player_id: str = self.data["Match"]["StateData"]["CurrentPlayerID"]
        players = self.data["Match"]["Players"]
        for player in players:
            if player["ChilliConnectID"] == player_id:
                return Player(player)
        raise RuntimeError(f"Player match for {player_id} not found in {players}")

    @property
    def hours_remaining(self) -> float:
        return self.data["Match"]["TurnTimeout"]["SecondsRemaining"] / 60 / 60

    @property
    def game_id(self):
        return self.data["Match"]["MatchID"]

    @property
    def is_valid(self):
        return "Error" not in self.data

    @property
    def is_completed(self) -> bool:
        return self.data["Match"]["State"] == "COMPLETED"

    @property
    def waiting_to_start(self) -> bool:
        return self.data["Match"]["State"] == "WAITING"


class Game(JSONData):
    @property
    def match_id(self) -> str:
        return self.data["MatchID"]

    @property
    def players(self) -> Sequence[Player]:
        for player in self.data["Players"]:
            yield Player(player)


class Games(JSONData):
    @property
    def games(self) -> Sequence[Game]:
        for game in self.data["Matches"]:
            yield Game(game)


class Wapi:
    def __init__(self, access_token: str = None):
        if access_token is not None:
            self.access_token = access_token
        else:
            self.generate_access_token()

    def generate_access_token(self):
        steamworks = STEAMWORKS()
        steamworks.initialize()

        session_ticket = steamworks.Users.GetAuthSessionTicket()
        resp = self.get_login(session_ticket)
        self.access_token = resp["ConnectAccessToken"]

    def get_login(self, session_ticket):
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

    def get_games(self) -> Games:
        r = requests.post(
            url=f"{HOST}/1.0/multiplayer/async/match/player/get",
            data={},
            headers={"Connect-Access-Token": self.access_token},
        )
        return Games(r.json())

    def get_game_info(self, match_id: str) -> GameInfo:
        r = requests.post(
            url=f"{HOST}/1.0/multiplayer/async/match/get",
            data={"MatchID": match_id},
            headers={"Connect-Access-Token": self.access_token},
        )
        return GameInfo(r.json())
