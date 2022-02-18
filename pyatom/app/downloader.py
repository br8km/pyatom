# -*- coding: utf-8 -*-

"""
    cls for File/Image Downloading.
"""

import os
from pathlib import Path
from typing import Union, Optional

import requests
from requests import Response
from tqdm import tqdm

from pyatom.base.io import dir_create, file_del
from pyatom.base.log import Logger, init_logger
from pyatom.config import ConfigManager


__all__ = ("DownLoader",)


class DownLoader:
    """
    Resumable Http Downloader for Large/Medium/Small File
    """

    def __init__(self, user_agent: str, proxy_str: str, logger: Logger) -> None:
        """Init downloader."""
        self.user_agent = user_agent
        self.proxy_str = proxy_str
        self.logger = logger

        self.session = requests.Session()
        if user_agent:
            self.session.headers.update({"User-Agent": user_agent})
        if proxy_str:
            self.session.proxies = {
                "http": f"http://{proxy_str}",
                "https": f"http://{proxy_str}",
            }

    def _head(self, file_url: str) -> Optional[Response]:
        """Head Request"""
        response = self.session.head(file_url, timeout=30)
        return response if isinstance(response, Response) else None

    @staticmethod
    def _has_range(response: Response) -> bool:
        """Check if accept range from response headers"""
        key_range = "Accept-Ranges"
        return bool(key_range in response.headers.keys())

    @staticmethod
    def _file_size(response: Response) -> int:
        """Parse file size from response headers"""
        return int(response.headers.get("Content-Length", 0))

    def download_direct(
        self, file_url: str, file_out: Union[Path, str], chunk_size: int = 1024
    ) -> bool:
        """Download In One Shot"""
        with self.session.get(file_url, stream=True) as response:
            response.raise_for_status()
            total_size = self._file_size(response)
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
            with open(file_out, "wb") as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    file.flush()
                    progress_bar.update(len(chunk))

                return os.stat(file_out).st_size == total_size

    def _resume_download(
        self, file_url: str, start_pos: int, end_pos: int = 0
    ) -> Response:
        """
        Resume download
        Parameters:
            :start_pos:int, start position of range
            :end_pos:int, end position of range, empty if zero
        """
        _range = f"bytes={start_pos}-"
        if end_pos:
            _range = f"range{end_pos}"
        self.session.headers["Range"] = _range
        return self.session.get(file_url, stream=True)

    def download_ranges(
        self,
        file_url: str,
        file_out: Union[Path, str],
        total_size: int = 0,
        start_pos: int = 0,
        chunk_size: int = 1024,
        block_size: int = 1024 * 1024,
    ) -> bool:
        """
        Downloading By Ranges
        Steps:
            :check local file exists/size
            :get start_pos/end_pos
            :resume_download
            :append new chunk to file if present
        """
        file_del(file_out)

        if not total_size:
            # http head method to get response headers
            response = self._head(file_url)
            if response is None:
                self.logger.error("file size error!")
                return False

            total_size = self._file_size(response)
            if not total_size:
                self.logger.error("file size error!")
                return False

        progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)

        with open(file_out, "ab+") as file:
            while True:
                file_size = os.stat(file_out).st_size
                if file_size >= total_size:
                    break

                end_pos = start_pos + block_size

                with self._resume_download(
                    file_url=file_url, start_pos=start_pos, end_pos=end_pos
                ) as response:
                    # maybe error if end_pos > content size?
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        file.write(chunk)
                        file.flush()
                        progress_bar.update(len(chunk))

                start_pos = end_pos

        return os.stat(file_out).st_size == total_size

    def download(self, file_url: str, file_out: Union[Path, str]) -> bool:
        """Smart Download"""

        dir_create(Path(file_out).parent)

        response = self._head(file_url)
        if response is None:
            return False

        total_size = self._file_size(response)
        if not total_size:
            self.logger.error("file size error!")
            return False

        if self._has_range(response):
            return self.download_ranges(
                file_url=file_url, file_out=file_out, total_size=total_size
            )
        return self.download_direct(file_url=file_url, file_out=file_out)


class TestDownloader:
    """Test Downloader."""

    dir_app = Path(__file__).parent
    file_config = Path(dir_app.parent.parent, "protect", "config.json")
    config = ConfigManager().load(file_config)

    def test_downloader(self) -> None:
        """test downloader by direct or ranges downloading"""
        app = DownLoader(
            user_agent=self.config.user_agent,
            proxy_str=self.config.proxy_str,
            logger=init_logger(name="test"),
        )

        # url accept ranges
        file_url_ranges = "http://ipv4.download.thinkbroadband.com/10MB.zip"
        file_url_ranges = "http://s3.amazonaws.com/alexa-static/top-1m.csv.zip"

        file_tmp = Path(self.dir_app, "ranges.tmp")
        assert app.download_ranges(file_url=file_url_ranges, file_out=file_tmp)
        file_del(file_tmp)
        assert file_tmp.is_file() is False

        file_url_direct = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"
        file_url_direct = "https://raw.githubusercontent.com/ableco/test-files/master/images/test-image-png_4032x3024.png"
        file_tmp = Path(self.dir_app, "direct.tmp")
        assert app.download_direct(file_url=file_url_direct, file_out=file_tmp)
        file_del(file_tmp)
        assert file_tmp.is_file() is False


if __name__ == "__main__":
    TestDownloader()
