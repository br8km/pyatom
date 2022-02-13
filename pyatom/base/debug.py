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

    __slots__ = (
        "path",
        "name",
        "length",
        "id_int",
        "id_str",
    )

    def __init__(self, path: Path, name: str, length: int = 4) -> None:
        self.path = path
        self.length = length
        self.name = name if name else self.rnd_name()

        self.id_int = 0
        self.id_str = self.id2str()

    @staticmethod
    def log(message: Any) -> None:
        """logging message for now"""
        now = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        print(f"{now} - {str(message)}")

    def rnd_name(self) -> str:
        """Generate self.name if empty."""
        seed = string.ascii_letters + string.digits
        rnd = [random.choice(seed) for _ in range(self.length)]
        return "".join(rnd)

    def id2str(self) -> str:
        """Transfer id int number to string."""
        suffix = "{}".format(self.id_int).rjust(self.length, "0")
        return f"{self.name}-{suffix}"

    def id_add(self) -> None:
        """
        Add 1 to id_int and generate new id_str fomrat: `[string]-[number]`
        example: abcd-0000, abcd-0001, abcd-0002
        for a long session, set number >= 6
        Usually call before save when need a new file name for debugging
        """
        self.id_int += 1
        self.id_str = self.id2str()

    def to_file(self) -> Path:
        """Generate file path from self.id_str."""
        return Path(self.path, self.id_str + ".debug")

    def save(self, data: Union[str, list, dict], encoding: str = "utf8") -> bool:
        """save data to file inside debug directory"""
        file_name = self.to_file()
        with open(file_name, "w", encoding=encoding) as file:
            try:
                file.write(json.dumps(data, indent=2))
            except TypeError:
                file.write(str(data))
        result = file_name.is_file()
        self.log(f"[{result}]save debug: {file_name}")
        return result


class TestDebugger:
    """Test Debugger."""

    name = "test"
    debugger = Debugger(path=Path(__file__).parent, name=name)

    def test_debugger(self) -> None:
        """Test debugger methods."""
        assert self.debugger.name
        assert self.debugger.id_int == 0
        assert self.debugger.id_str.endswith("0" * self.debugger.length)

        for index in range(10):
            self.debugger.id_add()
            assert self.debugger.id_str.endswith(str(index + 1))

        file_debug = self.debugger.to_file()
        assert file_debug.suffix == ".debug"

        assert self.debugger.save(data={"key": "value"})

        assert self.debugger.save(data={"key": ["value"]})

        assert self.debugger.save(data=["value"])

        assert self.debugger.save(data="value")

        file_debug.unlink(missing_ok=True)
        assert file_debug.is_file() is False


if __name__ == "__main__":
    app = TestDebugger()
