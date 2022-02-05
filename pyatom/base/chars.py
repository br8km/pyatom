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
    "str_clean",
    "hash2s",
    "hash2b",
)


def str_rnd(
    number: int = 12, upper: bool = False, strong: bool = False, ultra: bool = False
) -> str:
    """generate random string"""
    seq = string.ascii_lowercase + string.digits
    if upper is True:
        seq = string.ascii_letters + string.digits
    if strong is True:
        seq = string.ascii_letters + string.digits + "@#$%"
    if ultra is True:
        res: list[str] = [char.strip() for char in string.printable]
        res = [char for char in res if char]
        seq = "".join(res)
    rnd = [random.choice(seq) for _ in range(number)]
    return "".join(rnd)


def str_clean(text: str) -> str:
    """clean none string characters or multiline white space"""
    text = re.sub(r"[^a-zA-Z0-9]", " ", text)
    text = re.sub(r"[\s]{2,}", " ", text)
    return text.strip()


def hash2s(text: str) -> str:
    """generate hash string for text string"""
    middle = hashlib.md5(text.encode())
    return middle.hexdigest()


def hash2b(text: str) -> bytes:
    """generate hash bytes for text string"""
    middle = hashlib.md5(text.encode())
    return middle.digest()
