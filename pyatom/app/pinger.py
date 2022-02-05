"""
    Send requests to Ping Services.
    TODO: Add HTTP Post Pinger
"""

import random
import time
from pathlib import Path
from base64 import encodebytes
from dataclasses import dataclass, asdict
from urllib.parse import unquote_to_bytes, urlparse
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
from typing import Union, Tuple, Dict, Any

from tldextract import extract

from pyatom.base.log import Logger
from pyatom.base.io import (
    load_dict,
    save_dict,
)
from pyatom.base.proxy import HttpProxy


__all__ = ("Pinger",)


def normalize(url: str) -> str:
    """Normalize url string."""
    out = urlparse(url)
    if out.scheme not in ("http", "https"):
        return ""
    return url[:-1] if url.endswith("/") else url


def to_proxy_headers(usr: str, pwd: str) -> dict:
    """Generate proxy headers."""
    if not usr and not pwd:
        return {}
    if usr and pwd:
        auth_str = f"{usr}:{pwd}"
        auth_bytes = unquote_to_bytes(auth_str)
        auth_str = encodebytes(auth_bytes).decode("utf-8")
        auth_str = "".join(auth_str.split())  # get rid of whitespace
        return {"Proxy-Authorization": "Basic " + auth_str}

    raise ValueError(f"proxy auth error: `{usr}`:`{pwd}`")


@dataclass
class Service:
    """XML-RPC Ping Service."""

    url: str
    geo: str
    alive: bool
    timestamp: int
    err: str


class HTTPProxyTransport(Transport):
    """HTTP Proxy Transport."""

    def __init__(self, proxy_str: str, user_agent: str, time_out: int):
        """Init."""
        Transport.__init__(self)

        self.proxy = HttpProxy(proxy_str=proxy_str)
        self.user_agent = user_agent
        self.proxy_headers = to_proxy_headers(self.proxy.usr, self.proxy.pwd)
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

    def __init__(self, proxy_str: str, user_agent: str, time_out: int):
        """Init."""
        SafeTransport.__init__(self)

        self.proxy = HttpProxy(proxy_str=proxy_str)
        self.user_agent = user_agent
        self.proxy_headers = to_proxy_headers(self.proxy.usr, self.proxy.pwd)
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


class Pinger:
    """XML-RPC Pinger for ping services."""

    time_out = 30

    list_service_str = (
        "http://rpc.pingomatic.com",
        "https://rpc.twingly.com/",
        "http://ping.blo.gs/",
        "http://www.blogdigger.com/RPC2",
        #  "https://feedburner.google.com/fb/a/ping"
        #  "https://www.pingmyblog.com/",
        #  "http://ping.feedburner.com",
        #  "http://www.weblogues.com/RPC/",
        #  "http://pingoat.com/goat/RPC2",
    )

    def __init__(
        self, list_ua: list[str], list_px: list[str], file_service: Path, logger: Logger
    ) -> None:
        """Init Pinger."""

        self.list_ua = list_ua
        self.list_px = list_px
        self.file_service = file_service
        self.logger = logger

        self.service_data = self.load_services()

    def to_ua(self) -> str:
        """Generate random User-Agent string."""
        return random.choice(self.list_ua)

    def to_px(self) -> str:
        """Generate random Proxy string."""
        return random.choice(self.list_px)

    def load_services(self) -> dict[str, Service]:
        """Load dict of service as dict.
        # keys:  `service` string, `geo` string, `alive` bool, `timestamp` int
        """
        if not self.file_service.is_file():
            return {}

        data = load_dict(self.file_service)
        return {
            service_url: Service(
                url=item.get("url", ""),
                geo=item.get("geo", ""),
                alive=item.get("alive", False),
                timestamp=item.get("timestamp", 0),
                err=item.get("err", ""),
            )
            for service_url, item in data.items()
        }

    def save_services(self, service_data: dict[str, Service]) -> None:
        """Save list of service as dict."""
        save_dict(
            file_name=self.file_service,
            file_data={
                service_url: asdict(service)
                for service_url, service in service_data.items()
            },
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
            self.logger.error(response.get("message", ""))
            return False, response_str

        return True, response_str

    def ping(
        self, client: ServerProxy, site_name: str, home_url: str, post_url: str
    ) -> tuple[bool, str]:
        """weblogUpdates.extendedPing and weblogUpdates.ping method."""
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

    def to_client(
        self, service: Service, proxy_str: str, user_agent: str
    ) -> ServerProxy:
        """Generate ServerProxy client."""
        if service.url.startswith("https"):
            return ServerProxy(
                service.url,
                transport=HTTPSProxyTransport(
                    proxy_str=proxy_str, user_agent=user_agent, time_out=self.time_out
                ),
            )
        return ServerProxy(
            service.url,
            transport=HTTPProxyTransport(
                proxy_str=proxy_str, user_agent=user_agent, time_out=self.time_out
            ),
        )

    def pinging(
        self, site_name: str, home_url: str, post_url: str, strict: bool = False
    ) -> tuple[bool, float]:
        """Send ping request, Return tuple of success and success ratio."""
        alive, good = 0, 0
        for _, service in self.service_data.items():
            if service.alive:
                alive += 1
                client = self.to_client(
                    service=service, proxy_str=self.to_px(), user_agent=self.to_ua()
                )
                okay, _ = self.ping(
                    client=client,
                    site_name=site_name,
                    home_url=home_url,
                    post_url=post_url,
                )
                if okay:
                    good += 1
        #  print(f"alive = {alive}, success = {success}")
        if not alive:
            warn_message = "Pinger.service alive = 0"
            self.logger.warning(warn_message)
            return False, 0.0

        success = bool(good == alive if strict else good > 0)
        ratio = float(good / alive)
        return success, ratio

    @staticmethod
    def to_geo(url: str) -> str:
        """Get url domain geo string."""
        out = extract(url)
        return str(out.suffix)

    def check_service(self, service: Service) -> tuple[bool, str]:
        """Check service alive."""
        site_name = "Github"
        home_url = "https://github.com/"
        post_url = "https://github.com/about"
        client = self.to_client(
            service=service,
            proxy_str=self.to_px(),
            user_agent=self.to_ua(),
        )
        return self.ping(
            client=client,
            site_name=site_name,
            home_url=home_url,
            post_url=post_url,
        )

    def checking_service(
        self,
        list_service_url: list[str],
        including_exist: bool = False,
        save_only_success: bool = False,
    ) -> None:
        """Checking list of new service url and save into local json file."""
        checked, good = 0, 0
        if including_exist:
            list_service_url.extend(self.service_data.keys())

        list_service_url = [normalize(url) for url in list_service_url]
        list_service_url = [url for url in list_service_url if url]
        list_service_url = list(set(list_service_url))
        list_service_url = sorted(list_service_url)
        checked = len(list_service_url)
        self.logger.info(f"<{checked}>list_service_url to check...")

        service_data: dict[str, Service] = self.service_data

        for index, service_url in enumerate(list_service_url):
            service = self.service_data.get(
                service_url,
                Service(
                    url=service_url,
                    geo=self.to_geo(service_url),
                    alive=False,
                    timestamp=int(time.time()),
                    err="",
                ),
            )
            success, response_str = self.check_service(service)
            if success:
                good += 1
            self.logger.info(f"<{index}>[{success}] `{service.url}` -- {response_str}")
            service.alive = success
            service.err = response_str
            service_data[service_url] = service

        if save_only_success:
            service_data = {
                url: service for url, service in service_data.items() if service.alive
            }

        self.save_services(service_data)
        self.logger.info(f"<{checked}>service checked. <{good}>good found.")
