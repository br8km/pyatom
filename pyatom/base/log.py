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
from typing import Optional

from pytest import LogCaptureFixture


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

    def formatTime(self, record: LogRecord, datefmt: Optional[str] = None) -> str:
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
    name: str,
    level: int = DEBUG,
    file: Optional[Path] = None,
    stream: bool = False,
    tz_offset: int = 8,
) -> Logger:
    """Init Logger."""

    logger = getLogger(name)
    logger.setLevel(level)

    formatter = SmartFormatter(tz_offset=tz_offset)

    if file:
        file_name = str(file.absolute())
        file_handler = FileHandler(filename=file_name, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        if not stream:
            # Only file handler
            return logger

    # With stream handler
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


class TestLogger:
    """Testcase for logger."""

    name = "test"
    flag = "hello world"

    def test_logger(self, caplog: LogCaptureFixture) -> None:
        """Test logger method."""
        logger = init_logger(name=self.name)
        logger.info(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == INFO

        logger.debug(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == DEBUG

        logger.error(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == ERROR

        logger.warning(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == WARNING

        logger.critical(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == CRITICAL

    def test_logger_file(self, caplog: LogCaptureFixture) -> None:
        """Test logger file."""
        file_temp = Path(Path(__file__).parent, self.name + ".log")
        logger = init_logger(name=self.name, file=file_temp)

        logger.info(self.flag)
        record = caplog.records[-1]
        assert self.flag == record.message
        assert record.levelno == INFO

        logger.handlers = []
        file_temp.unlink(missing_ok=True)


if __name__ == "__main__":
    app = TestLogger()
