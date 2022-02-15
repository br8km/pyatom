"""
    Send Notification Message.
"""

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import pytest
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from pyatom.base.chars import str_rnd
from pyatom.base.io import dir_create, file_del, save_str
from pyatom.base.log import Logger, init_logger
from pyatom.client.smtp import MailSender
from pyatom.config import ConfigManager


__all__ = (
    "Notice",
    "PostfixSender",
    "TwilioSender",
)


@dataclass
class Notice:
    """Notice message."""

    nid: str

    title: str
    content: str
    files: list[str]
    urgency: int

    sender: str
    sender_id: str
    timestamp: int

    @property
    def success(self) -> bool:
        """Validate if send success."""
        return bool(self.nid and self.sender_id)


class BaseSender:
    """Base cls for notify sender."""

    def __init__(self, sender: str, logger: Logger, dir_bak: Path) -> None:
        """Init base sender."""
        self.sender = sender
        self.logger = logger

        self.dir_bak = dir_bak
        dir_create(self.dir_bak)

    @staticmethod
    def file_str(file_path: Path) -> str:
        """Parse file path full string."""
        return str(file_path.absolute())

    def _create_notice(
        self, title: str, content: str, files: list[str], urgency: int
    ) -> Notice:
        """Create new notice."""
        return Notice(
            nid=str_rnd(6),
            title=title,
            content=content,
            files=files,
            urgency=urgency,
            sender=self.sender,
            sender_id="",
            timestamp=int(time.time()),
        )

    @staticmethod
    def to_subject(notice: Notice) -> str:
        """Generate subject string for notice object."""
        return f"[NOTICE]<{notice.urgency}>{notice.title}"

    @staticmethod
    def to_body(notice: Notice) -> str:
        """Generate body string for notice object."""
        subject = f"[NOTICE]<{notice.urgency}>{notice.title}"
        return f"{subject}\n\n{notice.content}\n\nFrom:{notice.sender}\nTimestamp:{notice.timestamp}"

    def save_notice(self, notice: Notice) -> bool:
        """Save notice object into local file."""
        line_break = "\n" + "-" * 30 + "\n"
        file_notice = Path(self.dir_bak, f"{self.sender}.json.txt")
        with open(file_notice, "a") as file:
            file.write(json.dumps(asdict(notice), indent=2) + line_break)
        return file_notice.is_file()

    def clean_notice(self) -> bool:
        """Clear all notice from local file storage."""
        file_notice = Path(self.dir_bak, f"{self.sender}.json.txt")
        file_notice.unlink(missing_ok=True)
        return file_notice.is_file() is False


class PostfixSender(BaseSender):
    """Postfix Email Notify Sender."""

    def __init__(
        self,
        host: str,
        port: int,
        usr: str,
        pwd: str,
        ssl: bool,
        logger: Logger,
        dir_bak: Path,
    ) -> None:
        """Init postfix sender."""
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd
        self.ssl = ssl
        self.logger = logger

        super().__init__(
            sender=f"Postfix.Sender <{self.host}>", logger=logger, dir_bak=dir_bak
        )

        self.client = MailSender(
            host=self.host, port=self.port, usr=self.usr, pwd=self.pwd, use_ssl=ssl
        )

    def create_notice(
        self, title: str, content: str, files: list[str], urgency: int = 0
    ) -> Notice:
        """Create notice for postfix."""
        return self._create_notice(
            title=title,
            content=content,
            files=files,
            urgency=urgency,
        )

    def send(self, notice: Notice, email_to: str, save: bool = True) -> bool:
        """Send notice from postfix."""
        sender_name = "Notify"
        sender_email = f"notify@{self.host}"

        try:
            subject = self.to_subject(notice=notice)
            body = self.to_body(notice=notice)
            body_html = body.replace("\n", "<br />")

            html_text = ""
            if notice.files:
                html_text = f"<html><head><title>{subject}</title></head><body><div align='center'>{body_html}</div></body></html>"

            self.client.set_message(
                plain_text=body,
                html_text=html_text,
                subject=subject,
                sender_email=sender_email,
                sender_name=sender_name,
                recipient=email_to,
                list_attachment=[Path(fp) for fp in notice.files],
                id_seed=notice.nid,
            )
            self.client.connect()
            self.client.send(recipient=email_to)

            notice.sender_id = self.client.msg["Message-ID"]
        except ConnectionError as err:
            self.logger.error(err)

        if save:
            self.save_notice(notice=notice)

        return notice.success


class TwilioSender(BaseSender):
    """Twilio Notify Sender.

    Not Aavilable at 2022-01-29. not SMS-capable phone number.
    """

    def __init__(
        self, sid: str, token: str, number: str, logger: Logger, dir_bak: Path
    ) -> None:
        """Init twilio sender."""
        self.sid = sid
        self.token = token
        self.number = number

        self.sender = f"Twilio.Sender <{self.number}>"

        super().__init__(
            sender=f"Twilio.Sender <{self.number}>", logger=logger, dir_bak=dir_bak
        )

        self.client = Client(username=self.sid, password=self.token)

    def create_notice(
        self, title: str, content: str, files: list[str], urgency: int = 0
    ) -> Notice:
        """Create notice for twilio."""
        return self._create_notice(
            title=title,
            content=content,
            files=files,
            urgency=urgency,
        )

    def send(self, notice: Notice, number_to: str, save: bool = True) -> bool:
        """Send sms notice from twilio.

        parameter:number_to: string of number send to. format: +1 23456789
        """
        try:
            message = self.client.messages.create(
                to=number_to, from_=self.number, body=self.to_body(notice=notice)
            )
            if message:
                notice.sender_id = str(message.sid)

            self.logger.info(
                f"<{notice.success}>twilio send: {notice.sender_id} notice.id={notice.nid}"
            )
        except TwilioRestException as err:
            self.logger.error(err)

        if save:
            self.save_notice(notice=notice)

        return notice.success


class TestNotify:
    """TestCase for Notify."""

    dir_app = Path(__file__).parent
    file_config = Path(dir_app.parent.parent, "protect", "config.json")
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")
    file_temp = Path(dir_app, "temp.file")

    def create_temp_file(self) -> bool:
        """Create temp file as attachment."""
        number = 100
        text = " ".join(str_rnd() for _ in range(number))
        save_str(file_name=self.file_temp, file_content=text)
        return self.file_temp.is_file()

    @pytest.mark.skip(reason="tested okay.")
    def test_postfix_sender(self) -> None:
        """Test postfix sender."""
        assert self.create_temp_file()
        postfix = PostfixSender(
            host=self.config.postfix_domain,
            port=self.config.postfix_port_smtp,
            usr=self.config.postfix_usr,
            pwd=self.config.postfix_pwd,
            ssl=self.config.postfix_ssl,
            logger=self.logger,
            dir_bak=self.dir_app,
        )
        files = [postfix.file_str(self.file_temp)]
        notice = postfix.create_notice(
            title="", content="content", files=files, urgency=0
        )
        email_to = "friend@" + self.config.postfix_domain
        assert postfix.send(notice, email_to=email_to, save=True)
        file_del(self.file_temp)
        assert self.file_temp.is_file() is False

        assert postfix.clean_notice() is True

    @pytest.mark.skip(reason="currently sms number not available.")
    def test_twilio_sender(self) -> None:
        """Test Twilio sender."""
        assert self.create_temp_file()
        twilio = TwilioSender(
            sid=self.config.twilio_sid,
            token=self.config.twilio_token,
            number=self.config.twilio_number,
            logger=self.logger,
            dir_bak=self.dir_app,
        )
        files = [twilio.file_str(self.file_temp)]
        notice = twilio.create_notice(
            title="", content="content", files=files, urgency=0
        )
        number_to = "+8613900006666"
        assert twilio.send(notice, number_to=number_to, save=True)
        file_del(self.file_temp)
        assert self.file_temp.is_file() is False

        assert twilio.clean_notice() is True


if __name__ == "__main__":
    TestNotify()
