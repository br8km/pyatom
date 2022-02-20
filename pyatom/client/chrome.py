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
    ToDo:
    - Device data

"""

import json
import time
import gc
import socket
import platform
import random
import string
from abc import ABC
from pathlib import Path
from subprocess import Popen, DEVNULL, STDOUT
from dataclasses import dataclass
from typing import Optional, Any, Callable

import requests
import websocket
import psutil

from pyatom.base.chars import str_rnd
from pyatom.base.io import dir_create, dir_del
from pyatom.base.proxy import Proxy
from pyatom.base.log import Logger, init_logger
from pyatom.base.structure import Address
from pyatom.base.debug import Debugger
from pyatom.config import ConfigManager
from pyatom.app.downloader import Downloader as HttpDownloader


__all__ = (
    "Address",
    "Desktop",
    "Mobile",
    "Downloader",
    "Launcher",
    "Dev",
    "Chrome",
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
    battery: float

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


class Downloader(HttpDownloader):
    """Chrome Downloader.

    Support `Linux` Only as of 2022-02-18

    """

    def __init__(
        self,
        user_agent: str,
        proxy_str: str,
        dir_install: Path,
        chrome_version: str,
        logger: Logger,
    ) -> None:
        """Init Chrome Downloader."""
        super().__init__(user_agent=user_agent, proxy_str=proxy_str, logger=logger)

        dir_create(dir_install)
        self.dir_install = dir_install

        self.chrome_version = chrome_version or self.latest_version()
        self.base = "https://storage.googleapis.com/chromium-browser-snapshots"

    @property
    def platform_name(self) -> str:
        """Get platform info."""
        os_name = platform.system()
        if not os_name == "Linux":
            raise SystemError(f"not supported yet: {os_name}")

        is_x64 = bool(platform.architecture()[0] == "64bit")
        return os_name if not is_x64 else os_name + "_x64"

    def show_versions(self) -> list[dict]:
        """Get Latest version of chromium."""
        os_name = platform.system().lower()
        url = "https://omahaproxy.appspot.com/all.json"
        with self.session.get(url, timeout=30) as response:
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
        return self.unzip(data, self.dir_install)

    @staticmethod
    def _gen_random_cdc() -> bytes:
        """Generate random cdc_asdjflasutopfhvcZLmcfl_ string."""
        cdc = random.choices(string.ascii_lowercase, k=26)
        cdc[-6:-4] = map(str.upper, cdc[-6:-4])
        cdc[2] = cdc[0]
        cdc[3] = "_"
        return "".join(cdc).encode()

    def _patch_exe(self) -> bool:
        """Patch for executable bytes, maybe for selenium chromedriver?"""
        if self.exist():
            with open(self.executable(), "rb") as file:
                # do some replacement to file
                print(file)
                return True
        return False

    def _is_patched(self) -> bool:
        """Check if executable has been patched."""
        if self.exist():
            with open(self.executable(), "rb") as file:
                # do some string check to file
                print(file)
                return True
        return False

    def executable(self, chrome_version: str = "") -> Path:
        """Get file path for current env executable."""
        chrome_version = chrome_version or self.chrome_version
        return self.dir_install / chrome_version / "chrome-linux" / "chrome"

    def exist(self, chrome_version: str = "") -> bool:
        """Check exist of executable file."""
        return self.executable(chrome_version).is_file()

    def _cleanup_default(self) -> bool:
        """Cleanup default chrome version."""
        return dir_del(self.dir_install / self.chrome_version)

    def _cleanup_all(self) -> bool:
        """Cleanup all chrome version."""
        return dir_del(self.dir_install, remain_root=True)

    def _cleanup_only(self, chrome_version: str) -> bool:
        """Clean only this chrome version."""
        return dir_del(self.dir_install / chrome_version)

    def _cleanup_others(self, chrome_version: str) -> bool:
        """Cleanup others except this chrome version."""
        for item in self.dir_install.iterdir():
            if item.is_dir() and chrome_version not in item.name:
                dir_del(item)
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
        proxy: Optional[Proxy],
        logger: Logger,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        """Init Chrome Launcher."""
        self.chrome_exe = chrome_exe
        self.port = port

        self.device = device
        self.proxy = proxy

        dir_create(dir_profile)
        self.dir_profile = dir_profile

        self.logger = logger
        self.debug = debug

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
            chrome_args.append(f"--user-agent={self.device.user_agent}")
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

        width, height = self.device.viewport
        chrome_args.append(f"--window-size={width},{height}")
        chrome_args.append(start_url)
        return chrome_args

    def cleanup_data_dir(self, remain_root: bool = False) -> bool:
        """Cleanup temp user data dir."""
        return dir_del(self.dir_profile, remain_root=remain_root)

    def _start_process(self) -> None:
        """Start chrome process."""
        stdout, stderr = None, None
        if self.debug:
            stdout, stderr = DEVNULL, STDOUT
        self.proc = Popen(  # pylint: disable=R1732
            args=self.to_args(), shell=True, stdout=stdout, stderr=stderr
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
            with requests.get(self.url, timeout=self.timeout) as response:
                if response and response.ok:
                    self.ready = True
                    return True
            time.sleep(0.5)
        return False

    @property
    def okay(self) -> bool:
        """Okay."""
        return self.proc_ok and self.connection_ok

    def start(self) -> bool:
        """Start process of chrome executable."""
        self._start_process()
        if not self.okay:
            self.logger.error("chrome start failed: %d", self.port)
            return False
        return True

    def kill(self, force: bool = True) -> None:
        """Kill process of chrome executable."""
        self.ready = False
        for _ in range(self.retry):
            if self.proc:
                self.proc.kill()
                self.proc.__exit__(None, None, None)
                if force:
                    try:
                        self.proc.wait(timeout=self.timeout)
                    except (psutil.TimeoutExpired, psutil.NoSuchProcess, OSError):
                        pass

                time.sleep(0.5)


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
        """Init."""
        self.host = "127.0.0.1"
        self.port = port
        self.logger = logger
        self.timeout = timeout
        self.retry = retry

        self.wsk: Optional[websocket.WebSocket] = None
        self.tabs: list[dict] = []

        if auto_connect:
            self.connect()

    def get_tabs(self) -> bool:
        """Get live tabs."""
        response = requests.get(f"http://{self.host}:{self.port}/json")
        self.tabs = json.loads(response.text)
        return len(self.tabs) > 0

    def connect(self, tab_index: int = 0, update_tabs: bool = True) -> bool:
        """Connect."""
        if update_tabs or not self.tabs:
            self.get_tabs()

        ws_url = self.tabs[tab_index]["webSocketDebuggerUrl"]
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

    def close(self, retry: int = 30) -> None:
        """Close."""
        retry = retry or self.retry
        for _ in range(retry):
            if self.wsk:
                self.wsk.close()
                time.sleep(0.5)

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

    def __getattr__(self, attr: str) -> Callable:
        """Get attr."""
        func_name = "{}.{}".format(self.name, attr)

        def generic_function(**args: Any) -> tuple[dict, list[dict]]:
            """General function for child attr."""
            if not self.wsk:
                self.logger.error("websocket not connected.")
                return {}, []

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
        dir_chrome: Path,
        logger: Logger,
        debugger: Optional[Debugger] = None,
    ):
        """Init Chrome."""
        self.dir_chrome = dir_chrome
        self.logger = logger
        self.debugger = debugger

        self.data: dict = {"time_stamp": 0, "time_str": "", "req": {}, "res": {}}

        self._launcher: Launcher
        self._dev: Dev
        self.device: Device

    def init_device(self, **kwargs: Any) -> Device:
        """Init device."""
        print(self, kwargs)
        return Mobile(
            did=str_rnd(),
            headless=True,
            user_agent="",
            os_cpu="",
            os_name="",
            os_version="",
            concurrency=0,
            fonts=[],
            languages=[],
            plugins=[],
            color_depth=24,
            viewport=(800, 600),
            session_storage=True,
            local_storage=True,
            indexed_db=True,
            device_memory=1024 * 1024 * 1024,
            flight_mode=False,
            battery=0.85,
        )

    def load_device(self) -> bool:
        """Load device data."""

    def save_device(self) -> bool:
        """Save device data."""

    def check_install(self) -> bool:
        """Check if chrome installed."""
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

    def to_dir_profile(self, device_id: str) -> Path:
        """Get dir_profile."""
        path = self.dir_chrome / "profile" / device_id
        dir_create(path)
        return path

    def to_dir_install(self) -> Path:
        """Get dir_install."""
        path = self.dir_chrome / "install"
        dir_create(path)
        return path

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

    dir_app = Path(__file__).parent
    file_config = Path(dir_app.parent.parent, "protect", "config.json")
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")
    debugger = Debugger(path=dir_app, name="test")

    def test_downloader(self) -> None:
        """Test chrome downloader."""
        # test version select, save into config, etc.
        print(self)

    def test_launcher(self) -> None:
        """Test chrome launcher."""
        # test launch, check and kill chrome process.
        print(self)

    def test_dev(self) -> None:
        """Test chrome dev."""
        # test devtools to browser, page, tab operation.
        print(self)

    def test_chrome(self) -> None:
        """Test chrome."""
        # test cookies, headers, requests, debugger save data, device fingerprints, etc.
        print(self)


if __name__ == "__main__":
    TestChrome()
