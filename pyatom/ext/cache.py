# -*- coding: utf-8 -*-

import time
from pathlib import Path

from ..base.io import IO
from ..cfg import Config


__all__ = ("Cache", )


class Cache:
    """Cache."""

    # --- cache for Any data

    @staticmethod
    def has_cache(file: Path, seconds: int) -> bool:
        """Has cached file for seconds or Not."""
        assert seconds > 0
        return bool(
            file.is_file()
            and file.stat().st_mtime > time.time() - seconds
        )

    @staticmethod
    def prune_cache(file: Path, seconds: int = 0) -> None:
        """Prune cache file expired out of seconds."""
        assert seconds >= 0
        point = time.time() - seconds
        if file.is_file() and file.stat().st_mtime < point:
            file.unlink()

    @staticmethod
    def prune_caches(dir: Path, seconds: int = 0) -> None:
        """Prune cache files expired out of seconds."""
        assert seconds >= 0
        point = time.time() - seconds
        for fp in dir.iterdir():
            if fp.is_file() and fp.stat().st_mtime < point:
                fp.unlink()

    # --- cache for list of dict

    @staticmethod
    def prune_list_dict(data: list[dict], seconds: int) -> list[dict]:
        """Prune list of dict."""
        point = time.time() - seconds
        remain = []
        for item in data:
            if item["cache_time"] >= point:
                remain.append(item)
        return remain

    @classmethod
    def load_list_dict(cls, file: Path, seconds: int) -> list[dict]:
        """Load list of user dict from local cache."""
        if file.is_file():
            data = IO.load_list_dict(file)
            return cls.prune_list_dict(data=data, seconds=seconds)
        return []

    @classmethod
    def add_list_dict(cls, file: Path, item: dict, seconds: int) -> bool:
        """Add one item into local cache."""
        cached = cls.load_list_dict(file=file, seconds=seconds)
        item["cache_time"] = int(time.time())
        cached.append(item)
        IO.save_list_dict(file_name=file, file_data=cached)
        return file.is_file()

    @classmethod
    def save_list_dict(cls, file: Path, data: list[dict], seconds: int) -> bool:
        """Save list of items into local cache."""
        cached = cls.load_list_dict(file=file, seconds=seconds)
        for item in data:
            item["cache_time"] = int(time.time())
            cached.append(item)
        IO.save_list_dict(file_name=file, file_data=cached)
        return file.is_file()

    # --- cache for dict of dict

    @classmethod
    def prune_dict_dict(cls, data: dict[str, dict], seconds: int) -> dict[str, dict]:
        """Prune dict of dict."""
        point = time.time() - seconds
        remain: dict[str, dict] = {}
        for key, item in data.items():
            if item["cache_time"] >= point:
                remain[key] = item
        return remain

    @classmethod
    def load_dict_dict(cls, file: Path, seconds: int) -> dict[str, dict]:
        """Load dict of dict from local cache."""
        if file.is_file():
            data = IO.load_dict(file)
            return cls.prune_dict_dict(data=data, seconds=seconds)
        return {}

    @classmethod
    def add_dict_dict(cls, file: Path, key: str, item: dict, seconds: int) -> bool:
        """Add one key:item into local cache."""
        cached = cls.load_dict_dict(file=file, seconds=seconds)
        item["cache_time"] = int(time.time())
        cached[key] = item
        IO.save_dict(file_name=file, file_data=cached)
        return file.is_file()

    @classmethod
    def save_dict_dict(cls, file: Path, data: dict[str, dict], seconds: int) -> bool:
        """Add one key:item into local cache."""
        cached = cls.load_dict_dict(file=file, seconds=seconds)
        for key, item in data.items():
            item["cache_time"] = int(time.time())
            cached[key] = item
        IO.save_dict(file_name=file, file_data=cached)
        return file.is_file()


class TestCache:
    """Test Cache.

        :[okay]Tested: 20230717
    
    """

    config = Config()

    def test_cache_any(self) -> None:
        """Test cache for any data."""
        file = self.config.dir_cache / "TestCache.any.json"
        data = {"hello": "world", "age": 35}
        seconds = 10

        # start with no cache, cache = False
        assert not Cache.has_cache(file=file, seconds=seconds)

        # save file, now cache = True
        IO.save_dict(file, data)
        assert Cache.has_cache(file=file, seconds=seconds)

        # prune cache, but still cache = True
        Cache.prune_cache(file=file, seconds=seconds)
        assert Cache.has_cache(file=file, seconds=seconds)

        # wait for seconds + 1, now cache = False
        time.sleep(seconds + 1)
        assert not Cache.has_cache(file=file, seconds=seconds)

        # prune all caches inside of parent dir, cache = False
        Cache.prune_caches(dir=file.parent, seconds=0)
        assert not Cache.has_cache(file=file, seconds=seconds)

    def test_cache_list_dict(self) -> None:
        """Test cache list of dict items."""
        file = self.config.dir_cache / "TestCache.list_dict.json"
        data = [
            {"name": "amy", "age": 15},
            {"name": "ben", "age": 35},
            {"name": "coo", "age": 20},
        ]
        seconds = 20

        # add item: data[0]
        assert Cache.add_list_dict(file=file, item=data[0], seconds=seconds)
        cached = Cache.load_list_dict(file=file, seconds=seconds)
        assert cached == [data[0]]

        # wait 10 seconds, add data[1], data[2]
        time.sleep(10)
        assert Cache.save_list_dict(file=file, data=data[1:], seconds=seconds)
        cached = Cache.load_list_dict(file=file, seconds=seconds)
        assert cached == data

        # wait 10 + 1 seconds, now data[0] gone out of cache 
        time.sleep(10 + 1)
        cached = Cache.load_list_dict(file=file, seconds=seconds)
        assert cached == data[1:]

        # wait 10 seconds, all cache items expired.
        time.sleep(10)
        cached = Cache.load_list_dict(file=file, seconds=seconds)
        assert cached == []

        # prune all caches inside of parent dir, cache = False
        Cache.prune_caches(dir=file.parent, seconds=0)
        assert not Cache.has_cache(file=file, seconds=seconds)

    def test_cache_dict_dict(self) -> None:
        """Test cache dict of dict items."""
        file = self.config.dir_cache / "TestCache.dict_dict.json"
        amy = {"name": "amy", "age": 15}
        ben = {"name": "ben", "age": 25}
        coo = {"name": "coo", "age": 35}
        data = {
            "amy": amy,
            "ben": ben,
            "coo": coo,
        }
        seconds = 20

        # add item: data["amy"]
        assert Cache.add_dict_dict(file=file, key="amy", item=amy, seconds=seconds)
        cached = Cache.load_dict_dict(file=file, seconds=seconds)
        assert cached == {"amy": amy}

        # wait 10 seconds, add data["ben"], data["coo"]
        time.sleep(10)
        data_2 = {
            "ben": ben,
            "coo": coo,
        }
        assert Cache.save_dict_dict(file=file, data=data_2, seconds=seconds)
        cached = Cache.load_dict_dict(file=file, seconds=seconds)
        assert cached == data

        # wait 10 + 1 seconds, now {"amy": amy} gone out of cache 
        time.sleep(10 + 1)
        cached = Cache.load_dict_dict(file=file, seconds=seconds)
        assert cached == data_2

        # wait 10 seconds, all cache items expired.
        time.sleep(10)
        cached = Cache.load_dict_dict(file=file, seconds=seconds)
        assert cached == {}

        # prune all caches inside of parent dir, cache = False
        Cache.prune_caches(dir=file.parent, seconds=0)
        assert not Cache.has_cache(file=file, seconds=seconds)

    def run(self) -> None:
        """Run."""
        self.test_cache_any()
        self.test_cache_list_dict()
        self.test_cache_dict_dict()

if __name__ == "__main__":
    TestCache().run()