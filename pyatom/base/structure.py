"""
    General Data Structures
"""

from dataclasses import dataclass
from enum import IntEnum, unique


__all__ = (
    "Name",
    "Birth",
    "Phone",
    "Avatar",
    "Biography",
    "Address",
    "Status",
    "Account",
    "Post",
)


@dataclass
class Name:
    """Name for profile"""

    first: str
    last: str
    middle: str


@dataclass
class Birth:
    """Day of birth for profile"""

    year: int
    month: int
    day: int


@dataclass
class Phone:
    """Phone number for profile"""

    code: int
    number: str
    mobile: bool


@dataclass
class Avatar:
    """Avatar for profile"""

    file: str
    url: str


@dataclass
class Biography:
    """Biography for profile"""

    about: str
    motto: str


@dataclass
class Address:
    """Address for profile"""

    ipaddr: str
    tz_offset: int
    country: str
    state: str
    city: str
    street: str
    zip: str
    coordinate: tuple[int, int]


@unique
class Status(IntEnum):
    """Status of account."""

    UNKNOWN = 0  # unknown
    VISITOR = 1  # not registered
    USER = 2  # registered
    PASSWORD = 3  # password set
    CONFIRM = 4  # email confirmed
    LOGIN = 5  # logged in
    LIMITED = 6  # rate limited
    BANNED = 7  # banned for some reason


@dataclass
class Account:
    """Account data."""

    aid: str
    user_agent: str
    proxy_str: str
    email_user: str
    email_pass: str
    username: str
    password: str
    cookies: dict
    status: int
    error: str

    @property
    def okay(self) -> bool:
        """Check if okay to posting"""
        return bool(self.status == Status.LOGIN and not self.error)


@dataclass
class Post:
    """Post has been published."""

    pid: str
    title: str
    content: list[str]
    hashtag: list[str]
    attachment: list[str]
    timestamp: int

    url: str
    code: str
    error: str

    @property
    def success(self) -> bool:
        """Check if publish success."""
        return bool(self.url and not self.error)


@dataclass
class FingerPrint:
    """Finger Print for Browser."""

    user_agent: str
