from ctypes import *
from enum import Enum as Enum
from typing import Any

class SteamScreenshots:
    steam: Any
    def __init__(self, steam: object) -> None: ...
    def AddScreenshotToLibrary(
        self, filename: str, thumbnail_filename: str, width: int, height: int
    ) -> int: ...
    def HookScreenshots(self, hook: bool) -> None: ...
    def IsScreenshotsHooked(self) -> bool: ...
    def SetLocation(self, screenshot_handle: int, location: str) -> bool: ...
    def TriggerScreenshot(self) -> None: ...
