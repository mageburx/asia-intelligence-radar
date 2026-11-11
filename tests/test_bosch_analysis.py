import unittest
from datetime import datetime, timedelta, timezone
from asia_radar.bosch_analysis import analyze_bosch,load_facts
from asia_radar.bosch_group_upgrade import upgrade_bosch_group_dashboard,MARKER
from asia_radar.report import make_payload

NOW=datetime(2026,11,11,15,tzinfo=timezone.utc)

def article(i,d,country="Bosch",category="Pessoas",event=None,official=False):
    return dict(id=i,event_id=event or i,country=country,category=category,
      published_at=(NOW-timedelta(days=d)).isoformat(),
      publisher="Publisher "+i,source_type="Comunicado oficial" if official else "Imprensa / agregador",
      original_title="Bosch group news",url="https://example.test/"+i,topics=["Emprego e reorganização"])

class AnalysisTests(unittest.TestCase):
    def test_facts_are_sourced_and_dated(self):
        f=load_facts()
        self.assertEqual(f["report_date"],"2026-09-23")
        self.assertEqual(f["h1"]["sales"],46.4)
        self.assertEqual(len(f["sectors"]),4)
        self.assertTrue(f["report_url"].startswith("https://"))
    def test_coverage_is_event_based_and_separate(self):
        rows=[article("a",1,event="same",official=True),article("b",2,event="same"),
              article("c",2,category="Portugal"),article("d",10),article("e",1,country="China")]
        s={"first_run_at":(NOW-timedelta(days=5)).isoformat()}
        m=analyze_bosch(rows,s,NOW)["monitor"]
        self.assertEqual((m["articles"],m["events"],m["official_articles"]),(3,2,1))
        self.assertEqual(m["categories"]["Pessoas"],1)
        self.assertIsNone(m["previous_events"])
        self.assertFalse(m["comparison_ready"])
    def test_comparison_requires_14_days(self):
        s={"first_run_at":(NOW-timedelta(days=20)).isoformat()}
        m=analyze_bosch([article("a",1),article("b",10)],s,NOW)["monitor"]
        self.assertEqual(m["previous_events"],1)
    def test_payload_exposes_analysis(self):
        p=make_payload([article("a",1)],{"first_run_at":NOW.isoformat()},NOW)
        self.assertEqual(p["bosch_analysis"]["monitor"]["articles"],1)
    def test_upgrade_is_idempotent(self):
        sample='<html><style></style><body><section class="bosch-picker" id="bosch-view"><div id="bosch-categories"></div></section><div id="live-view"></div></body></html>'
        upgraded=upgrade_bosch_group_dashboard(sample)
        self.assertIn('id="bosch-group-analysis"',upgraded)
        self.assertIn('data-bga="monitor"',upgraded)
        self.assertIn('id="live-view"',upgraded)
        self.assertEqual(upgraded.count(MARKER),1)
        self.assertEqual(upgraded,upgrade_bosch_group_dashboard(upgraded))
