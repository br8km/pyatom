"""Config Manager."""

from pathlib import Path
from dataclasses import dataclass, asdict

from pyatom.base.io import IO


DIR_DEBUG = Path(__file__).parent.parent / "debug"

DIR_DEBUG.mkdir(parents=True, exist_ok=True)

__all__ = (
    "Config",
    "ConfigManager",
    "DIR_DEBUG",
)


@dataclass
class Config:  # pylint: disable=too-many-instance-attributes
    """Config."""

    key_2captcha: str = ""
    smart_proxy_usr: str = ""
    smart_proxy_pwd: str = ""
    smart_proxy_check: str = ""
    yourls_domain: str = ""
    yourls_key: str = ""
    postfix_domain: str = ""
    postfix_port_imap: int = 0
    postfix_port_smtp: int = 0
    postfix_usr: str = ""
    postfix_pwd: str = ""
    postfix_ssl: bool = False
    twilio_sid: str = ""
    twilio_token: str = ""
    twilio_number: str = ""
    domdetailer_app: str = ""
    domdetailer_key: str = ""
    pixabay_key: str = ""
    user_agent: str = ""
    proxy_url: str = ""
    chrome_version: str = ""


class ConfigManager:
    """Config Manager."""

    @staticmethod
    def load(file_config: Path) -> Config:
        """Load config from local file."""
        data = IO.load_dict(file_config)
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
            proxy_url=data.get("proxy_url", ""),
            chrome_version=data.get("chrome_version", ""),
        )

    @staticmethod
    def save(config: Config, file_config: Path) -> bool:
        """Save config into local file."""
        data = asdict(config)
        IO.save_dict(file_name=file_config, file_data=data)
        return file_config.is_file()

    @staticmethod
    def new() -> Config:
        """Get new blank Config."""
        return Config()


class TestConfig:
    """Test Config."""

    dir_app = Path(__file__).parent

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    file_example = DIR_DEBUG.parent / "data" / "example.config.json"

    def test_config_manager(self) -> None:
        """Test ConfigManger."""
        app = ConfigManager()
        config = app.load(self.file_config)
        assert isinstance(config, Config)
        blank = app.new()
        app.save(config=blank, file_config=self.file_example)


if __name__ == "__main__":
    TestConfig()
