import unittest
from pathlib import Path
from asia_radar.geo_upgrade import upgrade_geo_dashboard
from asia_radar.denmark_upgrade import upgrade_denmark_dashboard
ROOT=Path(__file__).resolve().parents[1]
class DenmarkUIIntegrationTests(unittest.TestCase):
    def test_danish_country_and_archive_visible(self):
        page=upgrade_denmark_dashboard(upgrade_geo_dashboard((ROOT/"docs"/"index.html").read_text(encoding="utf-8")))
        self.assertIn('data-country="Dinamarca"',page)
        self.assertIn('src="assets/flags/dk.svg"',page)
        self.assertIn('"Dinamarca":"dk"',page)
        self.assertIn('"Dinamarca":"🇩🇰"',page)
        self.assertIn('<option value="Dinamarca">Dinamarca</option>',page)
        self.assertEqual(page.count('data-country="Dinamarca"'),1)
        self.assertEqual(page,upgrade_denmark_dashboard(page))
        self.assertIn("<svg",(ROOT/"docs"/"assets"/"flags"/"dk.svg").read_text(encoding="utf-8"))
