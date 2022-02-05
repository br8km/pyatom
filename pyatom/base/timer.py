"""
    Time Transformation
"""

import random
import time
from typing import Optional


import arrow
from arrow import Arrow


__all__ = (
    "smart_delay",
    "Timer",
)


def smart_delay(seconds: float, demo: bool = False) -> float:
    """Smart delay for seconds of time"""
    small, big = float(seconds * 4 / 5), float(seconds * 6 / 5)
    pause = random.uniform(small, big)
    if not demo:
        time.sleep(pause)
    return pause


class Timer:
    """Base cls for time transformation"""

    __slots__ = ("__dict__", "tz_offset", "now", "fmt")

    def __init__(self, tz_offset: int = 0) -> None:
        self.tz_offset = tz_offset
        self.now = arrow.now().shift(hours=tz_offset)
        self.fmt = "YYYY-MM-DD HH:mm:ss"

    def to_str(self, now: Optional[Arrow] = None, fmt: str = "") -> str:
        """string format for now"""
        fmt = fmt if fmt else self.fmt
        now = now if now else self.now
        return now.format(fmt)

    def to_timestamp(self, now: Optional[Arrow] = None) -> int:
        """int timestamp for now"""
        now = now if now else self.now
        return int(now.timestamp())

    def ts2str(self, now_ts: int, fmt: str = "") -> str:
        """int to string for timestamp of now"""
        fmt = fmt if fmt else self.fmt
        return arrow.get(now_ts).format(fmt)

    def str2ts(self, now_str: str, fmt: str = "") -> int:
        """string to int for timestamp of now"""
        fmt = fmt if fmt else self.fmt
        return int(arrow.get(now_str, fmt).timestamp())

    def iso_week(self, offset: int = 0) -> str:
        """return ISO week format like: `2020W36`"""
        iso = self.now.shift(weeks=offset).isocalendar()
        return "{}W{}".format(iso[0], iso[1])
