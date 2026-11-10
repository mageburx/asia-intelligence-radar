"""Enable Braga-only 'Atualidade' category in the existing static dashboard."""
from __future__ import annotations
import re

MARKER="/* BRAGA_LOCAL_V1 */"

def upgrade_braga_dashboard(html):
    if MARKER in html:
        return html
    card='<button type="button" class="category" id="braga-current-category" data-category="Atualidade" aria-pressed="false" hidden><span class="catname">📰 Atualidade local</span><span class="catcount" id="braga-current-count">—</span></button>'
    start=html.find('<div class="categorygrid" id="categories">')
    m=re.search(r'\n[ \t]*</div>\n</nav>', html[start:]) if start>=0 else None
    end=start+m.start() if m else -1
    if start<0 or end<0:
        raise RuntimeError("Braga category navigation missing")
    html=html[:end]+'\n    '+card+html[end:]
    js='function count24(country,category){'
    pos=html.find(js)
    if pos<0: raise RuntimeError("Missing counts function")
    end=html.find('function withinDays(',pos)
    if end<0: raise RuntimeError("Missing next function")
    html=html[:pos]+'''function count24(country,category){
 if(category)return Number(p.counts24[country+"|"+category]||0);
 const cats=country==="Braga"?[...categoriesByCountry,"Atualidade"]:categoriesByCountry;
 return cats.reduce((sum,c)=>sum+Number(p.counts24[country+"|"+c]||0),0);
}
'''+html[end:]
    anchor='$("economy-count").textContent=count24(state.country,"Economia")+" notícias · 24 h";'
    if anchor not in html: raise RuntimeError("Missing Economy indicator")
    html=html.replace(anchor,anchor+'''
 $("braga-current-category").hidden=state.country!=="Braga";
 $("braga-current-count").textContent=count24("Braga","Atualidade")+" notícias · 24 h";''',1)
    anchor='const allowed=state.mode==="bosch"?categoriesBosch:categoriesByCountry;'
    if anchor not in html: raise RuntimeError("Missing deep link category matcher")
    html=html.replace(anchor,'const allowed=state.mode==="bosch"?categoriesBosch:(state.country==="Braga"?[...categoriesByCountry,"Atualidade"]:categoriesByCountry);',1)
    anchor='function archiveCategories(){'
    ix=html.find(anchor)
    if ix<0: raise RuntimeError("Missing archive categories")
    html=html[:ix]+html[ix:].replace(anchor,anchor+'''
 if(state.archiveCountry==="Braga")return [...categoriesByCountry,"Atualidade"];''',1)
    anchor='return categoriesByCountry.concat(categoriesBosch);'
    if anchor not in html: raise RuntimeError("Missing archive combined categories")
    html=html.replace(anchor,'return categoriesByCountry.concat(["Atualidade"],categoriesBosch);',1)
    anchor='function changeSelection(country,category){'
    if anchor not in html: raise RuntimeError("Missing change selection")
    html=html.replace(anchor,anchor+'''
 if(country!=="Braga"&&category==="Atualidade")category="";''',1)
    html=html.replace('</style>',MARKER+'''
#braga-current-category{border-color:#3a5f6b}
#braga-current-category[aria-pressed="true"]{border-color:#77d8c6}
'''+'''</style>''',1)
    return html
