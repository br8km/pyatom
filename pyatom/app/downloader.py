# -*- coding: utf-8 -*-

"""
    cls for File/Image Downloading.
"""

import os
from pathlib import Path
from typing import Union, Optional
from io import BytesIO
from zipfile import ZipFile

import requests
from requests import Response
from tqdm import tqdm

from pyatom.base.io import IO
from pyatom.base.log import Logger, init_logger
from pyatom import DIR_DEBUG
from pyatom.config import ConfigManager


__all__ = ("Downloader",)


class Downloader:
    """
    Resumable Http Downloader for Large/Medium/Small File
    """

    def __init__(self, user_agent: str, proxy_url: str, logger: Logger) -> None:
        """Init downloader."""
        self.user_agent = user_agent
        self.proxy_url = proxy_url
        self.logger = logger

        self.session = requests.Session()
        if user_agent:
            self.session.headers.update({"User-Agent": user_agent})
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https": proxy_url,
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
        try:
            return int(response.headers["content-length"])
        except (KeyError, ValueError, AttributeError):
            return 0

    def download_direct(
        self, file_url: str, file_out: Union[Path, str], chunk_size: int = 1024
    ) -> bool:
        """Download In One Shot"""
        with self.session.get(file_url, stream=True) as response:
            response.raise_for_status()
            total_size = self._file_size(response)
            with open(file_out, "wb") as file:
                progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    file.flush()
                    progress_bar.update(len(chunk))
                    progress_bar.refresh()
                progress_bar.close()

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
        IO.file_del(file_out)

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

        with open(file_out, "ab+") as file:
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
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
                        progress_bar.refresh()

                start_pos = end_pos

            progress_bar.close()

        return os.stat(file_out).st_size == total_size

    def download(self, file_url: str, file_out: Union[Path, str]) -> bool:
        """Smart Download"""

        IO.dir_create(Path(file_out).parent)

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

    def download_bytes(self, url: str, chunk_size: int = 1024) -> BytesIO:
        """Download bytes data."""
        with self.session.get(url, stream=True) as response:
            response.raise_for_status()
            total_size = self._file_size(response)
            progress_bar = tqdm(total=total_size, unit="iB", unit_scale=True)
            _data = BytesIO()
            for chunk in response.iter_content(chunk_size=chunk_size):
                _data.write(chunk)
                progress_bar.update(len(chunk))
                progress_bar.refresh()
            progress_bar.close()

            return _data

    @staticmethod
    def unzip(data: BytesIO, dir_to: Path) -> bool:
        """Unzip zipped bytes data into file path."""
        if not dir_to.exists():
            dir_to.mkdir(parents=True)
        with ZipFile(data) as file:
            file.extractall(str(dir_to.absolute()))

        return True


class TestDownloader:
    """Test Downloader."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    def test_downloader(self) -> None:
        """test downloader by direct or ranges downloading"""
        app = Downloader(
            user_agent=self.config.user_agent,
            proxy_url=self.config.proxy_url,
            logger=init_logger(name="test"),
        )

        # url accept ranges
        file_url_ranges = "http://ipv4.download.thinkbroadband.com/10MB.zip"
        file_url_ranges = "http://s3.amazonaws.com/alexa-static/top-1m.csv.zip"

        file_tmp = DIR_DEBUG / "ranges.tmp"
        assert app.download_ranges(file_url=file_url_ranges, file_out=file_tmp)
        file_tmp.unlink(missing_ok=True)
        assert file_tmp.is_file() is False

        file_url_direct = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png"
        file_url_direct = "https://raw.githubusercontent.com/ableco/test-files/master/images/test-image-png_4032x3024.png"
        file_tmp = DIR_DEBUG / "direct.tmp"
        assert app.download_direct(file_url=file_url_direct, file_out=file_tmp)
        file_tmp.unlink(missing_ok=True)
        assert file_tmp.is_file() is False

        # download bytes and unzip not tested yet as of 2022-02-24


if __name__ == "__main__":
    TestDownloader()
