"""
    Proxy cls for http/socks proxy
"""

from base64 import encodebytes
from urllib.parse import unquote_to_bytes

import regex as re


__all__ = (
    "to_auth_header",
    "Proxy",
    "HttpProxy",
    "Socks5Proxy",
    "Socks4Proxy",
)


def to_auth_header(usr: str, pwd: str) -> tuple[str, str]:
    """Generate proxy headers."""
    if not usr and not pwd:
        return "", ""
    if usr and pwd:
        auth_str = f"{usr}:{pwd}"
        auth_bytes = unquote_to_bytes(auth_str)
        auth_str = encodebytes(auth_bytes).decode("utf-8")
        auth_str = "".join(auth_str.split())  # get rid of whitespace
        return "Proxy-Authorization", "Basic " + auth_str

    raise ValueError(f"proxy auth error: `{usr}`:`{pwd}`")


class Proxy:
    """
    General cls for http/socks proxy parsing
    Parameters:
        - proxy_str: str, format: `usr:pwd@addr:port` or `addr:port`
        - proxy_type: int, socks4=1, socks5=2, http=3, default 3
        - proxy_rdns: bool, reverse dns, default True
    """

    def __init__(self, proxy_str: str, scheme: str = "http", rdns: bool = True) -> None:
        """Init Proxy."""
        if scheme not in ("http", "socks5", "socks4"):
            raise ValueError(f"proxy type not supported: `{scheme}`!")

        self.proxy_str = proxy_str
        self.scheme = scheme
        self.rdns = rdns

        self.usr = ""
        self.pwd = ""
        self.addr = ""
        self.port = 80

        if not self.parse():
            raise ValueError(f"bad proxy format: {proxy_str}")

    def parse2(self) -> bool:
        """parse short format as `addr:port`"""
        pattern = r"([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"
        found = re.compile(pattern, re.I).findall(self.proxy_str)
        if found:
            addr, port = found[0]
            self.addr = addr
            self.port = int(port)
            return True
        return False

    def parse4(self) -> bool:
        """parse long format as `usr:pwd@addr:port`"""
        pattern = r"([\w]+?):([\w]+?)@([\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}):([\d]{2,5})"
        found = re.compile(pattern, re.I).findall(self.proxy_str)
        if found:
            usr, pwd, addr, port = found[0]
            self.usr = usr
            self.pwd = pwd
            self.addr = addr
            self.port = int(port)
            return True
        return False

    def parse(self) -> bool:
        """main parse method"""
        if "@" in self.proxy_str:
            return self.parse4()
        return self.parse2()

    @property
    def url(self) -> str:
        """Get proxy server uri string."""
        return f"{self.scheme}://{self.addr}:{self.port}"


class HttpProxy(Proxy):
    """Http proxy"""

    def __init__(self, proxy_str: str, scheme: str = "http") -> None:
        """Init HttpProxy."""
        super().__init__(proxy_str=proxy_str, scheme=scheme)


class Socks5Proxy(Proxy):
    """Socks5 proxy"""

    def __init__(self, proxy_str: str, scheme: str = "socks5") -> None:
        """Init Socks5Proxy."""
        super().__init__(proxy_str=proxy_str, scheme=scheme)


class Socks4Proxy(Proxy):
    """Socks4 proxy"""

    def __init__(self, proxy_str: str, scheme: str = "socks4") -> None:
        """Init Socks4Proxy."""
        super().__init__(proxy_str=proxy_str, scheme=scheme)


class TestProxy:
    """TestCase for Proxy."""

    @staticmethod
    def test_auth_headers() -> None:
        """Test proxy usr:pwd to auth headers."""
        usr, pwd = "hello", "world"
        key, value = to_auth_header(usr=usr, pwd=pwd)
        assert key and key.startswith("Proxy")
        assert value and value.startswith("Basic")

    @staticmethod
    def test_proxy() -> None:
        """Test general proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        proxy = Proxy(proxy_str=proxy_str)
        assert proxy.usr == "hello_"
        assert proxy.pwd == "World8"
        assert proxy.port == 5000

    @staticmethod
    def test_http_proxy() -> None:
        """Test http proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        proxy = HttpProxy(proxy_str=proxy_str)
        assert proxy.port == 5000

    @staticmethod
    def test_socks5_proxy() -> None:
        """Test socks5 proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        proxy = Socks5Proxy(proxy_str=proxy_str)
        assert proxy.port == 5000

    @staticmethod
    def test_socks4_proxy() -> None:
        """Test socks5 proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        proxy = Socks4Proxy(proxy_str=proxy_str)
        assert proxy.port == 5000


if __name__ == "__main__":
    TestProxy()
