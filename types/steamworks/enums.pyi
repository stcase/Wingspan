from enum import Enum, IntFlag

class Arch(Enum):
    x86: int
    x64: int

class FriendFlags(Enum):
    NONE: int
    BLOCKED: int
    FRIENDSHIP_REQUESTED: int
    IMMEDIATE: int
    CLAN_MEMBER: int
    ON_GAME_SERVER: int
    REQUESTING_FRIENDSHIP: int
    REQUESTING_INFO: int
    IGNORED: int
    IGNORED_FRIEND: int
    SUGGESTED: int
    ALL: int

class EWorkshopFileType(Enum):
    COMMUNITY: int
    MICRO_TRANSACTION: int
    COLLECTION: int
    ART: int
    VIDEO: int
    SCREENSHOT: int
    GAME: int
    SOFTWARE: int
    CONCEPT: int
    WEB_GUIDE: int
    INTEGRATED_GUIDE: int
    MERCH: int
    CONTROLLER_BINDING: int
    STEAMWORKS_ACCESS_INVITE: int
    STEAM_VIDEO: int
    GAME_MANAGED_ITEM: int
    MAX: int

class EResult(Enum):
    OK: int
    FAIL: int
    NO_CONNECTION: int
    INVALID_PASSWORD: int
    LOGGED_IN_ELSEWHERE: int
    INVALID_PROTOCOL_VER: int
    INVALID_PARAM: int
    FILE_NOT_FOUND: int
    BUSY: int
    INVALID_STATE: int
    INVALID_NAME: int
    INVALID_EMAIL: int
    DUPLICATE_NAME: int
    ACCESS_DENIED: int
    TIMEOUT: int
    BANNED: int
    ACCOUNT_NOT_FOUND: int
    INVALID_STEAM_ID: int
    SERVICE_UNAVAILABLE: int
    NOT_LOGGED_ON: int
    PENDING: int
    INSUFFICIENT_PRIVILEGE: int
    LIMIT_EXCEEDED: int
    REVOKED: int
    EXPIRED: int
    ALREADY_REDEEMED: int
    DUPLICATE_REQUEST: int
    ALREADY_OWNED: int
    IP_NOT_FOUND: int
    PERSIST_FAILED: int
    LOCKING_FAILED: int
    LOGON_SESSION_REPLACED: int
    CONNECT_FAILED: int
    HANDSHAKE_FAILED: int
    IO_FAILURE: int
    REMOTE_DISCONNECT: int
    SHOPPING_CART_NOT_FOUND: int
    BLOCKED: int
    IGNORED: int
    NO_MATCH: int
    ACCOUNT_DISABLED: int
    SERVICE_READ_ONLY: int
    ACCOUNT_NOT_FEATURED: int
    ADMINISTRATOR_OK: int
    CONTENT_VERSION: int
    TRY_ANOTHER_CM: int
    PASSWORD_REQUIRED_TO_KICK_SESSION: int
    ALREADY_LOGGED_IN_ELSEWHERE: int
    SUSPENDED: int
    CANCELLED: int
    DATA_CORRUPTION: int
    DISK_FULL: int
    REMOTE_CALL_FAILED: int
    PASSWORD_UNSET: int
    EXTERNAL_ACCOUNT_UNLINKED: int
    PSN_TICKET_INVALID: int
    EXTERNAL_ACCOUNT_ALREADY_LINKED: int
    REMOTE_FILE_CONFLICT: int
    ILLEGAL_PASSWORD: int
    SAME_AS_PREVIOUS_VALUE: int
    ACCOUNT_LOGON_DENIED: int
    CANNOT_USE_OLD_PASSWORD: int
    INVALID_LOGIN_AUTH_CODE: int
    ACCOUNT_LOGON_DENIED_NO_MAIL: int
    HARDWARE_NOT_CAPABLE_OF_IPT: int
    IPT_INIT_ERROR: int
    PARENTAL_CONTROL_RESTRICTED: int
    FACEBOOK_QUERY_ERROR: int
    EXPIRED_LOGIN_AUTHCODE: int
    IP_LOGIN_RESTRICTION_FAILED: int
    ACCOUNT_LOCKED_DOWN: int
    ACCOUNT_LOGON_DENIED_VERIFIED_EMAIL_REQUIRED: int
    NO_MATCHING_URL: int
    BAD_RESPONSE: int
    REQUIRE_PASSWORD_REENTRY: int
    VALUE_OUT_OF_RANGE: int
    UNEXPECTED_ERROR: int
    DISABLED: int
    INVALID_CEG_SUBMISSION: int
    RESTRICTED_DEVICE: int
    REGION_LOCKED: int
    RATE_LIMIT_EXCEEDED: int
    ACCOUNT_LOGIN_DENIED_NEED_TWO_FACTOR: int
    ITEM_DELETED: int
    ACCOUNT_LOGIN_DENIED_THROTTLE: int
    TWO_FACTOR_CODE_MISMATCH: int
    TWO_FACTOR_ACTIVATION_CODE_MISMATCH: int
    ACCOUNT_ASSOCIATED_TO_MULTIPLE_PARTNERS: int
    NOT_MODIFIED: int
    NO_MOBILE_DEVICE: int
    TIME_NOT_SYNCED: int
    SMS_CODE_FAILED: int
    ACCOUNT_LIMIT_EXCEEDED: int
    ACCOUNT_ACTIVITY_LIMIT_EXCEEDED: int
    PHONE_ACTIVITY_LIMIT_EXCEEDED: int
    REFUND_TO_WALLET: int
    EMAIL_SEND_FAILURE: int
    NOT_SETTLED: int
    NEED_CAPTCHA: int
    GSLT_DENIED: int
    GS_OWNER_DENIED: int
    INVALID_ITEM_TYPE: int
    IP_BANNED: int
    GSLT_EXPIRED: int
    INSUFFICIENT_FUNDS: int
    TOO_MANY_PENDING: int

class EItemState(IntFlag):
    NONE: int
    SUBSCRIBED: int
    LEGACY_ITEM: int
    INSTALLED: int
    NEEDS_UPDATE: int
    DOWNLOADING: int
    DOWNLOAD_PENDING: int

class ERemoteStoragePublishedFileVisibility(Enum):
    PUBLIC: int
    FRIENDS_ONLY: int
    PRIVATE: int

class ENotificationPosition(Enum):
    TOP_LEFT: int
    TOP_RIGHT: int
    BOTTOM_LEFT: int
    BOTTOM_RIGHT: int

class EGamepadTextInputLineMode(Enum):
    SINGLE_LINE: int
    MULTIPLE_LINES: int

class EGamepadTextInputMode(Enum):
    NORMAL: int
    PASSWORD: int

class EItemUpdateStatus(Enum):
    INVALID: int
    PREPARING_CONFIG: int
    PREPARING_CONTENT: int
    UPLOADING_CONTENT: int
    UPLOADING_PREVIEW_FILE: int
    COMMITTING_CHANGES: int
