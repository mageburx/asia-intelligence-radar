import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class DashboardStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=(ROOT/"docs"/"index.html").read_text(encoding="utf-8")

    def test_three_independent_views(self):
        for view in ("countries","bosch","archive"):
            self.assertIn('data-view="'+view+'"',self.doc)
        self.assertIn('id="live-view"',self.doc)
        self.assertIn('id="archive-view"',self.doc)
        self.assertIn('id="archive-articles"',self.doc)

    def test_trends_are_secondary_and_collapsed(self):
        start=self.doc.index('<section class="area" aria-labelledby="news-title">')
        signals=self.doc.index('<section class="signals-area"')
        archive=self.doc.index('<section id="archive-view"') if '<section id="archive-view"' in self.doc else self.doc.index('<section id="archive-view"')
        self.assertLess(start,signals)
        self.assertLess(signals,archive)
        self.assertIn('<details class="signals-details" id="signals-panel">',self.doc)
        self.assertIn('id="signals-summary-count"',self.doc)
        self.assertNotIn('class="progress"',self.doc)
        self.assertNotIn('class="fill"',self.doc)
        self.assertIn('function highlightedSignal(article)',self.doc)
    def test_archive_controls_and_export(self):
        for item in ("archive-country","archive-category","archive-days","archive-search","archive-more"):
            self.assertIn('id="'+item+'"',self.doc)
        self.assertIn('href="arquivo-30-dias.csv"',self.doc)
        self.assertNotIn('id="archive-go"',self.doc)

    def test_countries_and_bosch_visuals(self):
        self.assertEqual(self.doc.count('class="country-card"'),7)
        for country in ("China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura"):
            self.assertIn('data-country="'+country+'"',self.doc)
        for category in ("Estratégia","Mobilidade","Indústria","Tecnologia","Pessoas","Portugal"):
            self.assertIn('data-bosch-category="'+category+'"',self.doc)
        self.assertIn('class="bosch-logo-plate',self.doc)
        self.assertIn('class="category-visual"',self.doc)

if __name__=="__main__":
    unittest.main()
