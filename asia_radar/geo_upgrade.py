"""Idempotent UI migration: Economy topic, Portugal country, Braga city.

The static HTML contains a large embedded article payload. This migration edits
only stable HTML/JS anchors during the hourly report generation.
"""
from __future__ import annotations
import re

MARKER = "/* GEOGRAPHY_V1 */"
FLAGS = {
    "Portugal": "pt",
}
STYLE = """
/* GEOGRAPHY_V1 */
.categorygrid{grid-template-columns:repeat(4,minmax(0,1fr))}
.local-picker{margin-top:17px;padding:13px 0 2px;border-top:1px solid #334958}
.local-label{font-size:11px;letter-spacing:.1em;color:#96b9bf;text-transform:uppercase;margin:0 0 10px;font-weight:750}
.local-picker .country-card{max-width:300px}
.city-marker{display:inline-flex;align-items:center;justify-content:center;font-size:26px;min-width:29px}
@media(max-width:660px){.categorygrid{grid-template-columns:repeat(2,minmax(0,1fr))}.local-picker .country-card{max-width:100%}}
"""

def _replace_once(page, before, after, description):
    if before not in page:
        raise RuntimeError(f"Geography upgrade: missing {description}")
    return page.replace(before, after, 1)


def _js_region(page, start, stop):
    a=page.find(start)
    b=page.find(stop,a+len(start))
    if a < 0 or b < 0:
        raise RuntimeError(f"Geography upgrade: missing JS function {start}")
    return a,b


def upgrade_geo_dashboard(template):
    if MARKER in template:
        return template
    page=_replace_once(template,"</style>",STYLE+"</style>","stylesheet")
    page=page.replace(
        "<title>Asia Intelligence Radar — 7 países</title>",
        "<title>Intelligence Radar — 8 países, Braga e Bosch</title>",1
    )
    page=_replace_once(
        page,"<h2>Escolhe o país</h2>",
        "<h2>Escolhe o país</h2>","country heading"
    )
    # Add the eighth country to the existing grid, before its closing tag.
    marker='  <div class="countrygrid" id="countries" aria-label="Países disponíveis">'
    a=page.find(marker)
    b=page.find("\n  </div>",a+len(marker))
    if a<0 or b<0:
        raise RuntimeError("Geography upgrade: country grid not found")
    country_card='''\n    <button type="button" class="country-card" data-country="Portugal" aria-pressed="false"><img class="flag-image" src="assets/flags/pt.svg" alt="" width="34" height="26" decoding="async"><span class="countrycopy"><strong>Portugal</strong><small>Notícias nas últimas 24 h</small></span><span class="selection" aria-hidden="true">✓</span></button>'''
    page=page[:b]+country_card+page[b:]
    # Braga is a city, never displayed as a ninth country.
    place_label='''<div class="local-picker"><p class="local-label">Área local · cidade</p>
    <button type="button" class="country-card" data-country="Braga" aria-pressed="false"><span class="city-marker" aria-hidden="true">🏙️</span><span class="countrycopy"><strong>Braga</strong><small>Notícias locais · 24 h</small></span><span class="selection" aria-hidden="true">✓</span></button></div>
  <div class="stepdivider"></div>'''
    page=_replace_once(page,'  <div class="stepdivider"></div>',place_label,"local place slot")
    category_button='''    <button type="button" class="category" data-category="Economia" aria-pressed="false"><span class="catname">📊 Economia</span><span class="catcount" id="economy-count">—</span></button>\n'''
    category_at=page.find('<div class="categorygrid" id="categories">')
    category_end=page.find("\n  </div>",category_at)
    if category_at<0 or category_end<0:
        raise RuntimeError("Geography upgrade: category grid not found")
    page=page[:category_end]+"\n"+category_button.rstrip()+page[category_end:]
    page=_replace_once(page,'<option value="Bosch">⚙ Bosch</option>',
      '<option value="Portugal">🇵🇹 Portugal</option><option value="Braga">🏙️ Braga</option><option value="Bosch">⚙ Bosch</option>',
      "archive geography filter")
    # JS constants
    page=_replace_once(page,'const countries=["China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura"];',
      'const countries=["China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura","Portugal"];\nconst cities=["Braga"];\nconst places=[...countries,...cities];',
      "country constants")
    page=_replace_once(page,'const categoriesByCountry=["Política","Automóvel"];',
      'const categoriesByCountry=["Política","Automóvel","Economia"];',
      "country categories")
    # Keep the existing flags/icons and SVGs. Add Portugal for both labels and images.
    page=_replace_once(page,'"Singapura":"🇸🇬"};',
      '"Singapura":"🇸🇬","Portugal":"🇵🇹"};', "flag name map")
    page=_replace_once(page,'"Singapura":"sg"};',
      '"Singapura":"sg","Portugal":"pt"};', "flag file map")
    page=_replace_once(page,'const icons={"Política":"🏛️","Automóvel":"🚗","Estratégia":"📈","Mobilidade":"🚘","Indústria":"🏭","Tecnologia":"💻","Pessoas":"👥","Portugal":"🇵🇹"};',
      'const icons={"Política":"🏛️","Automóvel":"🚗","Economia":"📊","Estratégia":"📈","Mobilidade":"🚘","Indústria":"🏭","Tecnologia":"💻","Pessoas":"👥","Portugal":"🇵🇹"};', "category icon map")
    page=page.replace('countries.includes(c)','places.includes(c)')
    page=page.replace('countries.includes(state.archiveCountry)','places.includes(state.archiveCountry)')
    page=page.replace('countries.includes(state.country)','places.includes(state.country)')
    # Ensure local place is visibly identifiable even though it has no national flag.
    start,stop=_js_region(page,'function flagImage(country,klass=', 'function visualFor(country)')
    snippet=page[start:stop]
    if ':\"\";' not in snippet:
        raise RuntimeError("Geography upgrade: flag fallback missing")
    snippet=snippet.replace(':\"\";', ':country==="Braga" ? \'<span class="city-marker" aria-hidden="true">🏙️</span>\' :\"\";',1)
    page=page[:start]+snippet+page[stop:]
    # Count all 3 categories, not just the old two.
    start,stop=_js_region(page,'function count24(country,category){','function withinDays(')
    page=page[:start]+'''function count24(country,category){
 if(category)return Number(p.counts24[country+"|"+category]||0);
 return categoriesByCountry.reduce((sum,cat)=>sum+Number(p.counts24[country+"|"+cat]||0),0);
}
'''+page[stop:]
    m=re.search(r'(\$\("auto-count"\)\.textContent=[^\n]+;)',page)
    if not m:
        raise RuntimeError("Geography upgrade: category counter missing")
    page=page[:m.end()]+ '\n $("economy-count").textContent=count24(state.country,"Economia")+" notícias · 24 h";'+page[m.end():]
    # Improve geographic description without implying Braga is a country.
    page=page.replace("e um radar dedicado à Bosch. Tudo organizado por área e tema.",
      "Portugal e notícias da cidade de Braga, além de um radar dedicado à Bosch. Tudo organizado por área e tema.",1)
    return page
