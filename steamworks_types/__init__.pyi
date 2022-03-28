from ctypes import *
from steamworks.enums import *
from steamworks.structs import *
from steamworks.exceptions import *
from enum import Enum as Enum
from steamworks.interfaces.apps import SteamApps as SteamApps
from steamworks.interfaces.friends import SteamFriends as SteamFriends
from steamworks.interfaces.matchmaking import SteamMatchmaking as SteamMatchmaking
from steamworks.interfaces.microtxn import SteamMicroTxn as SteamMicroTxn
from steamworks.interfaces.music import SteamMusic as SteamMusic
from steamworks.interfaces.screenshots import SteamScreenshots as SteamScreenshots
from steamworks.interfaces.users import SteamUsers as SteamUsers
from steamworks.interfaces.userstats import SteamUserStats as SteamUserStats
from steamworks.interfaces.utils import SteamUtils as SteamUtils
from steamworks.interfaces.workshop import SteamWorkshop as SteamWorkshop
from steamworks.methods import STEAMWORKS_METHODS as STEAMWORKS_METHODS

class STEAMWORKS:
    app_id: int
    def __init__(self, supported_platforms: list[str] = ...) -> None: ...
    def initialize(self) -> bool: ...
    def relaunch(self, app_id: int) -> bool: ...
    def unload(self) -> None: ...
    def loaded(self) -> bool: ...
    def run_callbacks(self) -> bool: ...
    def run_forever(self, base_interval: float = ...) -> None: ...
