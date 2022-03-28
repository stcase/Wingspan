from ctypes import *
from steamworks.enums import *
from steamworks.structs import *
from steamworks.exceptions import *
from enum import Enum as Enum
from typing import Any

class SteamMusic:
    steam: Any
    def __init__(self, steam: object) -> None: ...
    def MusicIsEnabled(self) -> bool: ...
    def MusicIsPlaying(self) -> bool: ...
    def MusicGetVolume(self) -> float: ...
    def MusicPause(self) -> None: ...
    def MusicPlay(self) -> None: ...
    def MusicPlayNext(self) -> None: ...
    def MusicPlayPrev(self) -> None: ...
    def MusicSetVolume(self, volume: float) -> None: ...
