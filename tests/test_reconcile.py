import unittest
from datetime import datetime, timezone, timedelta
from asia_radar.reconcile import combine_articles

NOW = datetime.now(timezone.utc)

def row(i, translated=False, seen_hours=3):
    t=(NOW-timedelta(hours=seen_hours)).isoformat()
    return {"id":i,"country":"Bosch","category":"Indústria","published_at":t,
            "first_seen_at":t,"url":f"https://example.org/{i}",
            "translation_status":"translated" if translated else "pending",
            "translated_title":"Tradução aprovada" if translated else "",
            "translated_summary":"", "translated_lang":"pt" if translated else ""}

class ReconcileTests(unittest.TestCase):
    def test_union_does_not_drop_newer_remote_article(self):
        items=combine_articles([row("remote")],[row("collected")])
        self.assertEqual({x["id"] for x in items},{"remote","collected"})

    def test_translation_not_overwritten_by_pending(self):
        items=combine_articles([row("a",translated=True)],[row("a",translated=False)])
        self.assertEqual(items[0]["translation_status"],"translated")
        self.assertEqual(items[0]["translated_title"],"Tradução aprovada")

    def test_new_translation_replaces_pending(self):
        items=combine_articles([row("a")],[row("a",translated=True)])
        self.assertEqual(items[0]["translation_status"],"translated")

    def test_old_bosch_sports_headline_removed_on_merge(self):
        bad=row("edo")
        bad["original_title"]="Edo Bosch comenta derrota na Supertaça de hóquei"
        clean=row("motor")
        clean["original_title"]="Nova fábrica de motores Bosch em Braga"
        result=combine_articles([bad,clean],[bad])
        self.assertEqual([x["id"] for x in result],["motor"])

    def test_still_respects_thirty_days(self):
        old=row("old")
        old["published_at"]=(NOW-timedelta(days=31)).isoformat()
        items=combine_articles([row("recent"),old],[])
        self.assertEqual([x["id"] for x in items],["recent"])
