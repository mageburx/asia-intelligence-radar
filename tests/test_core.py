import unittest
from datetime import datetime,timedelta,timezone
from asia_radar.core import article_id,topic_tags,relevant_native_politics,trend_data,clean_text
from asia_radar.report import make_payload
from asia_radar.collector import detect_source_lang,feed_url,ROOT
import json
class RadarTests(unittest.TestCase):
    def test_strip_markup(self):
        self.assertEqual(clean_text("<p>A &amp; B</p>"),"A & B")
    def test_dedupe_url_tracking(self):
        self.assertEqual(article_id("China","Automóvel","https://x.cn/a?utm_source=test","X"),
                         article_id("China","Automóvel","https://x.cn/a","X"))
    def test_multilingual_topics(self):
        self.assertIn("Baterias",topic_tags("全固体電池"))
        self.assertIn("BYD",topic_tags("比亚迪"))
    def test_native_politics_filter(self):
        self.assertTrue(relevant_native_politics("政府の政策",""))
        self.assertFalse(relevant_native_politics("Restaurante local",""))
    def test_trend_requires_independent_publishers(self):
        now=datetime.now(timezone.utc)
        articles=[{"id":str(i),"country":"Japão","category":"Automóvel","published_at":(now-timedelta(hours=2)).isoformat(),
                   "topics":["Baterias"],"publisher":"Fonte A"} for i in range(3)]
        self.assertEqual(trend_data(articles,now)[0]["status"],"A monitorizar")
        articles[2]["publisher"]="Fonte B"
        self.assertEqual(trend_data(articles,now)[0]["status"],"Tema emergente")
    def test_new_language_detection(self):
        self.assertEqual(detect_source_lang("현대차 전기차","Coreia do Sul"),"ko")
        self.assertEqual(detect_source_lang("台灣政府宣布政策","Taiwan"),"zh-TW")
        self.assertEqual(detect_source_lang("Bundesregierung plant neue Regeln","Alemanha"),"de")
        self.assertEqual(detect_source_lang("India auto manufacturing","Índia"),"en")
    def test_seven_country_sources(self):
        sources=json.loads((ROOT/"config"/"sources.json").read_text(encoding="utf-8"))
        countries={"China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura"}
        self.assertEqual(set(s["country"] for s in sources),countries)
        for c in countries:
            self.assertEqual(set(s["category"] for s in sources if s["country"]==c),{"Política","Automóvel"})
        self.assertEqual(len(set(s["id"] for s in sources)),len(sources))
        self.assertTrue(all(feed_url(s).startswith("https://") for s in sources))
    def test_empty_counts_seven_markets(self):
        p=make_payload([],{},datetime.now(timezone.utc))
        for country in ("China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura"):
            self.assertIn(f"{country}|Política",p["counts24"])
            self.assertIn(f"{country}|Automóvel",p["counts24"])
    def test_zero_history_dashboard(self):
        p=make_payload([],{},datetime.now(timezone.utc))
        self.assertEqual(p["articles"],[])
        self.assertEqual(p["counts24"]["Japão|Política"],0)
if __name__=="__main__":
    unittest.main()
