"""Config Manager."""

from pathlib import Path
from dataclasses import dataclass, asdict

from pyatom.base.io import load_dict, save_dict


__all__ = (
    "Config",
    "ConfigManager",
)


@dataclass
class Config:
    """Config."""

    key_2captcha: str
    smart_proxy_usr: str
    smart_proxy_pwd: str
    smart_proxy_check: str
    yourls_domain: str
    yourls_key: str
    postfix_domain: str
    postfix_port_imap: int
    postfix_port_smtp: int
    postfix_usr: str
    postfix_pwd: str
    postfix_ssl: bool
    twilio_sid: str
    twilio_token: str
    twilio_number: str
    domdetailer_app: str
    domdetailer_key: str
    pixabay_key: str
    user_agent: str
    proxy_str: str


class ConfigManager:
    """Config Manager."""

    def __init__(self, file_config: Path) -> None:
        """Init ConfigManager."""
        self.file_config = file_config

    def load(self) -> Config:
        """Load config from local file."""
        data = load_dict(self.file_config)
        return Config(
            key_2captcha=data.get("key_2captcha", ""),
            smart_proxy_usr=data.get("smart_proxy_usr", ""),
            smart_proxy_pwd=data.get("smart_proxy_pwd", ""),
            smart_proxy_check=data.get("smart_proxy_check", ""),
            yourls_domain=data.get("yourls_domain", ""),
            yourls_key=data.get("yourls_key", ""),
            postfix_domain=data.get("postfix_domain", ""),
            postfix_port_imap=data.get("postfix_port_imap", 0),
            postfix_port_smtp=data.get("postfix_port_smtp", 0),
            postfix_usr=data.get("postfix_usr", ""),
            postfix_pwd=data.get("postfix_pwd", ""),
            postfix_ssl=data.get("postfix_ssl", False),
            twilio_sid=data.get("twilio_sid", ""),
            twilio_token=data.get("twilio_token", ""),
            twilio_number=data.get("twilio_number", ""),
            domdetailer_app=data.get("domdetailer_app", ""),
            domdetailer_key=data.get("domdetailer_key", ""),
            pixabay_key=data.get("pixabay_key", ""),
            user_agent=data.get("user_agent", ""),
            proxy_str=data.get("proxy_str", ""),
        )

    def save(self, config: Config) -> bool:
        """Save config into local file."""
        data = asdict(config)
        save_dict(file_name=self.file_config, file_data=data)
        return self.file_config.is_file()
