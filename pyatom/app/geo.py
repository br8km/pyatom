"""
    GeoIP Address Data Extracting
"""

from pathlib import Path
from typing import Any, Union
from geoip2.database import Reader


__all__ = ("geoip",)


def geoip(addr: str, file_geo: Union[str, Path]) -> dict[str, Any]:
    """maxmind geoip2 database connection for ip address parser"""
    if addr:
        try:
            res = Reader(str(file_geo)).city(addr)
            data = {
                "country": res.country.iso_code,
                "state": res.subdivisions.most_specific.name,
                "city": res.city.name,
                "timezone": res.location.time_zone,
                "zip": res.postal.code,
                "coordinate": (res.location.latitude, res.location.longitude),
            }
            return data
        except ValueError as err:
            print(err)
    return {}
