"""
    Send requests to Ping Services.
    TODO: Add HTTP Post Pinger
"""

import random
import time
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass, asdict
from typing import Union, Tuple, Dict, Any
from http.client import HTTPConnection, HTTPSConnection
from xmlrpc.client import (
    Transport,
    SafeTransport,
    ServerProxy,
    ProtocolError,
    ResponseError,
    Fault,
)
from xml.parsers.expat import ExpatError

from tldextract import extract

from pyatom.base.io import IO
from pyatom.base.log import Logger, init_logger
from pyatom.base.proxy import Proxy
from pyatom.config import ConfigManager
from pyatom import DIR_DEBUG


__all__ = (
    "Service",
    "XMLPinger",
)


@dataclass
class Service:
    """XML-RPC Ping Service."""

    url: str
    geo: str
    alive: bool
    timestamp: int
    error: str


class HTTPProxyTransport(Transport):
    """HTTP Proxy Transport."""

    def __init__(self, user_agent: str, proxy_url: str, time_out: int):
        """Init."""
        Transport.__init__(self)

        self.user_agent = user_agent
        self.proxy = Proxy.load(url=proxy_url)
        key, value = self.proxy.auth
        self.proxy_headers = {key: value}
        self.timeout = time_out

    def make_connection(
        self, host: Union[Tuple[str, Dict[str, str]], str]
    ) -> HTTPConnection:
        """Make Connection."""
        connection = HTTPConnection(self.proxy.addr, self.proxy.port)
        connection.timeout = self.timeout
        connection.set_tunnel(str(host), headers=self.proxy_headers)
        self._connection = host, connection
        return connection


class HTTPSProxyTransport(SafeTransport):
    """HTTPS Proxy Transport."""

    def __init__(self, user_agent: str, proxy_url: str, time_out: int):
        """Init."""
        SafeTransport.__init__(self)

        self.user_agent = user_agent
        self.proxy = Proxy.load(url=proxy_url)
        key, value = self.proxy.auth
        self.proxy_headers = {key: value}
        self.timeout = time_out

    def make_connection(
        self, host: Union[Tuple[str, Dict[str, str]], str]
    ) -> HTTPSConnection:
        """Make Connection."""
        connection = HTTPSConnection(self.proxy.addr, self.proxy.port)
        connection.timeout = self.timeout
        connection.set_tunnel(str(host), headers=self.proxy_headers)
        self._connection = host, connection
        return connection


class BasePinger:
    """Base Pinger."""

    def __init__(self, list_ua: list[str], list_px: list[str]) -> None:
        """Init Base Pinger."""
        self.list_ua = list_ua
        self.list_px = list_px

    @property
    def rnd_ua(self) -> str:
        """Get random user_agent string."""
        return random.choice(self.list_ua)

    @property
    def rnd_px(self) -> str:
        """Get random proxy_url string."""
        return random.choice(self.list_px)

    @staticmethod
    def normalize(url: str) -> str:
        """Normalize url string."""
        out = urlparse(url)
        if out.scheme not in ("http", "https"):
            return ""
        return url[:-1] if url.endswith("/") else url

    @staticmethod
    def load_services(file_service: Path) -> list[Service]:
        """Load list of Service from local file."""
        service_data = IO.load_list_dict(file_service)
        return [
            Service(
                url=item.get("url") or "",
                geo=item.get("geo") or "",
                alive=item.get("alive") or False,
                timestamp=item.get("timestamp") or 0,
                error=item.get("error") or "",
            )
            for item in service_data
        ]

    @staticmethod
    def save_services(file_service: Path, list_service: list[Service]) -> bool:
        """Save list of Service into local file."""
        service_data = [asdict(service) for service in list_service]
        IO.save_list_dict(file_name=file_service, file_data=service_data)
        return file_service.is_file()

    @staticmethod
    def to_geo(url: str) -> str:
        """Get url domain geo string."""
        out = extract(url)
        return str(out.suffix)

    def to_service(self, url: str) -> Service:
        """Get Service from url."""
        return Service(
            url=url,
            geo=self.to_geo(url),
            alive=False,
            timestamp=int(time.time()),
            error="",
        )


class XMLPinger(BasePinger):
    """XML-RPC Pinger for ping services."""

    __slots__ = (
        "list_ua",
        "list_px",
        "logger",
        "time_out",
    )

    def __init__(
        self, list_ua: list[str], list_px: list[str], logger: Logger, time_out: int = 30
    ) -> None:
        """Init XML RPC Pinger."""
        super().__init__(list_ua=list_ua, list_px=list_px)

        self.logger = logger
        self.time_out = time_out

    def to_client(self, service_url: str) -> ServerProxy:
        """Generate ServerProxy client."""
        if service_url.startswith("https"):
            return ServerProxy(
                service_url,
                transport=HTTPSProxyTransport(
                    user_agent=self.rnd_ua,
                    proxy_url=self.rnd_px,
                    time_out=self.time_out,
                ),
            )
        return ServerProxy(
            service_url,
            transport=HTTPProxyTransport(
                user_agent=self.rnd_ua,
                proxy_url=self.rnd_px,
                time_out=self.time_out,
            ),
        )

    def basic_ping(self, client: ServerProxy, site_name: str, home_url: str) -> Any:
        """weblogUpdates.ping method."""
        try:
            return client.weblogUpdates.ping(site_name, home_url)
        except (ProtocolError, ResponseError, Fault, OSError, ExpatError) as err:
            self.logger.error(err)
            return err

    def extended_ping(
        self,
        client: ServerProxy,
        site_name: str,
        home_url: str,
        post_url: str = "",
    ) -> Any:
        """weblogUpdates.extendedPing method."""
        try:
            return client.weblogUpdates.extendedPing(site_name, home_url, post_url)
        except (ProtocolError, ResponseError, Fault, OSError, ExpatError) as err:
            self.logger.error(err)
            return err

    def parse_respnose(self, response: Any) -> tuple[bool, str]:
        """Parse ping response result into tuple of (success, response_str)."""
        response_str = str(response)

        if isinstance(response, Exception):
            self.logger.error(response_str)
            return False, response_str

        if not response or not isinstance(response, dict):
            return False, response_str

        if response.get("flerror", True):
            self.logger.error(response.get("message"))
            return False, response_str

        return True, response_str

    def ping(
        self, service: Service, site_name: str, home_url: str, post_url: str
    ) -> tuple[bool, str]:
        """weblogUpdates.extendedPing and weblogUpdates.ping method."""
        client = self.to_client(service.url)

        response = self.extended_ping(
            client=client, site_name=site_name, home_url=home_url, post_url=post_url
        )
        success, result = self.parse_respnose(response)
        if success:
            return success, result

        response = self.basic_ping(
            client=client, site_name=site_name, home_url=home_url
        )
        return self.parse_respnose(response)

    def pinging(
        self,
        list_service: list[Service],
        site_name: str,
        home_url: str,
        post_url: str,
        strict: bool = False,
    ) -> tuple[bool, float]:
        """Send ping request to alive services, Return tuple of success and success ratio."""
        total, good = len(list_service), 0
        for service in list_service:
            okay, _ = self.ping(
                service=service,
                site_name=site_name,
                home_url=home_url,
                post_url=post_url,
            )
            if okay:
                good += 1

        success = bool(good == total if strict else good > 0)
        ratio = float(good / total)
        return success, ratio

    def check_service(self, service: Service) -> tuple[bool, str]:
        """Check service alive."""
        site_name = "Github"
        home_url = "https://github.com/"
        post_url = "https://github.com/about"
        return self.ping(
            service=service,
            site_name=site_name,
            home_url=home_url,
            post_url=post_url,
        )

    def checking_service(self, list_service_url: list[str]) -> list[Service]:
        """Checking list of new service url, Return list of Service."""
        list_service_url = [self.normalize(url) for url in list_service_url]
        list_service_url = [url for url in list_service_url if url]
        list_service_url = list(set(list_service_url))
        if not list_service_url:
            self.logger.warning("no valid service urls.")
            return []

        checked, good = 0, 0
        list_service: list[Service] = []
        list_service_url = sorted(list_service_url)
        checked = len(list_service_url)
        self.logger.info(f"<{checked}>list_service_url to check...")

        for index, service_url in enumerate(list_service_url):
            service = self.to_service(service_url)
            success, response_str = self.check_service(service)
            self.logger.info(f"<{index}>[{success}] `{service.url}` -- {response_str}")
            service.alive = success
            service.error = response_str
            list_service.append(service)

            if success:
                good += 1

        self.logger.info(f"<{checked}>service checked. <{good}>good found.")
        return list_service


class TestPinger:
    """TestCase for Pinger."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")

    list_service_url = [
        "http://rpc.pingomatic.com",
        "https://rpc.twingly.com/",
        #  "http://ping.blo.gs/",  # Failed at 2022-02-14
        "http://www.blogdigger.com/RPC2",
    ]

    def test_base_pinger(self) -> None:
        """Test BasePinger."""
        pinger = BasePinger(
            list_ua=[self.config.user_agent], list_px=[self.config.proxy_url]
        )
        assert self.config.user_agent == pinger.rnd_ua
        assert self.config.proxy_url == pinger.rnd_px

        assert pinger.normalize("ftp://hello.com") == ""
        assert pinger.normalize("http://bing.com/") == "http://bing.com"

        list_service = [pinger.to_service(url) for url in self.list_service_url]
        file_service = DIR_DEBUG / "pinger.service.json"
        pinger.save_services(file_service, list_service)
        assert file_service.is_file()
        assert list_service == pinger.load_services(file_service)
        file_service.unlink(missing_ok=True)
        assert file_service.is_file() is False

    def test_xml_pinger(self) -> None:
        """Test XMLPinger."""
        pinger = XMLPinger(
            list_ua=[self.config.user_agent],
            list_px=[self.config.proxy_url],
            logger=self.logger,
        )
        list_service = [pinger.to_service(url) for url in self.list_service_url]
        assert len(list_service) == len(self.list_service_url)
        list_client = [pinger.to_client(url) for url in self.list_service_url]
        assert len(list_client) == len(self.list_service_url)

        # Check service alive.
        for service in list_service:
            success, _ = pinger.check_service(service)
            assert success is True

        # Checking list service.
        list_service = pinger.checking_service(self.list_service_url)
        assert len(list_service) == len(self.list_service_url)
        assert any(service.alive is True for service in list_service)

        site_name = "Github"
        home_url = "https://github.com/"
        post_url = "https://github.com/about"
        success, ratio = pinger.pinging(list_service, site_name, home_url, post_url)
        assert success is True
        assert ratio > 0


if __name__ == "__main__":
    TestPinger()
