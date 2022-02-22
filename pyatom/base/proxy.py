"""
    Proxy cls for http/socks proxy
"""

from __future__ import annotations
from base64 import encodebytes
from urllib.parse import unquote_to_bytes
from dataclasses import dataclass

import regex as re


__all__ = ("Proxy",)


@dataclass
class Proxy:
    """Proxy."""

    addr: str = ""
    port: int = 80
    usr: str = ""
    pwd: str = ""

    scheme: str = "http"
    rdns: bool = True

    @classmethod
    def load(cls, url: str, rdns: bool = True) -> Proxy:
        """Load Proxy by parsing proxy_str.

        Parameters:
            - proxy_url: str, format: `usr:pwd@addr:port` or `addr:port` or `http://...`
            - rdns: bool, reverse dns, default True
        """
        scheme = url.split("://")[0] if "://" in url else "http"
        scheme = scheme.lower()
        if scheme not in ("http", "socks5", "socks4"):
            raise ValueError(f"proxy type not supported: `{scheme}`!")

        addr, port, usr, pwd = "", 80, "", ""

        # long proxy format: usr:pwd@addr:port
        pattern_long = r"([\w]+?):([\w]+?)@([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"
        # short proxy format: addr:port
        pattern_short = r"([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"

        if "@" in url:
            found = re.compile(pattern_long, re.I).findall(url)
            if found:
                usr, pwd, addr, port = found[0]
                port = int(port)
                return cls(
                    addr=addr, port=port, usr=usr, pwd=pwd, scheme=scheme, rdns=rdns
                )

        found = re.compile(pattern_short, re.I).findall(url)
        if found:
            addr, port = found[0]
            port = int(port)
            return cls(addr=addr, port=port, usr=usr, pwd=pwd, scheme=scheme, rdns=rdns)

        raise ValueError(f"bad proxy format: {url}")

    @property
    def server(self) -> str:
        """Get proxy server address without auth."""
        return f"{self.scheme}://{self.addr}:{self.port}"

    @property
    def url(self) -> str:
        """Get proxy url string."""
        if self.usr and self.pwd:
            return f"{self.scheme}://{self.usr}:{self.pwd}@{self.addr}:{self.port}"
        return self.server

    @property
    def data(self) -> dict[str, str]:
        """to proxy data dictionary."""
        return {"http": self.url, "https": self.url}

    @classmethod
    def header_auth(cls, usr: str, pwd: str) -> tuple[str, str]:
        """Generate proxy header value for `Proxy-Authorization`."""
        if usr and pwd:
            auth_str = f"{usr}:{pwd}"
            auth_bytes = unquote_to_bytes(auth_str)
            auth_str = encodebytes(auth_bytes).decode("utf-8")
            auth_str = "".join(auth_str.split())  # get rid of whitespace
            return "Proxy-Authorization", "Basic " + auth_str

        raise ValueError(f"proxy auth error @ usr=`{usr}`, pwd=`{pwd}`")


class TestProxy:
    """TestCase for Proxy."""

    @staticmethod
    def test_proxy_header_auth() -> None:
        """Test proxy usr:pwd to auth headers."""
        usr, pwd = "hello", "world"
        key, value = Proxy.header_auth(usr=usr, pwd=pwd)
        assert key and key.startswith("Proxy")
        assert value and value.startswith("Basic")

    @staticmethod
    def test_proxy() -> None:
        """Test general proxy string."""
        url = "http://hello_:World8@127.0.0.1:5000"
        proxy = Proxy.load(url=url)
        assert isinstance(proxy, Proxy)
        assert proxy.rdns is True
        assert proxy.scheme == "http"
        assert proxy.usr == "hello_"
        assert proxy.pwd == "World8"
        assert proxy.addr == "127.0.0.1"
        assert proxy.port == 5000
        assert proxy.url.startswith("http")
        assert proxy.server == "http://127.0.0.1:5000"
        assert isinstance(proxy.data, dict)
        assert list(proxy.data.keys()) == ["http", "https"]


if __name__ == "__main__":
    TestProxy()
