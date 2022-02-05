# -*- coding: utf-8 -*-
"""
    Character String Operation
"""

import hashlib
import random
import string

from collections import defaultdict

import numpy as np
import regex as re


__all__ = (
    "str_rnd",
    "str_clean",
    "hash2s",
    "hash2b",
    "Markov",
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


class Markov:
    """
    Markov Chain Text Generator
    """

    def __init__(self, text: str) -> None:
        """Init markov text generator."""
        self.text = text

        pattern = re.compile(r"[a-zA-Z]+", re.I)
        tokens = [word for word in pattern.findall(text) if word != ""]

        self.markov_graph: defaultdict = defaultdict(lambda: defaultdict(int))

        last_word = tokens[0].lower()
        for word in tokens[1:]:
            word = word.lower()
            self.markov_graph[last_word][word] += 1
            last_word = word

        # limit = 3
        # for first_word in ["by", "who", "the"]:
        #     next_words = list(self.markov_graph[first_word].keys())[:limit]
        #     for next_word in next_words:
        #         print(first_word, next_word)

    def walk_graph(
        self, graph: dict, distance: int = 5, start_node: str = ""
    ) -> list[str]:
        """Returns a list of words from a randomly weighted walk."""
        if distance <= 0:
            return []

        # If not given, pick a start node at random.
        if not start_node:
            start_node = random.choice(list(graph.keys()))

        weights = np.array(
            list(self.markov_graph[start_node].values()), dtype=np.float64
        )
        # Normalize word counts to sum to 1.
        weights /= weights.sum()

        # Pick a destination using weighted distribution.
        choices = list(self.markov_graph[start_node].keys())
        if not choices:
            return []

        chosen_word = np.random.choice(choices, None, p=weights)

        return [chosen_word] + self.walk_graph(
            graph, distance=distance - 1, start_node=chosen_word
        )

    def generate(self, distance: int = 15) -> str:
        """generate words"""
        while True:
            new_words = self.walk_graph(self.markov_graph, distance=distance)
            if new_words:
                return " ".join(new_words)
