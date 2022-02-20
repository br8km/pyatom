"""
    Proxy cls for http/socks proxy
"""

from base64 import encodebytes
from urllib.parse import unquote_to_bytes
from dataclasses import dataclass

import regex as re


__all__ = (
    "Proxy",
    "to_proxy",
)


@dataclass
class Proxy:
    """Proxy."""

    addr: str
    port: int = 80
    usr: str = ""
    pwd: str = ""

    scheme: str = "http"
    rdns: bool = True

    @property
    def url(self) -> str:
        """to proxy url string without auth even have."""
        return f"{self.scheme}://{self.addr}:{self.port}"

    @property
    def dict(self) -> dict:
        """to proxy data dictionary."""
        proxy_str = str(self)
        return {"http": proxy_str, "https": proxy_str}

    def __str__(self) -> str:
        """Get proxy string."""
        if self.usr and self.pwd:
            return f"{self.scheme}://{self.usr}:{self.pwd}@{self.addr}:{self.port}"
        return f"{self.scheme}://{self.addr}:{self.port}"

    @classmethod
    def header_auth(cls, usr: str, pwd: str) -> tuple[str, str]:
        """Generate proxy header value for `Proxy-Authorization`."""
        if usr and pwd:
            auth_str = f"{usr}:{pwd}"
            auth_bytes = unquote_to_bytes(auth_str)
            auth_str = encodebytes(auth_bytes).decode("utf-8")
            auth_str = "".join(auth_str.split())  # get rid of whitespace
            return "Proxy-Authorization", "Basic " + auth_str

        return "", ""


def to_proxy(proxy_str: str, scheme: str = "http", rdns: bool = True) -> Proxy:
    """Get Proxy by parsing proxy_str.

    Parameters:
        - proxy_str: str, format: `usr:pwd@addr:port` or `addr:port`
        - proxy_scheme: str, http, socks4, socks5, default `http`
        - proxy_rdns: bool, reverse dns, default True

    """
    if scheme not in ("http", "socks5", "socks4"):
        raise ValueError(f"proxy type not supported: `{scheme}`!")

    addr, port, usr, pwd = "", 80, "", ""

    # long proxy format: usr:pwd@addr:port
    pattern_long = (
        r"([\w]+?):([\w]+?)@([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"
    )
    # short proxy format: addr:port
    pattern_short = r"([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"

    if "@" in proxy_str:
        found = re.compile(pattern_long, re.I).findall(proxy_str)
        if found:
            usr, pwd, addr, port = found[0]
            port = int(port)
            return Proxy(
                addr=addr, port=port, usr=usr, pwd=pwd, scheme=scheme, rdns=rdns
            )

    found = re.compile(pattern_short, re.I).findall(proxy_str)
    if found:
        addr, port = found[0]
        port = int(port)
        return Proxy(addr=addr, port=port, usr=usr, pwd=pwd, scheme=scheme, rdns=rdns)

    raise ValueError(f"bad proxy format: {proxy_str}")


class TestProxy:
    """TestCase for Proxy."""

    @staticmethod
    def test_auth_headers() -> None:
        """Test proxy usr:pwd to auth headers."""
        usr, pwd = "hello", "world"
        key, value = Proxy.header_auth(usr=usr, pwd=pwd)
        assert key and key.startswith("Proxy")
        assert value and value.startswith("Basic")

    @staticmethod
    def test_proxy() -> None:
        """Test general proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        scheme = "http"
        proxy = to_proxy(proxy_str=proxy_str, scheme=scheme)
        assert isinstance(proxy, Proxy)
        assert proxy.usr == "hello_"
        assert proxy.pwd == "World8"
        assert proxy.port == 5000
        assert str(proxy).startswith(scheme)
        assert str(proxy).endswith(proxy_str)


if __name__ == "__main__":
    TestProxy()
