"""
    Fake Data Generator like Fake Face API
    -- Fake Face API
    -- Fake Person Generator Bio Generator
        https://www.fakepersongenerator.com/user-biography-generator?new=refresh
"""

import os
from urllib.parse import urlencode

import requests
import regex as re

from pyatom import DIR_DEBUG
from pyatom.config import ConfigManager


__all__ = ("FakeFace",)


class FakeFace:
    """
    FakeFace for profile to posting
    """

    def __init__(self, user_agent: str, proxy_url: str) -> None:
        """Init FakeFace."""
        self.user_agent = user_agent
        self.proxy_url = proxy_url

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
            }

    def http_get(self, url: str) -> dict:
        """http get for response"""
        try:
            resp = self.session.get(url, timeout=30)
            if resp and resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    return data
        except requests.RequestException as err:
            print(err)
        return {}

    def generate(
        self, female: bool = True, age_min: int = 25, age_max: int = 35
    ) -> str:
        """Get random age, image"""
        gender = "female" if female else "male"
        params = {"gender": gender, "minimum_age": age_min, "maximum_age": age_max}
        base = "https://fakeface.rest/face/json?"
        url = f"{base}{urlencode(params)}"
        data = self.http_get(url)
        image_url = data.get("image_url") or ""
        if image_url and isinstance(image_url, str):
            image_name = os.path.basename(image_url)
            pattern = re.compile(r"(male|female)_([\d]+)_[\w]+?\.")
            found = pattern.findall(image_name)
            if found:
                return image_url

        return ""


class TestFake:
    """TestCase for FakeFace."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    def test_fakeface(self) -> None:
        """Test FakeFace."""
        app = FakeFace(
            user_agent=self.config.user_agent, proxy_url=self.config.proxy_url
        )
        image_url = app.generate()
        assert image_url != ""


if __name__ == "__main__":
    TestFake()
