from ctypes import *
from steamworks.enums import *
from steamworks.structs import *
from steamworks.exceptions import *
from enum import Enum as Enum
from typing import Any

class SteamMicroTxn:
    steam: Any
    def __init__(self, steam: object) -> None: ...
    def SetAuthorizationResponseCallback(self, callback: object) -> bool: ...
