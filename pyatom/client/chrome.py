# pylint: disable=too-many-lines

"""Chrome Devtools Wrapper.

    Reference:
    - `https://chromedevtools.github.io/devtools-protocol/`
    - `https://github.com/ClericPy/ichrome`
    - `https://github.com/marty90/PyChromeDevTools`
    - `https://github.com/pyppeteer/pyppeteer`
    - `https://github.com/ultrafunkamsterdam/undetected-chromedriver`

    Resource:
    - `https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md`
    - `https://peter.sh/experiments/chromium-command-line-switches/`

    Features:
    ToDo:
    - Device data

"""

from __future__ import annotations
import json
import time
import gc
import stat
import socket
import platform
import random
import string
from abc import ABC
from pathlib import Path
from subprocess import Popen, DEVNULL, STDOUT, check_output, TimeoutExpired
from dataclasses import dataclass
from typing import Optional, Any, Callable

import requests
import websocket
import psutil
import regex as re
import pytest

from pyatom.base.chars import str_rnd
from pyatom.base.io import IO
from pyatom.base.proxy import Proxy
from pyatom.base.log import Logger, init_logger
from pyatom.base.structure import Address
from pyatom.base.debug import Debugger
from pyatom.config import ConfigManager
from pyatom.app.downloader import Downloader as HttpDownloader
from pyatom.config import DIR_DEBUG


__all__ = (
    "Desktop",
    "Mobile",
    "Downloader",
    "Launcher",
    "Dev",
    "Chrome",
    "Address",
)


@dataclass
class Device(ABC):
    """Abstract Device for Browser FingerPrint."""

    did: str

    headless: bool
    user_agent: str

    os_cpu: str
    os_name: str
    os_version: str
    concurrency: int

    fonts: list[str]
    languages: list[str]
    plugins: list[str]

    color_depth: int
    viewport: tuple[int, int]

    session_storage: bool
    local_storage: bool
    indexed_db: bool

    device_memory: float


@dataclass
class Desktop(Device):
    """Desktop."""

    @property
    def is_windows(self) -> bool:
        """Is Windows."""
        print(self)
        return True

    @property
    def is_mac(self) -> bool:
        """Is Mac."""
        print(self)
        return True


@dataclass
class Mobile(Device):
    """Mobile."""

    flight_mode: bool

    @property
    def is_android(self) -> bool:
        """Is Android."""
        print(self)
        return True

    @property
    def is_ios(self) -> bool:
        """Is ios."""
        print(self)
        return True


def executable(dir_chrome: Path, chrome_version: str) -> Path:
    """Get file path for current env executable."""
    return dir_chrome / "install" / chrome_version / "chrome-linux" / "chrome"


def available(chrome_exe: Path, retry: int = 3) -> bool:
    """Check available of executable file."""
    for _ in range(retry):
        try:
            out = check_output([chrome_exe, "--version"], timeout=2)
            if out and out.startswith(b"Chromium"):
                return True
        except (FileNotFoundError, TimeoutExpired):
            continue
    return False


class Downloader:
    """Chrome Downloader.

    Support `Linux` Only as of 2022-02-18
    Latest Chromium Revision: `https://github.com/puppeteer/puppeteer/blob/main/src/revisions.ts`

    """

    def __init__(
        self,
        dir_chrome: Path,
        chrome_version: str,
        logger: Logger,
        user_agent: str = "",
        proxy_url: str = "",
    ) -> None:
        """Init Chrome Downloader."""

        self.dir_chrome = dir_chrome
        self.chrome_version = chrome_version
        self.logger = logger
        self.dir_install = self.dir_chrome / "install"
        IO.dir_create(self.dir_install)

        self.http = HttpDownloader(
            user_agent=user_agent, proxy_url=proxy_url, logger=self.logger
        )

    def show_versions(self) -> list[dict]:
        """Get Latest version of chromium. current using linux beta version `961656`."""
        os_name = platform.system().lower()
        url = "https://omahaproxy.appspot.com/all.json"
        with self.http.session.get(url, timeout=30) as response:
            if response and response.status_code == 200:
                data = response.json()
                assert isinstance(data, list) and isinstance(data[0], dict)
                for item in data:
                    if item.get("os") == os_name:
                        versions = item.get("versions", [])
                        assert isinstance(versions, list) and isinstance(
                            versions[0], dict
                        )
                        return versions
        return []

    @property
    def os_prefix(self) -> str:
        """Get platform info."""
        os_name = platform.system()
        if os_name == "Linux":
            is_x64 = bool(platform.architecture()[0] == "64bit")
            return os_name if not is_x64 else os_name + "_x64"
        raise SystemError(f"not supported yet: {os_name}")

    def remote_url(self, chrome_version: str = "") -> str:
        """Get download url."""
        chrome_version = chrome_version or self.chrome_version
        base = "https://storage.googleapis.com/chromium-browser-snapshots"
        return f"{base}/{self.os_prefix}/{chrome_version}/chrome-linux.zip"

    def download_exe(self, chrome_version: str = "") -> bool:
        """Dwonload executable file."""
        chrome_version = chrome_version or self.chrome_version
        url = self.remote_url(chrome_version)
        data = self.http.download_bytes(url=url)
        self.http.unzip(data, self.dir_install / chrome_version)
        exe = executable(self.dir_chrome, chrome_version)
        exe.chmod(exe.stat().st_mode | stat.S_IXOTH | stat.S_IXGRP | stat.S_IXUSR)
        return exe.is_file()

    @staticmethod
    def _gen_random_cdc() -> bytes:
        """Generate random cdc_asdjflasutopfhvcZLmcfl_ string."""
        cdc = random.choices(string.ascii_lowercase, k=26)
        cdc[-6:-4] = map(str.upper, cdc[-6:-4])
        cdc[2] = cdc[0]
        cdc[3] = "_"
        return "".join(cdc).encode()

    @staticmethod
    def _patch(chrome_exe: Path) -> bool:
        """Patch for executable bytes, maybe for selenium chromedriver?"""
        if chrome_exe.is_file():
            with open(chrome_exe, "rb") as file:
                # do some replacement to file
                print(file)
                return True
        return False

    @staticmethod
    def _is_patched(chrome_exe: Path) -> bool:
        """Check if executable has been patched.

        Seems not correct @ 2022-02-22

        """
        index = 0
        pattern = re.compile(rb"cdc_[\w]+")
        with open(chrome_exe, "rb") as file:
            for line in file:
                found = pattern.findall(line)
                if found:
                    index += 1
                    print(f"<{index}>{found[0]}")
        return index == 0

    def _cleanup_default(self) -> bool:
        """Cleanup default chrome version."""
        return IO.dir_del(self.dir_install / self.chrome_version)

    def _cleanup_all(self) -> bool:
        """Cleanup all chrome version."""
        return IO.dir_del(self.dir_install, remain_root=True)

    def _cleanup_only(self, chrome_version: str) -> bool:
        """Clean only this chrome version."""
        return IO.dir_del(self.dir_install / chrome_version)

    def _cleanup_others(self, chrome_version: str) -> bool:
        """Cleanup others except this chrome version."""
        for item in self.dir_install.iterdir():
            if item.is_dir() and chrome_version not in item.name:
                IO.dir_del(item)
        return all(
            chrome_version in item.name
            for item in self.dir_install.iterdir()
            if item.is_dir()
        )

    def cleanup(self, chrome_version: str = "", all_others: bool = False) -> bool:
        """Cleanup chrome install.

        Options:
        - chrome_version and all_others is False -> clean up this version;
        - chrome_version and all_others is True -> clean up others except this version;
        - no chrome_version and all_others is False -> clean up default version;
        - no chrome_version and all_others is True -> clean up all version;

        """
        if chrome_version:
            if all_others:
                return self._cleanup_others(chrome_version)
            return self._cleanup_only(chrome_version)

        if all_others:
            return self._cleanup_all()
        return self._cleanup_default()


class Launcher:
    """Chrome Launcher."""

    default_args: list[str] = [
        "--aggressive-cache-discard",
        "--aggressive-tab-discard",
        "--autoplay-policy=user-gesture-required",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-breakpad",
        "--disable-browser-side-navigation",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-device-discovery-notifications",
        "--disable-domain-reliability",
        "--disable-extensions",
        "--disable-features=site-per-process",
        "--disable-gpu",
        "--disable-hang-monitor",
        "--disable-login-animations",
        "--disable-notifications",
        "--disable-popup-blocking",
        "--disable-print-preview",
        "--disable-prompt-on-repost",
        "--disable-remote-fonts",
        "--disable-sync",
        "--disable-system-font-check",
        "--disable-translate",
        "--enable-automation",
        "--metrics-recording-only",
        "--no-default-browser-check",
        "--no-service-autorun",
        "--no-zygote",
        "--password-store=basic",
        "--safebrowsing-disable-auto-update",
        "--single-process",
        "--use-fake-device-for-media-stream",
        "--use-mock-keychain",
    ]

    def __init__(
        self,
        chrome_exe: Path,
        port: int,
        device: Device,
        dir_profile: Path,
        logger: Logger,
        proxy: Optional[Proxy] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """Init Chrome Launcher."""
        self.chrome_exe = chrome_exe
        self.port = port
        self.device = device
        self.dir_profile = dir_profile
        self.logger = logger
        self.proxy = proxy
        self.debug = debug

        IO.dir_create(self.dir_profile)

        self.host = "127.0.0.1"
        self.url = f"http://{self.host}:{port}"

        self.ready = False
        self.proc: Popen

        self.kwargs: dict[str, Any] = kwargs

        self.timeout = kwargs.get("timeout", 3)
        self.auto_close = kwargs.get("auto_close", True)
        self.ignore_https_errors = kwargs.get("ignore_https_errors", False)
        self.retry = kwargs.get("retry", 30)

    def to_args(self) -> list[str]:
        """Get chrome args to launch."""
        chrome_args: list[str] = [
            str(self.chrome_exe),
            f"--remote-debugging-address={self.host}",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.dir_profile}",
        ]

        ignore_default_args = self.kwargs.get("ignore_default_args", False)
        disable_image = self.kwargs.get("disable_image", False)
        extra_args = self.kwargs.get("extra_args", ["--no-first-run", "--no-sandbox"])
        incognito = self.kwargs.get("incognito", False)
        start_url = self.kwargs.get("start_url", "about:blank")

        if self.device.headless:
            chrome_args.extend(("--headless", "--hide-scrollbars", "--mute-audio"))
        if self.device.user_agent:
            chrome_args.append(f"--user-agent='{self.device.user_agent}'")
        if self.proxy:
            chrome_args.append(f"--proxy-server={self.proxy.server}")
        if disable_image:
            chrome_args.append("--blink-settings=imagesEnabled=false")
        if extra_args:
            chrome_args.extend(extra_args)
        if incognito:
            chrome_args.append("--incognito")
        if not ignore_default_args:
            chrome_args.extend(self.default_args)

        width, height = self.device.viewport
        chrome_args.append(f"--window-size={width},{height}")
        chrome_args.append(start_url)
        return chrome_args

    def cleanup_data_dir(self, remain_root: bool = False) -> bool:
        """Cleanup temp user data dir."""
        return IO.dir_del(self.dir_profile, remain_root=remain_root)

    def _start_process(self) -> None:
        """Start chrome process."""
        stdout, stderr = None, None
        if self.debug:
            stdout, stderr = DEVNULL, STDOUT
        self.proc = Popen(  # pylint: disable=R1732
            args=self.to_args(), shell=False, stdout=stdout, stderr=stderr
        )

    @property
    def proc_ok(self) -> bool:
        """Check if process okay."""
        for _ in range(int(self.retry)):
            if self.proc and self.proc.poll() is None:
                return True
            time.sleep(0.5)
        return False

    @property
    def connection_ok(self) -> bool:
        """Check if connection okay."""
        for _ in range(int(self.retry)):
            try:
                resp = requests.get(self.url, timeout=self.timeout)
                if resp and resp.ok:
                    self.ready = True
                    return True
            except requests.RequestException:
                pass
            time.sleep(0.5)
        return False

    @property
    def okay(self) -> bool:
        """Okay."""
        return self.proc_ok and self.connection_ok

    def start(self) -> bool:
        """Start process of chrome executable."""
        self._start_process()
        if self.okay:
            return True

        self.logger.error("chrome start failed: %d", self.port)
        return False

    def kill(self) -> bool:
        """Kill process of chrome executable."""
        self.ready = False
        for _ in range(self.retry):
            if self.proc.poll() is None:
                try:
                    self.proc.kill()
                    self.proc.wait(timeout=self.timeout)
                except TimeoutExpired:
                    parent = psutil.Process(self.proc.pid)
                    for child in parent.children(recursive=True):
                        child.kill()
                    parent.kill()

                time.sleep(0.5)

        return self.proc.poll() is not None


class ChromeElement:
    """Generic Chrome Element."""

    def __init__(self, name: str, parent: Dev) -> None:
        """Init Chrome Element."""
        self.name = name
        self.parent = parent
        print(f"self.name = {self.name}")
        print(f"self.parent = {self.parent}")

    def __getattr__(self, attr: str) -> Callable:
        """Get attr."""
        func_name = "{}.{}".format(self.name, attr)
        print(f"func_name = {func_name}")

        def generic_function(**args: Any) -> tuple[dict, list[dict]]:
            """Generic function."""
            if not self.parent.wsk:
                self.parent.logger.error("websocket not connected.")
                return {}, []

            self.parent.pop_messages()
            self.parent.message_counter += 1
            message_id = self.parent.message_counter
            call_obj = {"id": message_id, "method": func_name, "params": args}
            print(f"call_obj = {call_obj}")
            self.parent.wsk.send(json.dumps(call_obj))
            result, messages = self.parent.wait_result(message_id)
            return result, messages

        return generic_function


class Dev:
    """Chrome Devtools Protocol Wrapper."""

    message_counter = 0

    def __init__(
        self,
        port: int,
        logger: Logger,
        timeout: int = 1,
        retry: int = 30,
        auto_connect: bool = True,
    ):
        """Init Chrome Devtools Protocol Wrapper."""
        self.host = "127.0.0.1"

        self.port = port
        self.logger = logger
        self.timeout = timeout
        self.retry = retry

        self.wsk: Optional[websocket.WebSocket] = None
        self.tabs: list[dict] = []

        if auto_connect:
            self.connect_tab()

    def get_tabs(self) -> bool:
        """Get live tabs."""
        response = requests.get(f"http://{self.host}:{self.port}/json")
        self.tabs = json.loads(response.text)
        return len(self.tabs) > 0

    def connect_tab(self, index: int = 0, update: bool = True) -> bool:
        """Connect."""
        if update or not self.tabs:
            self.get_tabs()

        ws_url = self.tabs[index]["webSocketDebuggerUrl"]
        self.close()
        self.wsk = websocket.create_connection(ws_url)
        self.wsk.settimeout(self.timeout)
        return self.wsk is not None

    def connect_target(self, target_id: int) -> bool:
        """Connect target."""
        try:
            ws_url = f"ws://{self.host}:{self.port}/devtools/page/{target_id}"
            self.close()
            self.wsk = websocket.create_connection(ws_url)
            self.wsk.settimeout(self.timeout)
            return True
        except websocket.WebSocketException:
            ws_url = self.tabs[0]["webSocketDebuggerUrl"]
            self.wsk = websocket.create_connection(ws_url)
            self.wsk.settimeout(self.timeout)
            return False

    def close(self, retry: int = 30) -> bool:
        """Close."""
        retry = retry or self.retry
        for _ in range(retry):
            if self.wsk and not self.closed:
                self.wsk.close()
                time.sleep(0.5)

        return self.closed

    @property
    def closed(self) -> bool:
        """Check if self.wsk closed."""
        return bool(
            not self.wsk or self.wsk.sock is None and self.wsk.connected is False
        )

    # Blocking
    def wait_message(self, timeout: int = 0) -> dict:
        """Wait for message."""
        if not self.wsk:
            self.logger.error("websocket not connected.")
            return {}

        timeout = timeout or self.timeout
        self.wsk.settimeout(timeout)

        try:
            message = self.wsk.recv()
            parsed_message = json.loads(message)
            if isinstance(parsed_message, dict):
                return parsed_message
        except json.JSONDecodeError:
            pass
        return {}

    # Blocking
    def wait_event(self, event: str, timeout: int = 0) -> tuple[dict, list[dict]]:

        """Wait for event."""
        if not self.wsk:
            self.logger.error("websocket not connected.")
            return {}, []

        timeout = timeout or self.timeout
        self.wsk.settimeout(timeout)

        start_time = time.time()
        messages = []
        matching_message: dict = {}
        while True:
            now = time.time()
            if now - start_time > timeout:
                break
            try:
                message = self.wsk.recv()
                parsed_message = json.loads(message)
                messages.append(parsed_message)
                if (
                    isinstance(parsed_message, dict)
                    and "method" in parsed_message
                    and parsed_message["method"] == event
                ):
                    matching_message = parsed_message
                    break
            except websocket.WebSocketTimeoutException:
                continue
            except json.JSONDecodeError:
                break
        return matching_message, messages

    # Blocking
    def wait_result(self, result_id: int, timeout: int = 0) -> tuple[dict, list[dict]]:
        """Wait for result."""
        if not self.wsk:
            self.logger.error("websocket not connected.")
            return {}, []

        timeout = timeout or self.timeout
        self.wsk.settimeout(timeout)

        start_time = time.time()
        messages: list[dict] = []
        matching_result: dict = {}
        while True:
            now = time.time()
            if now - start_time > timeout:
                break
            try:
                message = self.wsk.recv()
                parsed_message = json.loads(message)
                messages.append(parsed_message)
                if "result" in parsed_message and parsed_message["id"] == result_id:
                    matching_result = parsed_message
                    break
            except websocket.WebSocketTimeoutException:
                continue
            except json.JSONDecodeError:
                break
        return matching_result, messages

    # Non Blocking
    def pop_messages(self) -> list[dict]:
        """Pop messages."""
        if not self.wsk:
            self.logger.error("websocket not connected.")
            return []

        messages = []
        self.wsk.settimeout(0)
        while True:
            try:
                message = self.wsk.recv()
                messages.append(json.loads(message))
            except json.JSONDecodeError:
                break
        self.wsk.settimeout(self.timeout)
        return messages

    def __getattr__(self, attr: str) -> ChromeElement:
        """Get attr."""
        element = ChromeElement(name=attr, parent=self)
        self.__setattr__(attr, element)
        return element


class Chrome:
    """Chrome Browser.

    manage chrome download, launch, browser, page, tab, etc.

    """

    def __init__(
        self,
        dir_chrome: Path,
        chrome_version: str,
        logger: Logger,
        debugger: Optional[Debugger] = None,
    ):
        """Init Chrome."""
        self.dir_chrome = dir_chrome
        self.chrome_version = chrome_version
        self.logger = logger
        self.debugger = debugger

        self.data: dict = {"time_stamp": 0, "time_str": "", "req": {}, "res": {}}

        self.launcher: Launcher
        self.dev: Dev

    @staticmethod
    def get_free_port() -> int:
        """Get Free Port."""
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        del sock
        gc.collect()
        return int(port)

    @staticmethod
    def init_device(  # pylint: disable=too-many-locals
        debug: bool = False, mobile: bool = False, **kwargs: Any
    ) -> Device:
        """Init device."""
        did = kwargs.get("did", "did" if debug else str_rnd())
        headless = kwargs.get("headless", True)
        user_agent = kwargs.get("user_agent", "")
        os_cpu = kwargs.get("os_cpu", "")
        os_name = kwargs.get("os_name", "")
        os_version = kwargs.get("os_version", "")
        concurrency = kwargs.get("concurrency", 1)
        fonts = kwargs.get("fonts", [])
        languages = kwargs.get("languages", [])
        plugins = kwargs.get("plugins", [])
        color_depth = kwargs.get("color_depth", 24)
        viewport = kwargs.get("viewport", (1920, 1080))
        session_storage = kwargs.get("session_storage", True)
        local_storage = kwargs.get("local_storage", True)
        indexed_db = kwargs.get("indexed_db", True)
        device_memory = kwargs.get("device_memory", 0)
        flight_mode = kwargs.get("flight_mode", False)
        if mobile:
            return Mobile(
                did=did,
                headless=headless,
                user_agent=user_agent,
                os_cpu=os_cpu,
                os_name=os_name,
                os_version=os_version,
                concurrency=concurrency,
                fonts=fonts,
                languages=languages,
                plugins=plugins,
                color_depth=color_depth,
                viewport=viewport,
                session_storage=session_storage,
                local_storage=local_storage,
                indexed_db=indexed_db,
                device_memory=device_memory,
                flight_mode=flight_mode,
            )
        return Desktop(
            did=did,
            headless=headless,
            user_agent=user_agent,
            os_cpu=os_cpu,
            os_name=os_name,
            os_version=os_version,
            concurrency=concurrency,
            fonts=fonts,
            languages=languages,
            plugins=plugins,
            color_depth=color_depth,
            viewport=viewport,
            session_storage=session_storage,
            local_storage=local_storage,
            indexed_db=indexed_db,
            device_memory=device_memory,
        )

    def load_device(self, device_id: str) -> Device:
        """Load device data."""
        print(self, device_id)
        raise NotImplementedError

    def save_device(self, device: Device) -> bool:
        """Save device data."""
        print(self, device)
        raise NotImplementedError

    def ensure_install(self) -> bool:
        """Ensure chrome installed."""
        print(self)
        return True

    def launch_exe(self) -> bool:
        """Launch new chrome process."""
        print(self)
        return True

    def connect_dev(self) -> bool:
        """Connect to chrome devtools protocol."""
        print(self)
        return True

    def to_dir_install(self) -> Path:
        """Get dir_install."""
        return self.dir_chrome / "install"

    def to_dir_profile(self, device: Device) -> Path:
        """Get dir_profile."""
        return self.dir_chrome / "profile" / device.did

    def header_set(self, key: str, value: str) -> bool:
        """Set http header for chrome browser."""
        print(self, key, value)
        return True

    def cookie_load(self) -> bool:
        """Load cookie for chrome browser."""
        print(self)
        return True

    def cookie_set(self, key: str, value: str) -> bool:
        """Set cookie for chrome browser."""
        print(self, key, value)
        return True

    def cookie_save(self) -> bool:
        """Save cookie into local file."""
        print(self)
        return True

    def req(self, method: str, url: str, **kwargs: Any) -> None:
        """Issue http requests."""
        print(self, method, url, kwargs)

    def get(self, url: str, **kwargs: Any) -> None:
        """Http GET."""
        return self.req(method="GET", url=url, kwargs=kwargs)

    def device_validate(self) -> bool:
        """Validate device attributes."""
        print(self)
        return True

    def device_spoof(self) -> bool:
        """Spoof device attributes."""
        print(self)
        return True

    def _get_device_os_cpu(self) -> str:
        """Get device os cpu string."""

    def _set_device_os_cpu(self) -> bool:
        """Set device os cpu string."""

    def _get_device_os_name(self) -> str:
        """Get device os name string."""

    def _get_device_os_version(self) -> str:
        """Get device os version string."""

    def _get_device_concurrency(self) -> int:
        """Get device hard concurrency."""

    def _get_device_fonts(self) -> list[str]:
        """Get device fonts."""

    def _get_device_languages(self) -> list[str]:
        """Get device languages."""

    def _get_device_plugins(self) -> list[str]:
        """Get device plugins."""

    def _get_device_color_depth(self) -> int:
        """Get device color depth."""

    def _get_device_viewport(self) -> tuple[int, int]:
        """Get device viewport."""

    def _get_device_session_storage(self) -> bool:
        """Get device session storage."""

    def _get_device_local_storage(self) -> bool:
        """Get device local storage."""

    def _get_device_indexed_db(self) -> bool:
        """Get device indexed_db."""

    def _get_device_memory(self) -> float:
        """Get device memory."""


class TestChrome:
    """Test Chrome."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")
    debugger = Debugger(path=DIR_DEBUG, name="test")

    dir_chrome = DIR_DEBUG / "chrome"

    def to_device(self) -> Device:
        """Generate device for testing."""
        return Device(
            did="did",
            headless=True,
            user_agent=self.config.user_agent,
            os_cpu="",
            os_name="",
            os_version="",
            concurrency=8,
            fonts=[],
            languages=[],
            plugins=[],
            color_depth=24,
            viewport=(1920, 1080),
            session_storage=True,
            local_storage=True,
            indexed_db=True,
            device_memory=1024 * 1024 * 1024,
        )

    @pytest.mark.skip(reason="pass")
    def test_dir_start(self) -> None:
        """Prepare dir_chrome."""
        IO.dir_create(self.dir_chrome)

    @pytest.mark.skip(reason="pass")
    def test_downloader(self) -> None:
        """Test chrome downloader."""
        # test version select, save into config, etc.
        app = Downloader(
            user_agent=self.config.user_agent,
            proxy_url=self.config.proxy_url,
            dir_chrome=self.dir_chrome,
            chrome_version=self.config.chrome_version,
            logger=self.logger,
        )
        print(app.os_prefix)
        print(app.remote_url())
        #  assert app.download_exe()
        chrome_exe = executable(self.dir_chrome, self.config.chrome_version)
        assert chrome_exe.is_file()
        assert available(chrome_exe=chrome_exe)

    @pytest.mark.skip(reason="pass")
    def test_launcher(self) -> None:
        """Test chrome launcher."""
        chrome_exe = executable(self.dir_chrome, self.config.chrome_version)
        device = self.to_device()
        dir_profile = self.dir_chrome / self.config.chrome_version / device.did
        proxy = Proxy.load(url=self.config.proxy_url)
        app = Launcher(
            chrome_exe=chrome_exe,
            port=9222,
            device=device,
            dir_profile=dir_profile,
            logger=self.logger,
            proxy=proxy,
        )
        assert app.start()
        print(f"app.porc = {app.proc}")
        assert app.kill()
        print(f"app.porc = {app.proc}")

    @pytest.mark.skip(reason="pass")
    def test_dev(self) -> None:
        """Test chrome dev."""
        chrome_exe = executable(self.dir_chrome, self.config.chrome_version)
        device = self.to_device()
        dir_profile = self.dir_chrome / self.config.chrome_version / device.did
        proxy = Proxy.load(url=self.config.proxy_url)
        app = Launcher(
            chrome_exe=chrome_exe,
            port=9222,
            device=device,
            dir_profile=dir_profile,
            logger=self.logger,
            proxy=proxy,
        )
        assert app.start()
        print(f"app.proc = {app.proc}")
        # test devtools to browser, page, tab operation.
        dev = Dev(port=9222, logger=self.logger)
        assert dev.get_tabs()
        assert dev.connect_tab()
        assert dev.close()

        assert app.kill()

    def test_chrome(self) -> None:
        """Test chrome."""
        # test cookies, headers, requests, debugger save data, device fingerprints, etc.
        app = Chrome(
            dir_chrome=self.dir_chrome,
            chrome_version=self.config.chrome_version,
            logger=self.logger,
            debugger=self.debugger,
        )
        chrome_exe = executable(self.dir_chrome, self.config.chrome_version)
        port = 9222
        device = self.to_device()
        dir_profile = self.dir_chrome / self.config.chrome_version / device.did
        proxy = Proxy.load(url=self.config.proxy_url)
        app.launcher = Launcher(
            chrome_exe=chrome_exe,
            port=port,
            device=device,
            dir_profile=dir_profile,
            logger=self.logger,
            proxy=proxy,
        )
        assert app.launcher.start()
        print(f"launcher.proc = {app.launcher.proc}")

        app.dev = Dev(port=port, logger=self.logger)
        assert app.dev.get_tabs()
        assert app.dev.connect_tab()
        try:
            app.dev.Network.enable()
        except Exception as err:  # pylint: disable=W0703
            print(err)

        #  app.dev.Page.enable()
        #  start_time = time.time()
        #  app.dev.Page.navigate(url="https://www.bing.com/")
        #  app.dev.wait_event("Page.loadEventFired", timeout=60)
        #  end_time = time.time()
        #  print("Page Loading Time:", end_time - start_time)

        assert app.dev.close()

        assert app.launcher.kill()

    def _test_dir_end(self) -> None:
        """Delete dir_chrome."""
        IO.dir_del(self.dir_chrome)


if __name__ == "__main__":
    TestChrome()
