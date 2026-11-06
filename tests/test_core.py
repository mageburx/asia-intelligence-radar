import unittest
from datetime import datetime,timedelta,timezone
from asia_radar.core import article_id,topic_tags,relevant_native_politics,trend_data,clean_text
from asia_radar.report import make_payload
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
    def test_zero_history_dashboard(self):
        p=make_payload([],{},datetime.now(timezone.utc))
        self.assertEqual(p["articles"],[])
        self.assertEqual(p["counts24"]["Japão|Política"],0)
if __name__=="__main__":
    unittest.main()
