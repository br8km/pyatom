"""
    Common Operation
"""

import random
from dataclasses import dataclass, asdict

import orjson

__all__ = (
    "print2",
    "split_list_int",
    "split_list_str",
    "to_dict",
    "to_json",
)


def print2(data: dict, extra_line: bool = True) -> None:
    """Pretty print dictionary with indent and extra line"""
    if type(data) in (dict, list):
        opt = orjson.OPT_INDENT_2
        if extra_line:
            opt = opt | orjson.OPT_APPEND_NEWLINE
        print(orjson.dumps(data, option=opt).decode())


def split_list_int(list_obj: list[int], number: int) -> list[list[int]]:
    """split list of int into list of list of int, each group include number of item."""
    return [list_obj[i : i + number] for i in range(0, len(list_obj), number)]


def split_list_str(list_obj: list[str], number: int) -> list[list[str]]:
    """split list of str into list of list of str, each group include number of item."""
    return [list_obj[i : i + number] for i in range(0, len(list_obj), number)]


def to_dict(obj: object) -> dict:
    """parse object attributes into dictionary"""
    data = {}
    for key in dir(obj):
        value = getattr(obj, key)
        if not key.startswith("__") and not callable(value):
            data[key] = value
    return data


def to_json(text: str) -> dict:
    """from text string to json format"""
    try:
        data = orjson.loads(text)
        if isinstance(data, dict):
            return data
    except orjson.JSONDecodeError as err:
        print(err)
    return {}


@dataclass
class SomeForTest:
    """Some cls for Test."""

    name: str
    age: int
    male: bool
    height: float
    money: list[float]
    data: dict


class TestUtils:
    """TestCase for Utils."""

    @staticmethod
    def test_print2() -> None:
        """Test print2 beauty print."""
        data = {"hello": "world", "age": 25, "name": ["Ben", "Cary"], "dict": {}}
        print2(data=data, extra_line=False)
        print2(data=data, extra_line=True)

    @staticmethod
    def test_split() -> None:
        """Test split list of string or integer."""
        number = 5
        list_int = [random.randint(0, 9) for _ in range(10)]
        group_int = split_list_int(list_int, number=number)
        assert len(group_int[0]) == number
        assert len(group_int) * number <= len(list_int)

        list_str = [str(random.randint(0, 9)) for _ in range(10)]
        group_str = split_list_str(list_str, number=number)
        assert len(group_str[0]) == number
        assert len(group_str) * number <= len(list_str)

    @staticmethod
    def test_to() -> None:
        """Test to_dict and to_json."""
        some = SomeForTest(
            name="name", age=25, male=True, height=10.0, money=[100.0], data={}
        )
        dict_some = asdict(some)
        assert dict_some == to_dict(some)

        str_some = orjson.dumps(dict_some).decode()
        print(str_some, type(str_some))
        json_some = to_json(str_some)
        print(json_some, type(json_some))
        assert json_some == dict_some


if __name__ == "__main__":
    app = TestUtils()
