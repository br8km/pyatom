"""
    Common Operation
"""

from typing import Any, Dict, List, Union

import orjson

__all__ = (
    "print2",
    "split_list",
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


def split_list(
    list_obj: list[Union[str, int]], number: int
) -> list[list[Union[str, int]]]:
    """Split list of string or integer into list of list of item."""
    return [list_obj[i : i + number] for i in range(0, len(list_obj), number)]


def split_list_int(list_obj: list[int], number: int) -> list[list[int]]:
    """split list of int into list of list of int"""
    return [list_obj[i : i + number] for i in range(0, len(list_obj), number)]


def split_list_str(list_obj: List[str], number: int) -> List[List[str]]:
    """split list of str into list of list of str"""
    return [list_obj[i : i + number] for i in range(0, len(list_obj), number)]


def to_dict(obj: object) -> Dict[str, Any]:
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
    except orjson.JSONDecodeError:
        pass
    return {}
