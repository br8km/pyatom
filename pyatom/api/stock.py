"""Stock Photos/Videos/Icons/Fonts API Wrapper."""


import time
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Union, Any, Iterable
from dataclasses import dataclass

import requests

from pyatom.base.chars import hash2s
from pyatom.base.io import IO
from pyatom.config import ConfigManager
from pyatom.config import DIR_DEBUG


__all__ = ("Pixabay",)


@dataclass
class BaseItem(ABC):
    """Base cls for Stock Item."""

    iid: str
    type: str
    tags: str

    views: int
    downloads: int


@dataclass
class Photo(BaseItem):
    """Stock Photo Item."""

    width: int
    height: int
    size: int

    url: str


@dataclass
class Video(BaseItem):
    """Stock Video Item."""

    duration: int

    width: int
    height: int
    size: int

    url: str


@dataclass
class Icon(BaseItem):
    """Stock Icon Item."""


@dataclass
class Font(BaseItem):
    """Stock Font Item."""


class BaseStock(ABC):
    """Base cls for stock items."""

    def __init__(self, name: str, cache_second: int, dir_cache: Path) -> None:
        """Init."""
        self.name = name
        self.cache_second = cache_second  # set 0 for disable cache

        self.sep = "__"  # file name seperator
        self.dir_cache = dir_cache

        IO.dir_create(self.dir_cache)

        self.payload: dict[str, str] = {}

    def cache_save(self, request_url: str, response_data: dict) -> bool:
        """Save cache response data into local file."""
        file_cache = self.to_cache_file(request_url)
        IO.save_dict(file_cache, response_data)
        return file_cache.is_file()

    def cache_get(self, request_url: str) -> dict:
        """Get cached response data from local file."""
        cache_id = hash2s(request_url)
        for file in self.dir_cache.glob(self.name + self.sep + "*.*"):
            if cache_id in file.name:
                return IO.load_dict(file)
        return {}

    def cache_clear(self) -> bool:
        """Clear cached items."""
        now = int(time.time())
        for file in self.dir_cache.glob(self.name + self.sep + "*.*"):
            time_stamp = int(file.stem.split(self.sep)[1])
            if now > time_stamp + self.cache_second:
                file.unlink()
        return True

    def cache_del(self) -> bool:
        """Delete cache diretory."""
        return IO.dir_del(self.dir_cache)

    def to_cache_file(self, request_url: str) -> Path:
        """Generate random filename corresponding to cache_id and timestamp."""
        cache_id = hash2s(request_url)
        now_str = str(int(time.time()))
        file_name = self.sep.join([self.name, now_str, cache_id])
        return Path(self.dir_cache, f"{file_name}.json")

    @staticmethod
    @abstractmethod
    def param_valid(key: str) -> list[str]:
        """Get valid param value string list."""
        assert key
        return []

    def add_param_str(self, key: str, value: Any, max_chars: int = 0) -> None:
        """Add parameter string into payload."""
        if not isinstance(value, str):
            raise TypeError(f"Param `{key}` must be string")

        valid = self.param_valid(key=key)
        if valid and value not in valid:
            raise ValueError(f"Param `{key}` not valid")

        if max_chars and len(value) > max_chars:
            raise ValueError(f"Param `{key}` cannot exceed {max_chars} characters")

        self.payload[key] = value

    def add_param_list_str(self, key: str, value: Any) -> None:
        """Add parameter list of string into payload."""
        if not isinstance(value, list) or not isinstance(value[0], str):
            raise TypeError(f"Param `{key}` must be list of string")

        valid = self.param_valid(key=key)
        if valid:
            for item in value:
                if item not in valid:
                    raise ValueError(f"Param `{key}` value not valid")

        self.payload[key] = ",".join(value)

    def add_param_int(
        self, key: str, value: Any, min_v: int = 0, max_v: int = 0
    ) -> None:
        """Add parameter integer into payload."""
        if not isinstance(value, int):
            raise TypeError(f"Param `{key}` must be integer")

        if min_v and value < min_v:
            raise ValueError(f"Param `{key}` < {min_v}")

        if max_v and value > max_v:
            raise ValueError(f"Param `{key}` > {max_v}")

        self.payload[key] = str(value)

    def add_param_bool(self, key: str, value: Any) -> None:
        """Add parameter bool into payload."""
        if not isinstance(value, bool):
            raise TypeError(f"Param `{key}` must be bool")

        self.payload[key] = str(value).lower()


class Pixabay(BaseStock):
    """Pixabay Free Stock Photos.

    api_document: https://pixabay.com/api/docs

    """

    def __init__(self, api_key: str, dir_cache: Path) -> None:
        """Init Pixabay."""
        super().__init__(name="Pixabay", cache_second=86400, dir_cache=dir_cache)

        self.api_key = api_key

    @staticmethod
    def param_valid(key: str) -> list:
        """Get valid value string list."""
        data = {
            "lang": [
                "cs",
                "da",
                "de",
                "en",
                "es",
                "fr",
                "id",
                "it",
                "hu",
                "nl",
                "no",
                "pl",
                "pt",
                "ro",
                "sk",
                "fi",
                "sv",
                "tr",
                "vi",
                "th",
                "bg",
                "ru",
                "el",
                "ja",
                "ko",
                "zh",
            ],
            "image_type": ["all", "photo", "illustration", "vector"],
            "video_type": [
                "all",
                "film",
                "animation",
            ],
            "orientation": ["all", "horizontal", "vertical"],
            "category": [
                "backgrounds",
                "fashion",
                "nature",
                "science",
                "education",
                "feelings",
                "health",
                "people",
                "religion",
                "places",
                "animals",
                "industry",
                "computer",
                "food",
                "sports",
                "transportation",
                "travel",
                "buildings",
                "business",
                "music",
            ],
            "colors": [
                "grayscale",
                "transparent",
                "red",
                "orange",
                "yellow",
                "green",
                "turquoise",
                "blue",
                "lilac",
                "pink",
                "white",
                "gray",
                "black",
                "brown",
            ],
            "order": ["popular", "latest"],
        }
        return data.get(key) or []

    def add_payload(self, **params: Union[str, int, bool]) -> None:
        """Generate request url string."""

        self.payload: dict[str, str] = {
            "lang": "en",
        }

        str_params = (
            "q",
            "lang",
            "id",
            "image_type",
            "video_type",
            "orientation",
            "category",
            "order",
            "callback",
        )

        int_params = (
            "min_width",
            "min_height",
            "page",
            "per_page",
        )

        bool_params = (
            "editors_choice",
            "safesearch",
            "pretty",
        )

        list_str_params = ("colors",)

        for key, value in params.items():

            if key in str_params:
                if key == "q":
                    self.add_param_str(key=key, value=value, max_chars=100)
                else:
                    self.add_param_str(key=key, value=value)

            if key in int_params:
                min_v, max_v = 0, 0
                if key == "page":
                    min_v = 1
                if key == "per_page":
                    min_v, max_v = 3, 200
                self.add_param_int(key=key, value=value, min_v=min_v, max_v=max_v)

            if key in bool_params:
                self.add_param_bool(key=key, value=value)

            if key in list_str_params:
                self.add_param_list_str(key=key, value=value)

    def to_url(self) -> str:
        """Build url for http request."""

        base = "https://pixabay.com/api/"
        payload_keys = self.payload.keys()

        if "image_type" in payload_keys:
            url = f"{base}?key={self.api_key}"
        elif "video_type" in payload_keys:
            url = f"{base}videos/?key={self.api_key}"
        else:
            raise ValueError("not valid search type")

        for key, value in self.payload.items():
            if key == "q":
                value = value.replace(" ", "+")
            url = f"{url}&{key}={value}"

        return url

    def parse(self, response_data: dict, search_type: str) -> tuple[bool, list[str]]:
        """Parse search items from response data."""
        print(self, response_data, search_type)
        return True, []

    @staticmethod
    def parse_totals(response_data: dict) -> tuple[int, int]:
        """Parse response data total and total hits number."""
        total = response_data.get("total") or 0
        total_hits = response_data.get("totalHits") or 0
        return total, total_hits

    @staticmethod
    def parse_images(
        response_data: dict, url_type: str = "imageURL"
    ) -> Iterable[Photo]:
        """Parse response data into Photos."""
        valid = ("imageURL", "fullHDURL", "vectorURL", "largeImageURL")
        if url_type not in valid:
            raise ValueError("Param `url_type` not valid")

        for hit in response_data.get("hits") or []:
            url_image = hit.get(url_type) or ""
            if not url_image:
                continue

            yield Photo(
                iid=hit.get("id") or "",
                type=hit.get("type") or "",
                tags=hit.get("tags") or "",
                width=hit.get("imageWidth") or 0,
                height=hit.get("imageHeight") or 0,
                size=hit.get("imageSize") or 0,
                views=hit.get("views") or 0,
                downloads=hit.get("downloads") or 0,
                url=url_image,
            )

    @staticmethod
    def parse_videos(response_data: dict, video_size: str = "large") -> Iterable[Video]:
        """Parse response data into Videos."""
        valid = ("large", "medium", "small", "tiny")
        if video_size not in valid:
            raise ValueError("Param `video_size` not valid")

        for hit in response_data.get("hits") or []:
            videos = hit.get("videos") or {}
            video = videos.get(video_size) or {}
            if not video:
                continue

            yield Video(
                iid=hit.get("id") or "",
                type=hit.get("type") or "",
                tags=hit.get("tags") or "",
                duration=hit.get("duration") or 0,
                width=video.get("width") or 0,
                height=video.get("height") or 0,
                size=video.get("size") or 0,
                views=hit.get("views") or 0,
                downloads=hit.get("downloads") or 0,
                url=video.get("url") or "",
            )

    @staticmethod
    def _request_data(url: str) -> dict:
        """Http request to get data from url string."""
        resp = requests.get(url=url)

        if not resp.status_code == 200:
            raise ValueError(resp.text)

        return dict(resp.json())

    def search(self, **params: Union[str, int, bool]) -> dict:
        """Search."""

        self.add_payload(**params)

        url = self.to_url()

        if self.cache_second:
            self.cache_clear()
            data = self.cache_get(request_url=url)
            if data:
                return data

            data = self._request_data(url)
            self.cache_save(url, data)
            return data

        return self._request_data(url)

    def search_image(self, **params: Union[str, int, bool]) -> dict:
        """returns Images API data in dict

        Images search

        :param q :type str :desc A URL encoded search term. If omitted,
        all images are returned. This value may not exceed 100 characters.
        Example: "yellow+flower"
        Default: "yellow+flower"

        :param lang :type str :desc Language code of the language to be searched in.
        Accepted values: cs, da, de, en, es, fr, id, it, hu, nl, no, pl, pt, ro, sk, fi,
        sv, tr, vi, th, bg, ru, el, ja, ko, zh
        Default: "en"
        For more info, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

        :param id :type str :desc Retrieve individual images by ID.
        Default: ""

        :param image_type :type str :desc Filter results by image type.
        Accepted values: "all", "photo", "illustration", "vector"
        Default: "all"

        :param orientation :type str :desc Whether an image is wider than it is tall,
        or taller than it is wide.
        Accepted values: "all", "horizontal", "vertical"
        Default: "all"

        :param category :type str :desc Filter results by category.
        Accepted values: fashion, nature, backgrounds, science, education, people,
        feelings, religion, health, places, animals, industry, food, computer, sports,
        transportation, travel, buildings, business, music

        :param min_width :type int :desc Minimum image width
        Default: 0

        :param min_height :type int :desc Minimum image height
        Default: 0

        :param colors :type str :desc A comma separated list of values may be used
        to select multiple properties.
        Accepted values: "grayscale", "transparent", "red", "orange", "yellow",
        "green", "turquoise", "blue", "lilac", "pink", "white", "gray", "black", "brown"

        :param editors_choice :type bool (python-pixabay use "true" and "false" string instead)
        :desc Select images that have received
        an Editor's Choice award.
        Accepted values: "true", "false"
        Default: "false"

        :param safesearch :type bool (python-pixabay use "true" and "false" string instead)
        :desc A flag indicating that only images suitable
        for all ages should be returned.
        Accepted values: "true", "false"
        Default: "false"

        :param order :type str :desc How the results should be ordered.
        Accepted values: "popular", "latest"
        Default: "popular"

        :param page :type int :desc Returned search results are paginated.
        Use this parameter to select the page number.
        Default: 1

        :param per_page :type int :desc Determine the number of results per page.
        Accepted values: 3 - 200
        Default: 20

        :param callback :type str :desc JSONP callback function name

        :param pretty :type bool (python-pixabay use "true" and "false" string instead)
        :desc Indent JSON output. This option should not
        be used in production.
        Accepted values: "true", "false"
        Default: "false"

        """

        if "image_type" not in params.keys():
            params["image_type"] = "all"

        return self.search(**params)

    def search_video(self, **params: Union[str, int, bool]) -> dict:
        """returns videos API data in dict

        Videos search

        :param q :type str :desc A URL encoded search term. If omitted,
        all images are returned. This value may not exceed 100 characters.
        Example: "yellow+flower"
        Default: "yellow+flower"

        :param lang :type str :desc Language code of the language to be searched in.
        Accepted values: cs, da, de, en, es, fr, id, it, hu, nl, no, pl, pt, ro, sk, fi,
        sv, tr, vi, th, bg, ru, el, ja, ko, zh
        Default: "en"
        For more info, see https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes

        :param id :type str :desc Retrieve individual images by ID.
        Default: ""

        :param video_type :type str :desc Filter results by video type.
        Accepted values: "all", "film", "animation"
        Default: "all"

        :param category :type str :desc Filter results by category.
        Accepted values: fashion, nature, backgrounds, science, education, people,
        feelings, religion, health, places, animals, industry, food, computer, sports,
        transportation, travel, buildings, business, music

        :param min_width :type int :desc Minimum image width
        Default: 0

        :param min_height :type int :desc Minimum image height
        Default: 0

        :param editors_choice :type bool (python-pixabay use "true" and "false" string instead)
        :desc Select images that have received
        an Editor's Choice award.
        Accepted values: "true", "false"
        Default: "false"

        :param safesearch :type bool (python-pixabay use "true" and "false" string instead)
        :desc A flag indicating that only images suitable
        for all ages should be returned.
        Accepted values: "true", "false"
        Default: "false"

        :param order :type str :desc How the results should be ordered.
        Accepted values: "popular", "latest"
        Default: "popular"

        :param page :type int :desc Returned search results are paginated.
        Use this parameter to select the page number.
        Default: 1

        :param per_page :type int :desc Determine the number of results per page.
        Accepted values: 3 - 200
        Default: 20

        :param callback :type str :desc JSONP callback function name

        :param pretty :type bool (python-pixabay use "true" and "false" string instead)
        :desc Indent JSON output. This option should not
        be used in production.
        Accepted values: "true", "false"
        Default: "false"

        """

        if "video_type" not in params.keys():
            params["video_type"] = "all"

        return self.search(**params)


class UnSplash(BaseStock):
    """UnSplash Free Stock Photos, with hashtag."""

    def __init__(self, dir_cache: Path) -> None:
        """Init UnSplash."""
        super().__init__(name="Unsplash", cache_second=86400, dir_cache=dir_cache)


class Pexels(BaseStock):
    """Pexels Free Stock Photos."""

    def __init__(self, dir_cache: Path) -> None:
        """Init Pexels."""
        super().__init__(name="Pexels", cache_second=86400, dir_cache=dir_cache)


class Flickr(BaseStock):
    """Flickr Free Stock Photos."""

    def __init__(self, dir_cache: Path) -> None:
        """Init Flickr."""
        super().__init__(name="Flickr", cache_second=86400, dir_cache=dir_cache)


class ShopifyBurst(BaseStock):
    """Burst.Shopify.com Free Stock Photos."""

    def __init__(self, dir_cache: Path) -> None:
        """Init Burst.Shopify."""
        super().__init__(name="Shopify", cache_second=86400, dir_cache=dir_cache)


class StockSnapIo(BaseStock):
    """StockSnap.Io Free Stock Photos."""

    def __init__(self, dir_cache: Path) -> None:
        """Init StockSnap."""
        super().__init__(name="StockSnap", cache_second=86400, dir_cache=dir_cache)


class MorgueFile(BaseStock):
    """MorgueFile.com Free Stock Photos, with hashtag."""

    def __init__(self, dir_cache: Path) -> None:
        """Init MorgueFile."""
        super().__init__(name="MorgueFile", cache_second=86400, dir_cache=dir_cache)


class WikiMediaCommons(BaseStock):
    """Commons.WikiMedia.org Free Stock Photos, with hashtag."""

    def __init__(self, dir_cache: Path) -> None:
        """Init WikiMedia.Commons."""
        super().__init__(
            name="WikiMedia.Commons", cache_second=86400, dir_cache=dir_cache
        )


class TestStock:
    """TestCase for Stock api wrappers."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    dir_cache = DIR_DEBUG / "cache"

    def test_base_cache(self) -> None:
        """Test BaseStock from Pixabay."""
        app = Pixabay(api_key=self.config.pixabay_key, dir_cache=self.dir_cache)

        request_url = "http://bing.com"
        response_data = {"url": request_url}
        assert app.cache_save(request_url=request_url, response_data=response_data)
        assert app.cache_get(request_url=request_url) == response_data
        assert app.cache_clear() is True
        assert app.cache_del() is True

    def test_pixabay(self) -> None:
        """Test Pixabay."""
        app = Pixabay(api_key=self.config.pixabay_key, dir_cache=self.dir_cache)

        keyword = "yellow flower"

        data_image = app.search_image(q=keyword)
        assert data_image != {}
        total, total_hits = app.parse_totals(response_data=data_image)
        assert total > 0 and total_hits > 0
        list_photo = list(app.parse_images(response_data=data_image))
        assert len(list_photo) > 0

        data_video = app.search_video(q=keyword)
        assert data_video != {}
        total, total_hits = app.parse_totals(response_data=data_video)
        assert total > 0 and total_hits > 0
        list_video = list(app.parse_videos(response_data=data_video))
        assert len(list_video) > 0

        assert app.cache_del() is True


if __name__ == "__main__":
    TestStock()
