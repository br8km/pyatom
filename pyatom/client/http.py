"""
    Doc string for browser client
        - http requests client
        - chrome headless anti-fingerprint browser client
"""

import os
from abc import ABC
from pathlib import Path
from typing import Any, Optional, Union

import arrow
import orjson
import requests
from requests import Response

from pyatom.base.io import load_dict, save_dict
from pyatom.base.debug import Debugger
from pyatom.base.log import Logger


__all__ = (
    "Http",
    "Chrome",
)


class BaseClient(ABC):
    """Base cls for Browser Client."""

    __slots__ = (
        "__dict__",
        "user_agent",
        "proxy_str",
        "time_out",
        "logger",
        "debugger",
        "data",
    )

    def __init__(
        self,
        user_agent: str,
        proxy_str: str,
        time_out: int,
        logger: Optional[Logger],
        debugger: Optional[Debugger],
    ) -> None:

        self.user_agent = user_agent
        self.proxy_str = proxy_str
        self.time_out = time_out

        self.logger = logger
        self.debugger = debugger

        self.data: dict = {"time_stamp": 0, "time_str": "", "req": {}, "res": {}}


class Http(BaseClient):
    """HTTP Client for requests"""

    def __init__(
        self,
        user_agent: str,
        proxy_str: str,
        time_out: int = 30,
        logger: Optional[Logger] = None,
        debugger: Optional[Debugger] = None,
    ) -> None:
        super().__init__(
            user_agent=user_agent,
            proxy_str=proxy_str,
            time_out=time_out,
            logger=logger,
            debugger=debugger,
        )

        self.session = requests.Session()

        if user_agent:
            headers = {"User-Agent": user_agent}
            self.session.headers.update(headers)

        if proxy_str:
            proxy_dict = {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}
            self.session.proxies = proxy_dict

    def header_set(self, key: str, value: Optional[str] = None) -> None:
        """set header for session"""
        if value is not None:
            self.session.headers[key] = value
        else:
            if key in self.session.headers.keys():
                del self.session.headers[key]

    def h_accept(self, value: str = "*/*") -> None:
        """set heaer `Accept`"""
        self.header_set("Accept", value)

    def h_encoding(self, value: str = "gzip, defalte, br") -> None:
        """set header `Accept-Encoding`"""
        self.header_set("Accept-Encoding", value)

    def h_lang(self, value: str = "en-US,en;q=0.5") -> None:
        """set header `Accept-Language`"""
        self.header_set("Accept-Language", value)

    def h_origin(self, value: Optional[str] = None) -> None:
        """set header `Origin`"""
        self.header_set("Origin", value)

    def h_refer(self, value: Optional[str] = None) -> None:
        """set header `Referer`"""
        self.header_set("Referer", value)

    def h_type(self, value: Optional[str] = None) -> None:
        """set header `Content-Type`"""
        self.header_set("Content-Type", value)

    def h_xml(self, value: str = "XMLHttpRequest") -> None:
        """set header `X-Requested-With`"""
        self.header_set("X-Requested-With", value)

    def h_data(self, utf8: bool = True) -> None:
        """set header `Content-Type` for form data submit"""
        value = "application/x-www-form-urlencoded"
        if utf8 is True:
            value = f"{value}; charset=UTF-8"
        self.header_set("Content-Type", value)

    def h_json(self, utf8: bool = True) -> None:
        """set header `Content-Type` for json payload post"""
        value = "application/json"
        if utf8 is True:
            value = f"{value}; charset=UTF-8"
        self.header_set("Content-Type", value)

    def cookie_set(self, key: str, value: Optional[str]) -> None:
        """set cookie for session"""
        self.session.cookies.set(key, value)

    def cookie_load(self, file_cookie: Union[str, Path]) -> None:
        """load session cookie from local file"""
        if os.path.isfile(file_cookie):
            cookie = load_dict(file_cookie)
            self.session.cookies.update(cookie)

    def cookie_save(self, file_cookie: Union[str, Path]) -> None:
        """save session cookies into local file"""
        save_dict(file_cookie, dict(self.session.cookies))

    def prepare_headers(self, **kwargs: Any) -> None:
        """set headers for following request"""
        if kwargs.get("json") is not None:
            self.h_json()
        elif kwargs.get("data") is not None:
            self.h_data()

        headers = kwargs.get("headers")
        if headers is not None:
            for key, value in headers.items():
                self.header_set(key, value)

    def save_req(
        self, method: str, url: str, debug: bool = False, **kwargs: Any
    ) -> None:
        """save request information into self.data"""
        if debug and self.debugger:
            _kwargs = {}
            for key, value in kwargs.items():
                try:
                    orjson.dumps({"v": value})
                except TypeError:
                    value = str(value)
                _kwargs[key] = value

            cookies = dict(self.session.cookies.items())
            headers = dict(self.session.headers.items())
            now = arrow.now()
            time_stamp = int(now.timestamp())
            time_str = now.format("YYYY-MM-DD HH:mm:ss")
            self.data["time_stamp"] = time_stamp
            self.data["time_str"] = time_str
            self.data["req"] = {
                "method": method,
                "url": url,
                "kwargs": kwargs,
                "headers": headers,
                "cookies": cookies,
            }
            self.debugger.sid = self.debugger.sid_new()
            self.debugger.save(self.data)

    def save_res(self, response: Response, debug: bool = False) -> None:
        """save http response into self.data"""
        if debug and self.debugger:
            cookies = dict(response.cookies.items())
            headers = dict(response.headers.items())
            try:
                res_json = orjson.loads(response.text)
            except orjson.JSONDecodeError:
                res_json = {}
            self.data["res"] = {
                "status_code": response.status_code,
                "url": response.url,
                "headers": headers,
                "cookies": cookies,
                "text": response.text,
                "json": res_json,
            }
            # suppose debugger is already initialized.
            self.debugger.save(self.data)

    def req(
        self, method: str, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """Preform HTTP Request"""
        response = None
        try:
            self.prepare_headers(**kwargs)
            self.save_req(method, url, debug, **kwargs)
            if not kwargs.get("timeout", None):
                kwargs["timeout"] = self.time_out
            with self.session.request(method, url, **kwargs) as response:
                code = response.status_code
                length = len(response.text)
                message = f"[{code}]<{length}>{response.url}"
                if self.logger:
                    self.logger.info(message)
                self.save_res(response, debug)
                return response
        except requests.RequestException as err:
            if self.logger:
                self.logger.error(err)
        return response

    def get(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP GET"""
        return self.req("GET", url, debug=debug, **kwargs)

    def post(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP POST"""
        return self.req("POST", url, debug=debug, **kwargs)

    def head(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP HEAD"""
        return self.req("HEAD", url, debug=debug, **kwargs)

    def options(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP OPTIONS"""
        return self.req("OPTIONS", url, debug=debug, **kwargs)

    def connect(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP CONNECT"""
        return self.req("CONNECT", url, debug=debug, **kwargs)

    def put(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP PUT"""
        return self.req("PUT", url, debug=debug, **kwargs)

    def patch(self, url: str, debug: bool = False, **kwargs: Any) -> Optional[Response]:
        """HTTP PATCH"""
        return self.req("PATCH", url, debug=debug, **kwargs)

    def delete(
        self, url: str, debug: bool = False, **kwargs: Any
    ) -> Optional[Response]:
        """HTTP DELETE"""
        return self.req("DELETE", url, debug=debug, **kwargs)


class Chrome(BaseClient):
    """Chrome Browser Client."""

    def __init__(
        self,
        user_agent: str,
        proxy_str: str,
        time_out: int,
        logger: Optional[Logger],
        debugger: Optional[Debugger],
    ) -> None:
        super().__init__(
            user_agent=user_agent,
            proxy_str=proxy_str,
            time_out=time_out,
            logger=logger,
            debugger=debugger,
        )
