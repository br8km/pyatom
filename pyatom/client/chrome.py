"""
    Chrome Devtools Wrapper.

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

"""

import asyncio
import json
import time
import gc
import socket
import platform
from abc import ABC
from pathlib import Path
from subprocess import Popen, DEVNULL, STDOUT
from dataclasses import dataclass
from typing import Optional, Any, Callable, Union

import requests
import websocket


from pyatom.base.io import dir_create, dir_del
from pyatom.base.proxy import Proxy
from pyatom.base.log import Logger, init_logger
from pyatom.app.downloader import Downloader as AppDownloader
from pyatom.base.debug import Debugger
from pyatom.config import ConfigManager


__all__ = (
    "Desktop",
    "Tablet",
    "Mobile",
    "Downloader",
    "Launcher",
    "Dev",
    "Chrome",
)


@dataclass
class Viewport:
    """Viewport of chrome browser window size."""

    width: int
    height: int


@dataclass
class Device(ABC):
    """Abstract Device for Browser FingerPrint."""

    did: str

    user_agent: str
    proxy_str: str

    ip_addr: str
    incognito: bool

    os_cpu: str
    os_name: str
    os_version: str
    concurrency: int

    fonts: list[str]
    languages: list[str]
    plugins: list[str]

    color_depth: int
    screen_width: int
    screen_height: int

    session_storage: bool
    local_storage: bool
    indexed_db: bool

    device_memory: float

    def timezone(self) -> str:
        """Get time zone."""

    def browser(self) -> str:
        """Get browser name."""

    def browser_version(self) -> str:
        """Get browser version."""


@dataclass
class Desktop(Device):
    """Desktop."""


@dataclass
class Tablet(Device):
    """Tablet."""


@dataclass
class Mobile(Device):
    """Mobile."""

    flight_mode: bool
    battery: float


class Downloader(AppDownloader):
    """Chrome Downloader.

    Support `Linux` Only as of 2022-02-18

    """

    def __init__(
        self,
        user_agent: str,
        proxy_str: str,
        chrome_dir: Union[str, Path],
        chrome_version: str,
        logger: Logger,
    ) -> None:
        """Init Chrome Downloader."""
        super().__init__(user_agent=user_agent, proxy_str=proxy_str, logger=logger)

        if not dir_create(chrome_dir):
            raise OSError(f"directory created failed: {chrome_dir}")

        self.chrome_dir = Path(chrome_dir)
        self.chrome_version = chrome_version

        self.base = "https://storage.googleapis.com/chromium-browser-snapshots"

    @property
    def platform_name(self) -> str:
        """Get platform info."""
        os_name = platform.system()
        if not os_name == "Linux":
            raise SystemError(f"not supported yet: {os_name}")

        is_x64 = bool(platform.architecture()[0] == "64bit")
        return os_name if not is_x64 else os_name + "_x64"

    @staticmethod
    def show_versions() -> list[dict]:
        """Get Latest version of chromium."""
        os_name = platform.system().lower()
        url = "https://omahaproxy.appspot.com/all.json"
        with requests.get(url, timeout=30) as response:
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

    def latest_version(self) -> str:
        """Get Latest version string."""
        url = f"https://storage.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/{self.platform_name}%2FLAST_CHANGE?alt=media"
        with requests.get(url, timeout=30) as response:
            if response and response.text.isdigit():
                return response.text

        raise ValueError("check your connection to latest version url.")

    def remote_url(self, chrome_version: str = "") -> str:
        """Get download url."""
        chrome_version = chrome_version or self.chrome_version
        return f"{self.base}/{self.platform_name}/{chrome_version}/chrome_linux.zip"

    def download_exe(self, chrome_version: str = "") -> bool:
        """Dwonload executable file."""
        url = self.remote_url(chrome_version)
        data = self.download_bytes(url=url)
        return self.unzip(data, self.chrome_dir)

    def _patch(self, data: bytes) -> bytes:
        """Patch for executable bytes."""
        print(self, data)
        return data

    def executable(self, chrome_version: str = "") -> Path:
        """Get file path for current env executable."""
        chrome_version = chrome_version or self.chrome_version
        return self.chrome_dir / chrome_version / "chrome-linux" / "chrome"

    def exist(self, chrome_version: str = "") -> bool:
        """Check exist of executable file."""
        return self.executable(chrome_version).is_file()

    def cleanup(self, chrome_version: str = "") -> bool:
        """Cleanup chrome_dir."""
        if chrome_version:
            return dir_del(self.chrome_dir / chrome_version, remain_root=False)
        return dir_del(self.chrome_dir, remain_root=True)


class Launcher:
    """Chrome Launcher."""

    default_args: list[str] = [
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-breakpad",
        "--disable-browser-side-navigation",
        "--disable-client-side-phishing-detection",
        "--disable-default-apps",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--disable-features=site-per-process",
        "--disable-hang-monitor",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--disable-translate",
        "--metrics-recording-only",
        "--safebrowsing-disable-auto-update",
        "--enable-automation",
        "--password-store=basic",
        "--use-mock-keychain",
        "--disable-client-side-phishing-detection",
        "--disable-component-extensions-with-background-pages",
        "--no-default-browser-check",
        "--use-fake-device-for-media-stream",
        "--single-process",
        "--disable-login-animations",
        "--disable-notifications",
        "--disable-print-preview",
        "--disable-system-font-check",
        "--aggressive-cache-discard",
        "--aggressive-tab-discard",
        "--disable-domain-reliability",
        "--disable-component-update",
        "--disable-device-discovery-notifications",
        "--no-service-autorun",
        "--password-store=basic",
    ]

    def __init__(
        self,
        chrome_exe: Path,
        port: int,
        headless: bool,
        user_agent: str,
        proxy_str: str,
        user_data_dir: Path,
        logger: Logger,
        debugger: Optional[Debugger],
        **kwargs: Any,
    ) -> None:
        """Init Chrome Launcher."""
        self.chrome_exe = chrome_exe
        self.port = port

        self.headless = headless
        self.user_agent = user_agent
        self.proxy: Optional[Proxy] = Proxy(proxy_str=proxy_str) if proxy_str else None
        self.user_data_dir = user_data_dir
        dir_create(self.user_data_dir)

        self.logger = logger
        self.debugger = debugger

        self.host = "127.0.0.1"
        self.url = f"http://{self.host}:{port}"

        self.proc: Popen
        self.loop = kwargs.get("loop", asyncio.get_event_loop())

        self.kwargs: dict[str, Any] = kwargs

        self.auto_close = kwargs.get("auto_close", True)
        self.timeout = kwargs.get("timeout", 3)
        self.viewport = kwargs.get("viewport", Viewport(width=800, height=600))
        self.ignore_https_errors = kwargs.get("ignore_https_errors", False)
        self.max_connection_check = kwargs.get("max_connection_check", 15)

    def to_args(self) -> list[str]:
        """Get chrome args to launch."""
        chrome_args: list[str] = [
            str(self.chrome_exe),
            f"--remote-debugging-address={self.host}",
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={self.user_data_dir}",
        ]

        ignore_default_args = self.kwargs.get("ignore_default_args", False)
        devtools = self.kwargs.get("devtools", False)
        headless = self.kwargs.get("headless", not devtools)
        disable_image = self.kwargs.get("disable_image", False)
        extra_args = self.kwargs.get("extra_args", ["--no-first-run", "--no-sandbox"])
        incognito = self.kwargs.get("incognito", False)
        start_url = self.kwargs.get("start_url", "about:blank")

        if devtools:
            chrome_args.append("--auto-open-devtools-for-tabs")
        if headless:
            chrome_args.extend(("--headless", "--hide-scrollbars", "--mute-audio"))
        if self.user_agent:
            chrome_args.append(f"--user-agent={self.user_agent}")
        if self.proxy:
            chrome_args.append(f"--proxy-server={self.proxy.url}")
        if disable_image:
            chrome_args.append("--blink-settings=imagesEnabled=false")
        if extra_args:
            chrome_args.extend(extra_args)
        if incognito:
            chrome_args.append("--incognito")

        if not ignore_default_args:
            chrome_args.extend(self.default_args)

        width, height = self.viewport.width, self.viewport.height
        chrome_args.append(f"--window-size={width},{height}")
        chrome_args.append(start_url)
        return chrome_args

    def cleanup_data_dir(self) -> bool:
        """Cleanup temp user data dir."""
        return dir_del(self.user_data_dir, remain_root=True)

    def _start_chrome_process(self) -> None:
        """Start chrome process."""
        stdout, stderr = None, None
        if self.debugger:
            stdout, stderr = DEVNULL, STDOUT
        self.proc = Popen(  # pylint: disable=R1732
            args=self.to_args(), shell=True, stdout=stdout, stderr=stderr
        )

    @property
    def proc_ok(self) -> bool:
        """Check if process okay."""
        for _ in range(int(self.max_connection_check)):
            if self.proc and self.proc.poll() is None:
                return True
            time.sleep(0.5)
        return True

    @property
    def connection_ok(self) -> bool:
        """Check if connection okay."""
        for _ in range(int(self.max_connection_check)):
            with requests.get(self.url, timeout=self.timeout) as response:
                if response and response.ok:
                    return True
            time.sleep(0.5)
        return False

    @property
    def okay(self) -> bool:
        """Okay."""
        return self.proc_ok and self.connection_ok

    def start(self) -> bool:
        """Start process of chrome executable."""
        self._start_chrome_process()
        if not self.okay:
            self.logger.error("chrome start failed: %d", self.port)
            return False
        return True

    def kill(self, retry: int = 3) -> None:
        """Kill process of chrome executable."""
        for _ in range(retry):
            if self.proc:
                self.proc.kill()
                self.proc.__exit__(None, None, None)

            time.sleep(0.5)


class Dev:
    """Chrome Devtools Protocol Wrapper."""

    message_counter = 0

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9222,
        tab_index: int = 0,
        timeout: int = 1,
        auto_connect: bool = True,
    ):
        """Init."""
        self.host = host
        self.port = port
        self.wsk: Optional[websocket.WebSocket] = None
        self.tabs: list[dict] = []
        self.timeout = timeout
        if auto_connect:
            self.connect(tab_index=tab_index)

    def get_tabs(self) -> None:
        """Get live tabs."""
        response = requests.get(f"http://{self.host}:{self.port}/json")
        self.tabs = json.loads(response.text)

    def connect(self, tab_index: int = 0, update_tabs: bool = True) -> None:
        """Connect."""
        if update_tabs or not self.tabs:
            self.get_tabs()

        ws_url = self.tabs[tab_index]["webSocketDebuggerUrl"]
        self.close()
        self.wsk = websocket.create_connection(ws_url)
        self.wsk.settimeout(self.timeout)

    def connect_target(self, target_id: int) -> bool:
        """Connect target."""
        try:
            ws_url = f"ws://{self.host}:{self.port}/devtools/page/{target_id}"
            self.close()
            self.wsk = websocket.create_connection(ws_url)
            self.wsk.settimeout(self.timeout)
            return True
        except json.JSONDecodeError:
            ws_url = self.tabs[0]["webSocketDebuggerUrl"]
            self.wsk = websocket.create_connection(ws_url)
            self.wsk.settimeout(self.timeout)
            return False

    def close(self) -> None:
        """Close."""
        if self.wsk:
            self.wsk.close()

    # Blocking
    def wait_message(self, timeout: int = 0) -> dict:
        """Wait for message."""
        if not self.wsk:
            raise TypeError("self.wsk not init.")

        timeout = timeout if timeout else self.timeout
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
            raise TypeError("self.wsk not init.")

        timeout = timeout if timeout else self.timeout
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
            raise TypeError("self.wsk not init.")

        timeout = timeout if timeout else self.timeout
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
            raise TypeError("self.wsk not init.")

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

    def __getattr__(self, attr: str) -> Callable:
        """Get attr."""
        func_name = "{}.{}".format(self.name, attr)

        def generic_function(**args: Any) -> tuple[dict, list[dict]]:
            """General function for child attr."""
            if not self.wsk:
                raise TypeError("self.wsk not init.")

            self.pop_messages()
            self.message_counter += 1
            message_id = self.message_counter
            call_obj = {"id": message_id, "method": func_name, "params": args}
            self.wsk.send(json.dumps(call_obj))
            result, messages = self.wait_result(message_id)
            return result, messages

        return generic_function


class Chrome:
    """Chrome Browser.

    manage chrome download, launch, browser, page, tab, etc.

    """

    def __init__(
        self,
        device: Device,
        proxy_str: str,
        user_data_dir: str,
        headless: bool,
        logger: Logger,
        debugger: Optional[Debugger] = None,
    ):
        """Init Chrome."""
        self.device = device
        self.proxy_str = proxy_str
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.logger = logger
        self.debugger = debugger

        self._launcher: Launcher
        self._dev: Dev

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


class TestDownloader:
    """Test Downloader."""

    dir_app = Path(__file__).parent
    file_config = Path(dir_app.parent.parent, "protect", "config.json")
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")
    debugger = Debugger(path=dir_app, name="test")


if __name__ == "__main__":
    TestDownloader()
