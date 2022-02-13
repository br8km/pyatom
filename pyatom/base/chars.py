# -*- coding: utf-8 -*-
"""
    Character String Operation
"""

import hashlib
import random
import string

import regex as re


__all__ = (
    "str_rnd",
    "hash2s",
    "hash2b",
)


def str_rnd(
    number: int = 12, upper: bool = False, strong: bool = False, ultra: bool = False
) -> str:
    """generate random string"""
    seed = string.ascii_lowercase + string.digits
    if upper is True:
        seed = string.ascii_letters + string.digits
    if strong is True:
        seed = string.ascii_letters + string.digits + "@#$%"
    if ultra is True:
        seed = string.ascii_letters + string.digits + string.punctuation
    rnd = [random.choice(seed) for _ in range(number)]
    return "".join(rnd)


def hash2s(text: str) -> str:
    """generate hash string for text string"""
    middle = hashlib.md5(text.encode())
    return middle.hexdigest()


def hash2b(text: str) -> bytes:
    """generate hash bytes for text string"""
    middle = hashlib.md5(text.encode())
    return middle.digest()


class TestChars:
    """TestCase for chars operation."""

    @staticmethod
    def test_str_rnd() -> None:
        """Test string random generation."""

        number = 12
        strs = str_rnd(number=number)
        assert len(strs) == number
        assert re.compile(r"[A-Z]").findall(strs) == []

        strs = str_rnd(number=number, upper=True)
        assert re.compile(r"[A-Z]").findall(strs)

        strong_chars = "@#$%"
        assert any(
            char in str_rnd(strong=True) for char in strong_chars for _ in range(100)
        )

        assert any(
            char in str_rnd(ultra=True)
            for char in string.punctuation
            for _ in range(100)
        )

    @staticmethod
    def test_hash_str() -> None:
        """Test hash string."""
        hash_set = set()
        for _ in range(100):
            strs = str_rnd(number=12, upper=True, strong=True, ultra=True)
            hash_str = hash2s(strs)
            assert hash_str and hash_str not in hash_set
            hash_set.add(hash_str)

    @staticmethod
    def test_hash_bytes() -> None:
        """Test hash bytes."""
        hash_set = set()
        for _ in range(100):
            strs = str_rnd(number=12, upper=True, strong=True, ultra=True)
            hash_bytes = hash2b(strs)
            assert hash_bytes and hash_bytes not in hash_set
            hash_set.add(hash_bytes)


if __name__ == "__main__":
    app = TestChars()
