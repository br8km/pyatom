"""Markov Text Generator."""

import random
import string
from pathlib import Path
from collections import defaultdict

import regex as re
import numpy as np


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


class TestMarkov:
    """TestCase for Markov text generator."""

    dir_app = Path(__file__).parent

    @staticmethod
    def dummy(words: int = 1000) -> str:
        """generate dummy text"""
        return " ".join(
            [
                "".join(
                    [
                        random.choice(string.ascii_letters)
                        for _ in range(random.randint(5, 10))
                    ]
                )
                for _ in range(words)
            ]
        )

    def test_markov(self) -> None:
        """test markov generator"""
        number = 10
        text = self.dummy()
        app = Markov(text=text)
        for index in range(number):
            length = random.randint(20, 30)
            text = app.generate(distance=length)
            num_words = len(text.split(" "))
            print(f"<{index}>[{num_words}] {text}")
            assert num_words > 0


if __name__ == "__main__":
    TestMarkov()
