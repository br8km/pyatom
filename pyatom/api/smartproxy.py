"""
    SmartProxy.com Service API
"""

import threading
import time
from ipaddress import ip_address
from typing import Optional, Union

import orjson
import regex as re
from requests import Response, Session, RequestException

from pyatom.base.chars import str_rnd
from pyatom.base.log import Logger


__all__ = ("SmartProxy",)


class SmartProxy:
    """smartproxy.com API implemention"""

    __slots__ = (
        "__dict__",
        "usr",
        "pwd",
        "logger",
        "api",
        "check_url",
        "data",
        "addr",
        "proxy_str",
        "delay",
        "stop",
        "session",
    )

    def __init__(self, usr: str, pwd: str, check_url: str, logger: Logger) -> None:
        """Init."""
        self.usr = usr
        self.pwd = pwd
        self.check_url = check_url
        self.logger = logger

        self.api = "gate.smartproxy.com:7000"

        self.data: dict[str, Union[str, dict, int]] = {
            "id": "",
            "ifconfig": {},
            "teoh": {},
            "iphub": {},
        }
        self.addr = ""
        self.proxy_str = ""
        self.delay = 30
        self.stop = False

        self.session = Session()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0"
        headers = {"User-Agent": user_agent}
        self.session.headers.update(headers)

    def update(self, proxy_str: str) -> None:
        """Update requests.session with new proxy string."""
        self.proxy_str = proxy_str
        self.session.proxies = {
            "http": f"http://{proxy_str}",
            "https": f"http://{proxy_str}",
        }

    def rnd(self, country: str = "US") -> None:
        """Generate random proxy string for specific country."""
        proxy_str = f"user-{self.usr}-country-{country}:{self.pwd}@{self.api}"
        self.update(proxy_str)

    def sticky(self, country: str = "US", city: str = "") -> None:
        """Generate sticky proxy string for specific country and city."""
        session_id = str_rnd(number=6)
        prefix = f"user-{self.usr}-country-{country}"
        if city:
            prefix = f"{prefix}-city-{city}"
        proxy_str = f"{prefix}-session-{session_id}:{self.pwd}@{self.api}"
        self.update(proxy_str)

    def http_get(self, url: str, timeout: int = 30) -> Optional[Response]:
        """HTTP GET request"""
        try:
            resp = self.session.get(url, timeout=timeout)
            if resp:
                self.logger.info(f"<{resp.status_code}>[{len(resp.text)}] - {resp.url}")
            return resp
        except RequestException as err:
            self.logger.error(err)
        return None

    def check(self) -> bool:
        """check connection"""
        response = self.http_get(self.check_url)
        if response:
            pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
            found = pattern.findall(response.text)
            if found:
                self.addr = found[0]
                return True
        return False

    def parse(self, response: Optional[Response]) -> dict:
        """parse http response"""
        if isinstance(response, Response):
            try:
                data = orjson.loads(response.text)
                if isinstance(data, dict):
                    return data
            except orjson.JSONDecodeError as err:
                self.logger.error(err)
        return {}

    def ifconfig(self) -> bool:
        """
        check ifconfig data:
            ip, country, country_iso, time_zone, asn, asn_org, hostname, region_name,
            region_code, metro_code, zip_code, city, latitude, longitude, etc.
        """
        url = "https://ifconfig.co/json"
        response = self.http_get(url)
        data = self.parse(response)
        if isinstance(data, dict):
            self.data["ifconfig"] = data
            return True
        return False

    def teoh(self, addr: str) -> bool:
        """
        Error: Access denied  Error 1020 from Cloudflare
        check teoh.io data:
            ip, asn, organization, type, risk, is_hosting, vpn_or_proxy, etc.
        """
        if addr:
            url = f"https://ip.teoh.io/api/vpn/{addr}"
            response = self.http_get(url)
            data = self.parse(response)
            if isinstance(data, dict):
                self.data["teoh"] = data
                return True
        return False

    def iphub(self, addr: str) -> bool:
        """
        get iphub data:
            ip, countryCode, asn, isp, block, hostname, etc.
        block:
            <0>Residential or business IP (i.e. safe IP)
            <1>Non-residential IP (hosting provider, proxy, etc.)
            <2>Mixed ISP (hosting & residential) : Non-residential & residential IP (warning, may flag innocent people)
        """
        if addr:
            base = "https://v2.api.iphub.info/guest/ip/"
            url = f"{base}{addr}"
            response = self.http_get(url)
            data = self.parse(response)
            if isinstance(data, dict):
                self.data["iphub"] = data
                return True
        return False

    def valid(self, addr: str) -> bool:
        """validation for ip address"""
        try:
            ip_address(addr)
            return True
        except ValueError as err:
            self.logger.error(err)
        return False

    def heart_beat(self) -> None:
        """heart beat to stay alive"""
        self.stop = False
        while 1:
            time.sleep(self.delay)
            response = self.http_get(self.check_url)
            if isinstance(response, Response):
                msg = f"<heartbeat>[{response.status_code}]{response.url}"
                self.logger.info(msg)
            if self.stop:
                break

    def heart_beat_start(self) -> None:
        """heart beat start as thread"""
        thread_beat = threading.Thread(target=self.heart_beat, args=())
        thread_beat.start()

    def heart_beat_stop(self) -> None:
        """heart beat stop threading"""
        self.stop = True

    def get_proxy(
        self,
        country: str = "us",
        retry: int = 100,
    ) -> str:
        """get valid proxy string."""
        check_blocks = [0, 2]

        for _ in range(retry):
            # get new sticky proxy
            self.sticky(country=country)

            if not self.check():
                continue
            if not self.iphub(self.addr):
                continue
            if not isinstance(self.data["iphub"], dict):
                continue

            block = self.data["iphub"].get("block")
            self.logger.info(f"{block} - {check_blocks}")
            if block in check_blocks:
                self.logger.info(f"<GOOD>[block={block}]{self.addr}")
                return self.proxy_str

            self.logger.info(f"<BAD>[block={block}]{self.addr}")
        return ""
