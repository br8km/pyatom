
from pathlib import Path


class Config:
    """Config."""

    dir_app = Path(__file__).parent.parent

    dir_dat =  dir_app / "data"
    dir_out = dir_app / "out"
    dir_cache = dir_out / "cache"
    dir_debug = dir_out / "debug"
    dir_log = dir_out / "log"
    dir_tmp = dir_out / "tmp"

