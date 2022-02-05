"""
    Input/Output Operation For File System
"""

import os
import shutil
from pathlib import Path
from typing import List, Union

import orjson


__all__ = (
    "dir_clear",
    "dir_create",
    "file_del",
    "load_str",
    "load_bytes",
    "load_list",
    "load_dict",
    "load_list_list",
    "load_list_dict",
    "load_line",
    "save_str",
    "save_bytes",
    "save_list",
    "save_dict",
    "save_list_list",
    "save_list_dict",
    "save_line",
)


def dir_clear(dir_name: Union[str, Path], retain_dir: bool = True) -> bool:
    """clear files with option to retain empty directory"""
    if isinstance(dir_name, Path):
        dir_name = str(dir_name.absolute())
    if os.path.isdir(dir_name):
        shutil.rmtree(dir_name)
    if retain_dir is True:
        os.makedirs(dir_name)
    return retain_dir == os.path.isdir(dir_name)


def dir_create(dir_name: Union[str, Path]) -> bool:
    """create directory"""
    if isinstance(dir_name, Path):
        dir_name = str(dir_name.absolute())
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return os.path.isdir(dir_name)


def file_del(file_name: Union[str, Path]) -> bool:
    """delete file if exsts"""
    if Path(file_name).is_file():
        try:
            os.remove(file_name)
            return True
        except OSError:
            pass
    return Path(file_name).is_file() is False


def load_str(file_name: Union[str, Path], encoding: str = "utf8") -> str:
    """load string from file"""
    with open(file_name, "r", encoding=encoding) as file:
        return file.read()


def load_bytes(file_name: Union[str, Path]) -> bytes:
    """load bytes from file"""
    with open(file_name, "rb") as file:
        return file.read()


def load_list(file_name: Union[str, Path], encoding: str = "utf8") -> list:
    """load list from file"""
    with open(file_name, "r", encoding=encoding) as file:
        result = orjson.loads(file.read())
        if isinstance(result, list):
            return result
        raise ValueError(f"load_list error: {file_name}")


def load_dict(file_name: Union[str, Path], encoding: str = "utf8") -> dict:
    """load dictionary from file"""
    with open(file_name, "r", encoding=encoding) as file:
        result = orjson.loads(file.read())
        if isinstance(result, dict):
            return result
        raise ValueError(f"load_dict error: {file_name}")


def load_list_list(file_name: Union[str, Path], encoding: str = "utf8") -> List[list]:
    """load list of list from file"""
    with open(file_name, "r", encoding=encoding) as file:
        result = orjson.loads(file.read())
        if isinstance(result, list):
            if result and all(isinstance(_, list) for _ in result):
                return result
        raise ValueError(f"load_list_list error: {file_name}")


def load_list_dict(file_name: Union[str, Path], encoding: str = "utf8") -> List[dict]:
    """load list of dictionary from file"""
    with open(file_name, "r", encoding=encoding) as file:
        result = orjson.loads(file.read())
        if isinstance(result, list):
            if result and all(isinstance(_, dict) for _ in result):
                return result
        raise ValueError(f"load_list_dict error: {file_name}")


def load_line(
    file_name: Union[str, Path],
    encoding: str = "utf8",
    min_chars: int = 0,
    keyword: str = "",
) -> List[str]:
    """load lines of string from file"""
    result = []
    with open(file_name, "r", encoding=encoding) as file:
        result = [x.strip() for x in file.readlines()]
        if min_chars:
            result = [x for x in result if len(x) >= min_chars]
        if keyword:
            result = [x for x in result if keyword in x]
    return result


def save_str(
    file_name: Union[str, Path], file_content: str, encoding: str = "utf8"
) -> None:
    """save string into file"""
    with open(file_name, "w", encoding=encoding) as file:
        file.write(file_content)


def save_bytes(file_name: Union[str, Path], file_content: bytes) -> None:
    """save bytes into file"""
    with open(file_name, "wb") as file:
        file.write(file_content)


def save_dict(
    file_name: Union[str, Path], file_data: dict, encoding: str = "utf8"
) -> None:
    """save dictionary into file"""
    with open(file_name, "w", encoding=encoding) as file:
        opt = orjson.OPT_INDENT_2
        file.write(orjson.dumps(file_data, option=opt).decode())


def save_list(
    file_name: Union[str, Path], file_data: list, encoding: str = "utf8"
) -> None:
    """save list into file"""
    with open(file_name, "w", encoding=encoding) as file:
        opt = orjson.OPT_INDENT_2
        file.write(orjson.dumps(file_data, option=opt).decode())


def save_list_list(
    file_name: Union[str, Path], file_data: List[list], encoding: str = "utf8"
) -> None:
    """save list of list into file"""
    with open(file_name, "w", encoding=encoding) as file:
        opt = orjson.OPT_INDENT_2
        file.write(orjson.dumps(file_data, option=opt).decode())


def save_list_dict(
    file_name: Union[str, Path], file_data: List[dict], encoding: str = "utf8"
) -> None:
    """save list of dict into file"""
    with open(file_name, "w", encoding=encoding) as file:
        opt = orjson.OPT_INDENT_2
        file.write(orjson.dumps(file_data, option=opt).decode())


def save_line(
    file_name: Union[str, Path], file_content: List[str], encoding: str = "utf8"
) -> None:
    """save lines of string into file"""
    with open(file_name, "w", encoding=encoding) as file:
        file.write("\n".join(file_content))
