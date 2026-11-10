import unittest
from asia_radar.braga_local import is_braga_local, classify_braga, filter_records, BRAGA_IDS
from asia_radar.braga_upgrade import upgrade_braga_dashboard

class BragaLocalTests(unittest.TestCase):
    SID="braga-ominho"
    def test_brazil_and_surnames_rejected(self):
        for title, url in [
            ("Braga e Omar contra as bets","https://portalunico.com/news"),
            ("XTB Talks: Ricardo Braga explica dividendos","https://xtb.com/story"),
            ("IBGE destaca liderança de Luís Eduardo Magalhães em arborização urbana","https://blogbraga.com.br/news"),
            ("Operação Natal Seguro coloca polícias nas ruas de Manaus","https://ominho.pt/news"),
            ("Mau tempo no distrito de Braga","https://ominho.pt/news"),
            ("SC Braga vence jogo de futebol","https://ominho.pt/news"),
        ]:
            self.assertFalse(is_braga_local(title,url=url,source_id=self.SID),title)
    def test_accept_municipality_and_city_stories(self):
        examples=[
            "Câmara Municipal de Braga aprova investimento",
            "Braga: carrinha despista-se na Avenida da Liberdade",
            "Gala Jovens Talentos juntou 115 participantes no Theatro Circo",
            "Startup Braga acolhe novas empresas",
            "Mobilidade de Braga ganha nova linha TUB",
            "Município de Braga requalifica equipamento",
            "Gualtar recebe novo equipamento escolar",
        ]
        for t in examples:
            self.assertTrue(is_braga_local(t,url="https://ominho.pt/story",source_id=self.SID),t)
    def test_unknown_source_is_not_local(self):
        self.assertFalse(is_braga_local("Câmara de Braga",source_id="braga-politics"))
    def test_category_fallback(self):
        self.assertEqual(classify_braga("Braga recebe festa de São João"),"Atualidade")
        self.assertEqual(classify_braga("Câmara de Braga aprova orçamento"),"Política")
        self.assertEqual(classify_braga("TUB Braga anuncia novos autocarros"),"Automóvel")
        self.assertEqual(classify_braga("Startup Braga anuncia investimento"),"Economia")
    def test_previous_untrusted_stories_cleared(self):
        rows=[{"id":"a","country":"Braga","original_title":"Braga e Omar contra bets","source_id":"braga-politics"},
              {"id":"b","country":"Braga","original_title":"Câmara de Braga anuncia plano","source_id":"braga-ominho"},
              {"id":"c","country":"Bosch","source_id":"bosch-official-de"}]
        self.assertEqual({r["id"] for r in filter_records(rows)},{"b","c"})
    def test_geo_ui_upgrade_once(self):
        page='''<style></style><div class="categorygrid" id="categories">
</div>
</nav><script>
const allowed=state.mode==="bosch"?categoriesBosch:categoriesByCountry;
function count24(country,category){return 1;}
function withinDays(){}
$("economy-count").textContent=count24(state.country,"Economia")+" notícias · 24 h";
function archiveCategories(){
 return categoriesByCountry.concat(categoriesBosch);
}
function changeSelection(country,category){}
</script>'''
        upgraded=upgrade_braga_dashboard(page)
        self.assertIn('id="braga-current-category"',upgraded)
        self.assertIn('"Atualidade"',upgraded)
        self.assertEqual(upgraded,upgrade_braga_dashboard(upgraded))
