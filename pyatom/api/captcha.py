"""
    Captcha Resolver Service, eg: 2captcha.com service api
"""

import time
import base64
from urllib.parse import urlencode

import requests

from pyatom.base.log import Logger


__all__ = ("TwoCaptcha",)


class TwoCaptcha:
    """2captcha.com API implemention"""

    __slots__ = ("__dict__", "demo", "logger", "key", "base", "param")

    def __init__(self, api_key: str, logger: Logger) -> None:
        """Init 2captcha.com api wrapper."""
        self.key = api_key
        self.logger = logger
        self.base = "http://2captcha.com/"

    def balance(self) -> float:
        """get account balance"""
        param = {"key": self.key, "action": "getbalance", "json": 1}
        url = f"{self.base}res.php?{urlencode(param)}"
        with requests.get(url, timeout=30) as response:
            data = response.json()
            if data.get("status") == 1:
                return float(data.get("request"))
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
                self.logger.debug("[{}]solving recaptcha...".format(i))

                j = 12
                while j and answer:
                    if "OK" in answer:
                        return answer.split("|")[1]

                    if "ERROR_CAPTCHA_UNSOLVABLE" in answer:
                        self.logger.debug("ERROR_CAPTCHA_UNSOLVABLE")
                        return ""

                    if "CAPCHA_NOT_READY" in answer:
                        self.logger.debug("[{}]{}".format(j, answer))
                        time.sleep(10)
                        answer = requests.get(url2).text
                    j = j - 1
            except requests.exceptions.RequestException as err:
                self.logger.error(err)
        return ""

    def normal(
        self,
        raw_image: bytes,
        method: str = "base64",
        retry: int = 3,
    ) -> str:
        """
        Normal image captcha solver;
        """
        payload = {
            "key": self.key,
            "method": method,
            "body": base64.b64encode(raw_image),
        }
        url = f"{self.base}in.php"

        for i in range(retry):
            try:
                response = requests.post(url, data=payload)
                self.logger.info(
                    f"<{response.status_code}>[{len(response.text)}]- {response.url}"
                )
                cid = response.text.split("|")[1]
                param2 = {"key": self.key, "action": "get", "id": cid}
                url2 = f"{self.base}res.php?{urlencode(param2)}"
                response = requests.get(url2)
                self.logger.info(
                    f"<{response.status_code}>[{len(response.text)}]- {response.url}"
                )
                answer = response.text
                self.logger.debug("[{}]solving normal captcha...".format(i))

                j = 12
                while j and answer:
                    if "OK" in answer:
                        return answer.split("|")[1]

                    if "ERROR_CAPTCHA_UNSOLVABLE" in answer:
                        self.logger.debug("ERROR_CAPTCHA_UNSOLVABLE")
                        return ""

                    if "CAPCHA_NOT_READY" in answer:
                        self.logger.debug("[{}]{}".format(j, answer))
                        time.sleep(10)
                        answer = requests.get(url2).text
                    j = j - 1
            except requests.exceptions.RequestException as err:
                self.logger.error(err)
        return ""
