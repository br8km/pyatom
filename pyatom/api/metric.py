# -*- coding: utf-8 -*-

"""
    Metrics for Domain, Url, etc. like: DomDetailer API
"""

import requests

from pyatom.base.utils import print2
from pyatom.base.log import Logger, init_logger
from pyatom.config import ConfigManager
from pyatom.config import DIR_DEBUG


__all__ = ("DomDetailer",)


class DomDetailer:
    """
    Dom.Detailer: "https://domdetailer.com/API.php"
    Alternative: https://seo-rank.my-addr.com/
    """

    def __init__(self, app: str, key: str, logger: Logger):
        """Init DomDetailer."""
        self.app = app
        self.key = key
        self.logger = logger

        self.params = {"apikey": self.key, "app": self.app}

        self.min_cf = 10
        self.min_tf = 10
        self.min_da = 10
        self.min_pa = 10

    def balance(self) -> float:
        """Get Account Balance"""
        url = "http://domdetailer.com/api/checkBalance.php"
        with requests.post(url, data=self.params) as response:
            if response is not None and "UnitsLeft" in response.text:
                data = response.json()
                if isinstance(data, list):
                    return float(data[1])
        return 0.0

    def check(
        self, domain: str, majestic_choice: str = "root", debug: bool = False
    ) -> dict:
        """
        Filter Domain.Metrics For Moz.Majestic.API
        Params:
            :majesticChoice
                :url - returns the Majestic stats for http://domain.com
                :root - returns the Majestic stats for domain.com
                :subdomain - return the Majestic stats for www.domain.com
                :asis - return the Majestic stats for whatever domain is sent via teh API
        Metrics:
            :domain - Domain the check was done on
            :mozLinks - Moz. number of Links for the domain
            :mozPA - Moz Page Authority
            :mozDA - Moz Domain Authority
            :mozRank - Moz Rank
            :mozTrust - currently removed - Moz Trust Rank
            :majesticLinks - Majestic's Links for the domain
            :majesticRefDomains - Majestic's Referring Domains
            :majesticCF - Majestic's Citation Flow
            :majesticTF - Majestic's Trust Flow
            :FB_comments - Amount of Comments on Facebook
            :FB_shares - Amount of Shares on Facebook
            :pinterest_pins - Amount of Pins on Pinterest
        """
        params = self.params
        params["domain"] = domain
        params["majesticChoice"] = majestic_choice
        url = f"http://domdetailer.com/api/checkDomain.php?{params}"
        resp = requests.post(url, data=params)
        self.logger.info("<%d>[%d] - %s", resp.status_code, len(resp.text), resp.url)
        if resp and resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict):
                if debug:
                    print2(data)
                return data
        return {}


class TestMetric:
    """TestCase for Metric api wrappers."""

    file_config = DIR_DEBUG.parent / "protect" / "config.json"
    config = ConfigManager().load(file_config)

    logger = init_logger(name="test")

    def test_domdetailer(self) -> None:
        """Test DomDetailer."""
        app = DomDetailer(
            app=self.config.domdetailer_app,
            key=self.config.domdetailer_key,
            logger=self.logger,
        )
        balance = app.balance()
        print(f"domdetailer.balance = {balance}")
        assert balance > 0

        data = app.check(domain="bing.com", debug=True)
        assert data != {}


if __name__ == "__main__":
    TestMetric()
