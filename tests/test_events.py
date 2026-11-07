import unittest
from datetime import datetime, timedelta, timezone

from asia_radar.events import group_events, grouping_stats, same_event, headline_forms
from asia_radar.dashboard_upgrade import upgrade_dashboard, START

NOW = datetime(2026, 11, 7, 0, 0, tzinfo=timezone.utc)


def news(id, title, country="Alemanha", category="Automóvel", publisher="Fonte A",
         offset_hours=0, translation="", url=None):
    return {
        "id": id, "original_title": title, "translated_title": translation,
        "translation_status": "translated" if translation else "pending",
        "published_at": (NOW-timedelta(hours=offset_hours)).isoformat(),
        "country": country, "category": category, "publisher": publisher,
        "url": url or f"https://source.test/article/{id}",
    }


class EventGroupingTests(unittest.TestCase):
    def test_reordered_actors_not_silently_conflated(self):
        a=news("a","Japan bans China imports after security review")
        b=news("b","China bans Japan imports after security review")
        g=group_events([a,b])
        self.assertNotEqual(g[0]["event_id"],g[1]["event_id"])

    def test_same_story_different_publishers(self):
        rows=[
            news("a","Bosch opens new electric motor factory in Germany - The Herald",publisher="The Herald"),
            news("b","Bosch opens new electric motor factory in Germany - News Daily",publisher="News Daily",offset_hours=2),
            news("c","Toyota releases new hybrid model in Japan",publisher="Auto Press"),
        ]
        grouped=group_events(rows)
        self.assertEqual(grouped[0]["event_id"],grouped[1]["event_id"])
        self.assertNotEqual(grouped[0]["event_id"],grouped[2]["event_id"])
        self.assertEqual(grouping_stats(grouped)["secondary_articles"],1)
        self.assertNotIn("event_id",rows[0])

    def test_similar_but_different_numbers_do_not_merge(self):
        a=news("a","Bosch reports 200 job cuts at German plant")
        b=news("b","Bosch reports 300 job cuts at German plant")
        g=group_events([a,b])
        self.assertNotEqual(g[0]["event_id"],g[1]["event_id"])

    def test_separate_countries_and_categories(self):
        title="Bosch plans new battery factory in Germany"
        a=news("a",title,country="Bosch",category="Indústria")
        b=news("b",title,country="Alemanha",category="Automóvel")
        c=news("c",title,country="Bosch",category="Estratégia")
        g=group_events([a,b,c])
        self.assertEqual(len(set(x["event_id"] for x in g)),3)

    def test_old_story_not_grouped_with_new_one(self):
        title="Bosch opens new electric motor factory in Germany"
        g=group_events([news("a",title),news("b",title,offset_hours=100)])
        self.assertNotEqual(g[0]["event_id"],g[1]["event_id"])

    def test_same_url_normalization(self):
        a=news("a","Story about Bosch automation",url="https://test.com/news/1?utm_source=feed")
        b=news("b","Completely different title of an updated story",url="https://test.com/news/1")
        g=group_events([a,b])
        self.assertEqual(g[0]["event_id"],g[1]["event_id"])

    def test_different_major_stories_remain_distinct(self):
        rows=[
            news("a","Germany plans new tariffs on imported cars"),
            news("b","Germany considers raising taxes on electric vehicle owners"),
            news("c","Germany announces new battery plant investment"),
        ]
        g=group_events(rows)
        self.assertEqual(len(set(x["event_id"] for x in g)),3)

    def test_translated_titles_can_be_compared(self):
        rows=[
            news("a","Bosch baut neue Autofabrik in Deutschland",translation="Bosch opens new car factory in Germany"),
            news("b","Bosch opens new car factory in Germany",publisher="News B"),
        ]
        g=group_events(rows)
        self.assertEqual(g[0]["event_id"],g[1]["event_id"])

    def test_empty(self):
        self.assertEqual(group_events([]),[])
        self.assertEqual(grouping_stats([])["events"],0)


class UIUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.page="""<!doctype html><style>.article{padding:1px}</style><body>
<script id="payload" type="application/json">{"articles":[]}</script>
<script>
function drawArticles(){
 const list=filteredArticles();
 return list;
}
function archiveCategories(){return [];}
function drawArchive(){
 const list=filteredArchive();
 return list;
}
function render(){}
</script></body>"""

    def test_upgrade_once(self):
        page=upgrade_dashboard(self.page)
        self.assertEqual(page.count(START),1)
        self.assertEqual(page.count("function groupedEvents("),1)
        self.assertEqual(page.count("function eventCard("),1)
        self.assertEqual(page.count("function drawArticles("),1)
        self.assertEqual(page.count("function drawArchive("),1)
        self.assertIn("publicações",page)
        self.assertEqual(page,upgrade_dashboard(page))

    def test_wrong_template_refused(self):
        with self.assertRaises(RuntimeError):
            upgrade_dashboard("<html><style></style></html>")


if __name__=="__main__":
    unittest.main()
