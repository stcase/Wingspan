from ctypes import *
from enum import Enum as Enum
from typing import Any

class SteamUtils:
    steam: Any
    def __init__(self, steam: object) -> None: ...
    def OverlayNeedsPresent(self) -> bool: ...
    def GetAppID(self) -> int: ...
    def GetCurrentBatteryPower(self) -> int: ...
    def GetIPCCallCount(self) -> int: ...
    def GetIPCountry(self) -> str: ...
    def GetSecondsSinceAppActive(self) -> int: ...
    def GetSecondsSinceComputerActive(self) -> int: ...
    def GetServerRealTime(self) -> int: ...
    def GetSteamUILanguage(self) -> str: ...
    def IsOverlayEnabled(self) -> bool: ...
    def IsSteamInBigPictureMode(self) -> bool: ...
    def IsVRHeadsetStreamingEnabled(self) -> bool: ...
    def SetOverlayNotificationInset(self, horizontal: int, vertical: int) -> None: ...
    def SetOverlayNotificationPosition(
        self, position: ENotificationPosition
    ) -> None: ...
    def SetVRHeadsetStreamingEnabled(self, enabled: bool) -> None: ...
    def ShowGamepadTextInput(
        self,
        input_mode: EGamepadTextInputLineMode,
        line_input_mode: EGamepadTextInputMode,
        description: str,
        max_characters: int,
        preset: str,
    ) -> bool: ...
    def StartVRDashboard(self) -> None: ...
