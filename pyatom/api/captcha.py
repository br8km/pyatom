"""
    Captcha Resolver Service, eg: 2captcha.com service api
"""

import time
import base64
from pathlib import Path
from abc import ABC, abstractmethod
from urllib.parse import urlencode

import requests

from pyatom.base.log import Logger, init_logger
from pyatom.config import ConfigManager


__all__ = ("TwoCaptcha",)


class AbsCaptcha(ABC):
    """Abstract cls for Captcha API Wrappers."""

    def __init__(self, api_name: str, api_key: str, logger: Logger) -> None:
        """Init."""
        self.name = api_name
        self.key = api_key
        self.logger = logger

    @abstractmethod
    def balance(self) -> float:
        """Get account balance."""
        return 0.0

    @abstractmethod
    def recaptcha(self, site_key: str, page_url: str, retry: int = 3) -> str:
        """Get Google ReCaptcha Response string."""
        return ""

    @abstractmethod
    def captcha(self, raw_image: bytes, retry: int = 3) -> str:
        """Get verification code string for raw image bytes."""
        return ""


class TwoCaptcha(AbsCaptcha):
    """2captcha.com API implemention"""

    __slots__ = (
        "name",
        "key",
        "logger",
        "base",
    )

    def __init__(
        self, api_key: str, logger: Logger, api_name: str = "2captcha"
    ) -> None:
        """Init 2captcha.com api wrapper."""
        super().__init__(api_key=api_key, api_name=api_name, logger=logger)

        self.base = "http://2captcha.com/"

    def balance(self) -> float:
        """get account balance"""
        param = {"key": self.key, "action": "getbalance", "json": 1}
        url = f"{self.base}res.php?{urlencode(param)}"
        with requests.get(url, timeout=30) as response:
            if response and response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:
                    return float(data.get("request", -1))
        return -1

    def recaptcha(self, site_key: str, page_url: str, retry: int = 3) -> str:
        """
        sitekey: for google recaptcha on domain like DISCORD.COM
        discord: "6Lef5iQTAAAAAKeIvIY-DeexoO3gj7ryl9rLMEnn"
        """
        param = {
            "key": self.key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
        }
        url = f"{self.base}in.php?{urlencode(param)}"
        for i in range(retry):
            try:
                res = requests.get(url)
                cid = res.text.split("|")[1]
                param2 = {"key": self.key, "action": "get", "id": cid}
                url2 = f"{self.base}res.php?{urlencode(param2)}"
                answer = requests.get(url2).text
                self.logger.info("[{%d}]solving recaptcha...", i)

                j = 12
                while j and answer:
                    if "OK" in answer:
                        return answer.split("|")[1]

                    if "ERROR_CAPTCHA_UNSOLVABLE" in answer:
                        self.logger.error("ERROR_CAPTCHA_UNSOLVABLE")
                        return ""

                    if "CAPCHA_NOT_READY" in answer:
                        self.logger.debug("[%d]%s", i, answer)
                        time.sleep(10)
                        answer = requests.get(url2).text
                    j = j - 1
            except requests.RequestException as err:
                self.logger.exception(err)
        return ""

    def captcha(self, raw_image: bytes, retry: int = 3) -> str:
        """Normal image captcha solver;"""
        payload = {
            "key": self.key,
            "method": "base64",
            "body": base64.b64encode(raw_image),
        }
        url = f"{self.base}in.php"

        for i in range(retry):
            try:
                response = requests.post(url, data=payload)
                self.logger.debug(
                    "<%d>[%d]%s",
                    response.status_code,
                    len(response.text),
                    response.url,
                )
                cid = response.text.split("|")[1]
                param2 = {"key": self.key, "action": "get", "id": cid}
                url2 = f"{self.base}res.php?{urlencode(param2)}"
                response = requests.get(url2)
                self.logger.debug(
                    "<%d>[%d]%s",
                    response.status_code,
                    len(response.text),
                    response.url,
                )
                answer = response.text
                self.logger.info("[%d]solving normal captcha...", i)

                j = 12
                while j and answer:
                    if "OK" in answer:
                        return answer.split("|")[1]

                    if "ERROR_CAPTCHA_UNSOLVABLE" in answer:
                        self.logger.error("ERROR_CAPTCHA_UNSOLVABLE")
                        return ""

                    if "CAPCHA_NOT_READY" in answer:
                        self.logger.debug("[%d]%s", j, answer)
                        time.sleep(10)
                        answer = requests.get(url2).text
                    j = j - 1
            except requests.RequestException as err:
                self.logger.exception(err)
        return ""


class TestCaptcha:
    """Test Captcha APIs."""

    dir_app = Path(__file__).parent
    file_config = Path(dir_app.parent.parent, "protect", "config.json")
    config = ConfigManager(file_config).load()

    logger = init_logger(name="test")

    @staticmethod
    def _recaptcha(app: AbsCaptcha, number: int = 10) -> bool:
        """test twocaptcha google recaptcha solving"""
        page_url = "https://www.google.com/recaptcha/api2/demo"
        site_key = "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
        return any(
            app.recaptcha(site_key=site_key, page_url=page_url) != ""
            for _ in range(number)
        )

    @staticmethod
    def _captcha(app: AbsCaptcha, number: int = 10) -> bool:
        """test twocaptcha mormal image captcha solving"""
        page_url = "https://www.phpcaptcha.org/securimage/securimage_show.php?namespace=captcha_one"
        for _ in range(number):
            with requests.get(page_url, stream=True, timeout=30) as response:
                if response and response.status_code == 200:
                    if app.captcha(raw_image=response.content) != "":
                        return True
        return False

    def test_twocaptcha(self) -> None:
        """Test 2captcha.com api wrapper."""
        app = TwoCaptcha(api_key=self.config.key_2captcha, logger=self.logger)
        assert app.balance() > 0

        assert self._recaptcha(app=app)
        assert self._captcha(app=app)

    def test_other(self) -> None:
        """Test other capter solver."""
        assert self is not None


if __name__ == "__main__":
    TestCaptcha()
