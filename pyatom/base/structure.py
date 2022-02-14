"""
    General Data Structures
"""

from dataclasses import dataclass
from enum import IntEnum, unique

from datetime import datetime


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

    @property
    def valid(self) -> bool:
        """Validate birth attributes."""
        try:
            datetime(year=self.year, month=self.month, day=self.day)
            return True
        except ValueError:
            return False


@dataclass
class Phone:
    """Phone number for profile"""

    code: str
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
    country: str
    state: str
    city: str
    street: str
    postal: str
    coordinate: tuple[float, float]
    time_zone: str
    utc_offset: int


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
        """Check if account okay to posting"""
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
    error: str

    @property
    def success(self) -> bool:
        """Check if publish success."""
        return bool(self.url and not self.error)


@dataclass
class FingerPrint:
    """Finger Print for Browser."""

    user_agent: str


class TestStructure:
    """TestCase for Structures."""

    @staticmethod
    def test_birth() -> None:
        """Test birth cls."""
        birth = Birth(year=-1, month=12, day=12)
        assert birth.valid is False
        birth = Birth(year=1900, month=24, day=12)
        assert birth.valid is False
        birth = Birth(year=2000, month=10, day=55)
        assert birth.valid is False
        birth = Birth(year=2020, month=6, day=25)
        assert birth.valid is True

    @staticmethod
    def test_account() -> None:
        """Test account cls."""
        account = Account(
            aid="aid",
            user_agent="user_agent",
            proxy_str="proxy_str",
            email_user="email_user",
            email_pass="email_pass",
            username="username",
            password="password",
            cookies={},
            status=0,
            error="error",
        )
        assert account.okay is False
        account.status = Status.LOGIN
        assert account.okay is False
        account.error = ""
        assert account.okay is True

    @staticmethod
    def test_post() -> None:
        """Test post cls."""
        post = Post(
            pid="pid",
            title="title",
            content=["content"],
            hashtag=["hashtag"],
            attachment=["attachment"],
            timestamp=0,
            url="",
            error="error",
        )
        assert post.success is False
        post.url = "url"
        assert post.success is False
        post.error = ""
        assert post.success is True


if __name__ == "__main__":
    app = TestStructure()
