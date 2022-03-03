"""
    GeoIP Address Data Extracting
"""

from pathlib import Path

from geoip2.database import Reader

from pyatom.base.timer import utc_offset
from pyatom.base.structure import Address
from pyatom.config import DIR_DEBUG


__all__ = (
    "geoip",
    "Address",
)


def geoip(ipaddr: str, file_geo: Path) -> Address:
    """maxmind geoip2 database connection for ip address parser"""
    res = Reader(str(file_geo)).city(ipaddr)
    country = res.country.iso_code
    state = res.subdivisions.most_specific.name
    city = res.city.name
    postal = res.postal.code
    time_zone = res.location.time_zone
    offset = utc_offset(time_zone) if time_zone else 0
    latitude = res.location.latitude
    longitude = res.location.longitude
    coordinate = (
        latitude or 0.0,
        longitude or 0.0,
    )
    return Address(
        ipaddr=ipaddr,
        country=country or "",
        state=state or "",
        city=city or "",
        postal=postal or "",
        coordinate=coordinate,
        time_zone=time_zone or "",
        street="",
        utc_offset=offset,
    )


class TestGeoip:
    """TestCase for geoip."""

    ip_addr = "172.245.255.158"

    dir_app = Path(__file__).parent
    file_geo = DIR_DEBUG.parent / "data" / "GeoLite2-City.mmdb"

    def test_geoip(self) -> None:
        """Test geoip."""
        print(self.file_geo.absolute())
        assert self.file_geo.is_file()
        address = geoip(ipaddr=self.ip_addr, file_geo=self.file_geo)
        print(address)
        assert address.country
        assert address.coordinate[0] and address.coordinate[1]
        assert address.time_zone


if __name__ == "__main__":
    TestGeoip()
