"""
    Debugger
"""

import json
import random
import string
from pathlib import Path
from typing import Any, Union

import arrow

__all__ = ("Debugger",)


class Debugger:
    """Debugger to generate string identities"""

    __slots__ = ("__dict__", "path", "name", "length", "sid")

    def __init__(self, path: Path, name: str, length: int = 4) -> None:
        self.path = path
        self.name = name
        self.length = length
        self.sid = ""

    @staticmethod
    def log(message: Any) -> None:
        """logging message for now"""
        now = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        print(f"{now} - {message}")

    def sid_init(self) -> str:
        """initialize sid"""
        seed = string.ascii_letters + string.digits
        if not self.name:
            rnd = [random.choice(seed) for _ in range(self.length)]
            self.name = "".join(rnd)
        suffix = "0".rjust(self.length, "0")
        return f"{self.name}-{suffix}"

    def sid_add(self, sid: str) -> str:
        """increase right side of sid by 1"""
        suffix_str = sid.split("-")[1]
        suffix_int = int(suffix_str) + 1
        suffix = "{}".format(suffix_int).rjust(self.length, "0")
        return "{}-{}".format(self.name, suffix)

    def sid_new(self) -> str:
        """
        Generate sid fomrat: `[char]-[number]`
        example: abcd-0000, abcd-0001, abcd-0002
        for a long session, set number >= 6
        Usually call before save when need a new file name for debugging
        """
        if self.sid and "-" in self.sid:
            self.sid = self.sid_add(self.sid)
        else:
            self.sid = self.sid_init()
        return self.sid

    def save(self, data: Union[str, list, dict], encoding: str = "utf8") -> bool:
        """save data to file inside debug directory"""
        if not self.sid:
            raise ValueError("debugger sid not set!")

        file_name = Path(self.path, self.sid)
        with open(file_name, "w", encoding=encoding) as file:
            try:
                file.write(json.dumps(data, indent=2))
            except TypeError:
                file.write(str(data))
        result = file_name.is_file()
        self.log(f"[{result}]save debug: {file_name}")
        return result
