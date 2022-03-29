from ctypes import *
from enum import Enum as Enum
from typing import Any

class SteamUserStats:
    steam: Any
    def __init__(self, steam: object) -> None: ...
    def GetAchievement(self, name: str) -> bool: ...
    def GetNumAchievements(self) -> int: ...
    def GetAchievementName(self, index: int) -> str: ...
    def GetAchievementDisplayAttribute(self, name: str, key: str) -> str: ...
    def GetStatFloat(self, name: str) -> float: ...
    def GetStatInt(self, name: str) -> float: ...
    def ResetAllStats(self, achievements: bool) -> bool: ...
    def RequestCurrentStats(self) -> bool: ...
    def SetAchievement(self, name: str) -> bool: ...
    def SetStat(self, name: str, value: object) -> bool: ...
    def StoreStats(self) -> bool: ...
    def ClearAchievement(self, name: str) -> bool: ...
    def SetFindLeaderboardResultCallback(self, callback: object) -> bool: ...
    def FindLeaderboard(
        self, name: str, callback: object = ..., override_callback: bool = ...
    ) -> bool: ...
