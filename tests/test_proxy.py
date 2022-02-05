# -*- coding: utf-8 -*-
"""
    Test case for Proxy cls.
"""

from src.atom_proxy import Proxy


class TestProxy:
    """Test case for Procy cls."""

    @staticmethod
    def test_scheme() -> None:
        """Test parse proxy type."""
        netloc = "user-Name:pwd2022@1.2.3.144:80"
        schemes = {
            "http": 3,
            "https": 3,
            "socks4": 1,
            "socks5": 2,
        }
        for scheme, value in schemes.items():
            proxy_str = scheme + "://" + netloc
            proxy = Proxy(proxy_str=proxy_str)
            assert proxy.type == value

    @staticmethod
    def test_parse() -> None:
        """Test parse proxy string."""
        proxy_str = "https://user-Name:pwd2022@123.12.22.11:55555"
        proxy = Proxy(proxy_str=proxy_str)
        assert proxy.port == 55555
