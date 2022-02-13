"""
    Proxy cls for http/socks proxy
"""


import regex as re


__all__ = ("Proxy", "HttpProxy", "Socks5Proxy")


class Proxy:
    """
    General cls for http/socks proxy parsing
    Parameters:
        - proxy_str: str, format: `usr:pwd@addr:port` or `addr:port`
        - proxy_type: int, socks4=1, socks5=2, http=3, default 3
        - proxy_rdns: bool, reverse dns, default True
    """

    __slots__ = ("proxy_str", "proxy_type", "proxy_rdns", "usr", "pwd", "addr", "port")

    def __init__(
        self, proxy_str: str, proxy_type: int = 3, proxy_rdns: bool = True
    ) -> None:
        self.proxy_str = proxy_str
        self.proxy_type = proxy_type
        self.proxy_rdns = proxy_rdns

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


class HttpProxy(Proxy):
    """http proxy"""

    def __init__(self, proxy_str: str, proxy_type: int = 3) -> None:
        super().__init__(proxy_str=proxy_str, proxy_type=proxy_type)


class Socks5Proxy(Proxy):
    """socks5 proxy"""

    def __init__(self, proxy_str: str, proxy_type: int = 2) -> None:
        super().__init__(proxy_str=proxy_str, proxy_type=proxy_type)


class TestProxy:
    """TestCase for Proxy."""

    @staticmethod
    def test_proxy() -> None:
        """Test general proxy string."""
        proxy_str = "hello_:World8@127.0.0.1:5000"
        proxy_type = 1
        proxy = Proxy(proxy_str=proxy_str, proxy_type=proxy_type)
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


if __name__ == "__main__":
    app = TestProxy()
