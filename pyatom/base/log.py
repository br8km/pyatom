"""
    Init Logger cls
"""

from datetime import datetime, timezone, timedelta
from logging import (
    Logger,
    getLogger,
    Formatter,
    StreamHandler,
    FileHandler,
    LogRecord,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
)

from pathlib import Path
from typing import Union


__all__ = ("init_logger",)


class SmartFormatter(Formatter):
    """Override logging.Formatter.

    use an aware datetime object and
    use different format according to record.level.
    """

    datefmt = "%Y-%m-%d %H:%M:%S %Z"
    formats = {
        DEBUG: "%(asctime)s: %(levelname)s: %(module)s: %(lineno)d: %(message)s",
        INFO: "%(asctime)s: %(levelname)s: %(message)s",
        WARNING: "%(asctime)s: %(levelname)s %(message)s",
        ERROR: "%(asctime)s: %(levelname)s %(message)s",
        CRITICAL: "%(asctime)s: %(levelname)s %(message)s",
        "DEFAULT": "%(asctime)s:%(levelname)s:%(message)s",
    }

    def __init__(self, tz_offset: int) -> None:
        """Init Format."""
        super().__init__(None, self.datefmt, style="%", validate=True)

        self.fmt_orig = self.formats.get("DEFAULT", "")
        self.tz_offset = tz_offset

    def _converter(self, timestamp: float) -> datetime:
        """Add hours offset to utc timezone."""
        tz_info = timezone(timedelta(hours=self.tz_offset))
        return datetime.fromtimestamp(timestamp, tz=tz_info)

    def formatTime(self, record: LogRecord, datefmt: Union[str, None] = None) -> str:
        date_obj = self._converter(record.created)
        if datefmt:
            date_str = date_obj.strftime(datefmt)
        else:
            try:
                date_str = date_obj.isoformat(timespec="milliseconds")
            except TypeError:
                date_str = date_obj.isoformat()
        return date_str

    def format(self, record: LogRecord) -> str:
        """Set Customize format."""
        self._style._fmt = self.formats.get(  # pylint: disable=W0212
            record.levelno, self.fmt_orig
        )
        return Formatter.format(self, record)


def init_logger(
    name: str, stream: bool, file: Union[str, Path, None], tz_offset: int = 8
) -> Logger:
    """Init Logger."""

    if not stream and not file:
        raise ValueError("Require at least one handler: stream|file")

    logger = getLogger(name)
    logger.setLevel(DEBUG)

    formatter = SmartFormatter(tz_offset=tz_offset)

    if stream:
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if file:
        file_name = str(file.absolute()) if isinstance(file, Path) else file
        file_handler = FileHandler(filename=file_name, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
