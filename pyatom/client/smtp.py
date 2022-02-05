"""SMTP Mail Sender."""

import smtplib
from pathlib import Path
from typing import Union

from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from email import encoders


class MailSender:
    """Sender email via SMTP."""

    def __init__(
        self, host: str, port: int, usr: str, pwd: str, use_ssl: bool = False
    ) -> None:
        """Init SMTP Mail Sender."""
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd
        self.use_ssl = use_ssl

        self.connected = False
        self.smtpserver: Union[SMTP, SMTP_SSL]
        if self.use_ssl:
            self.smtpserver = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.smtpserver = smtplib.SMTP(self.host, self.port)

        self.html_ready = False
        self.msg: Union[MIMEMultipart, MIMEText]

    def set_message(
        self,
        plain_text: str,
        html_text: str,
        subject: str,
        sender_email: str,
        sender_name: str,
        recipient: str,
        list_attachment: list[Path],
        id_seed: str,
    ) -> None:
        """Create the MIME message to be sent by e-mail. Optionally allows adding subject and 'from' field. Sets up empty recipient fields. To use html messages specify an htmltext input."""
        if html_text:
            self.html_ready = True
            self.msg = MIMEMultipart("alternative")
            # 'alternative' allows attaching an html version message later

            for attachment in list_attachment:
                part = MIMEBase("application", "octet-stream")
                with open(attachment, "rb") as file:
                    part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", "attachment; filename=" + attachment.name
                )
                self.msg.attach(part)
            self.msg.attach(MIMEText(plain_text, "plain"))
            self.msg.attach(MIMEText(html_text, "html"))

        else:
            self.msg = MIMEText(plain_text, "plain")

        self.msg["Subject"] = subject
        self.msg["From"] = f"{sender_name} <{sender_email}>"
        self.msg["To"] = recipient
        self.msg["Message-ID"] = make_msgid(idstring=id_seed, domain=self.host)

    def set_id(self, id_seed: str) -> None:
        """Set Email Subject."""
        self.msg["Message-ID"] = make_msgid(idstring=id_seed, domain=self.host)

    def clear_message(self) -> None:
        """Remove the whole email body. If both plaintext and html are attached both are removed."""
        self.msg.set_payload("")

    def set_subject(self, email_subject: str) -> None:
        """Set Email Subject."""
        self.msg.replace_header("Subject", email_subject)

    def set_from(self, sender_name: str, sender_email: str) -> None:
        """Set Email From."""
        self.msg.replace_header("From", f"{sender_name} <{sender_email}>")

    def set_plaintext(self, email_text: str) -> None:
        """
        Set plaintext message: replaces entire payload if no html is used, otherwise replaces the plaintext only.

        :param body_text: Plaintext email body, replaces old plaintext email body
        """
        if not self.html_ready:
            self.msg.set_payload(email_text)
        else:
            payload = self.msg.get_payload()
            payload[0] = MIMEText(email_text)
            self.msg.set_payload(payload)

    def set_html(self, email_html: str) -> None:
        """
        Replace HTML version of the email body. The plaintext version is unaffected.

        :param email_html: HTML email body, replaces old HTML email body
        """
        try:
            payload = self.msg.get_payload()
            payload[1] = MIMEText(email_html, "html")
            self.msg.set_payload(payload)
        except TypeError:
            print(
                "ERROR: "
                "Payload is not a list. Specify an HTML message with email_htmltext in MailSender.set_message()"
            )
            raise

    def connect(self) -> None:
        """Connect to SMTP server using the username and password. Must be called before sending messages."""
        if not self.use_ssl:
            self.smtpserver.starttls()

        self.smtpserver.login(self.usr, self.pwd)
        self.connected = True

    def disconnect(self) -> None:
        """Disconnect from smtp server."""
        self.smtpserver.close()
        self.connected = False

    def send(self, recipient: str = "") -> None:
        """Send message to one specific recipient."""
        if not self.connected:
            raise ConnectionError(
                "Not connected to any server. Try self.connect() first"
            )
        if recipient:
            self.msg.replace_header("To", recipient)

        self.smtpserver.send_message(self.msg)
        self.disconnect()

    def send_all(self, recipients: list[str]) -> None:
        """Send message to all specified recipients, one at a time.

        Optionally closes connection after sending. Close the connection after sending if you are not sending another batch of emails immediately after.

        :param close_connection: Should the connection to the server be closed after all emails have been sent (True) or not (False)
        """
        if not self.connected:
            raise ConnectionError(
                "Not connected to any server. Try self.connect() first"
            )

        #  print("Message: {}".format(self.msg.get_payload()))

        for recipient in recipients:
            self.msg.replace_header("To", recipient)
            print("Sending to {}".format(recipient))
            self.smtpserver.send_message(self.msg)

        #  print("All messages sent")

        self.disconnect()
        #  print("Connection closed")
