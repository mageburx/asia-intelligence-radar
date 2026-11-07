"""Idempotent upgrade of the generated static HTML dashboard.

The dashboard file carries a large embedded JSON payload. Updating it inside
the hourly report avoids replacing megabytes of historical news just to ship UI.
"""
from __future__ import annotations
import re

START = "/* EVENT_GROUPING_V1 */"
END = "/* /EVENT_GROUPING_V1 */"

STYLE = """
.event-group{min-width:0;display:flex;flex-direction:column;border-radius:14px}
.event-group>.article{border-radius:14px 14px 0 0}
.related-stories{border:1px solid #355262;border-top:0;border-radius:0 0 14px 14px;background:#102638;color:#cfebeb}
.related-stories summary{cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;font-size:12px;font-weight:750;color:#99ecd9}
.related-stories summary::-webkit-details-marker{display:none}
.related-stories summary:hover{background:#193b46}
.related-stories summary:focus-visible{outline:2px solid #85e9da;outline-offset:-2px}
.related-stories[open] summary{border-bottom:1px solid #2a4954}
.related-list{padding:7px 15px 12px;display:grid;gap:0}
.related-entry{padding:10px 0;border-bottom:1px solid #284251;display:grid;gap:3px}
.related-entry:last-child{border-bottom:0}
.related-entry a{font-size:12px;line-height:1.45;color:#e4f3f4;text-decoration:none;overflow-wrap:anywhere}
.related-entry a:hover{text-decoration:underline}
.related-meta{font-size:11px;color:#a7bdc9;display:flex;gap:8px;flex-wrap:wrap}
.event-count{display:inline-block;font-size:11px;color:#a6decf;border:1px solid #3d7768;border-radius:7px;padding:4px 8px}
@media(max-width:650px){.related-stories summary{padding:10px 12px}.related-list{padding:6px 12px 10px}}
"""

# This block is inserted only once, just before the existing drawArticles().
HELPERS = r"""
function groupedEvents(list){
 const groups=new Map();
 for(const article of list){
   const id=article.event_id||article.id;
   if(!groups.has(id))groups.set(id,[]);
   groups.get(id).push(article);
 }
 return [...groups.values()];
}
function eventCard(group){
 if(group.length===1)return articleCard(group[0]);
 const lead=group[0], others=group.slice(1);
 const publishers=new Set(group.map(a=>a.publisher||a.source).filter(Boolean));
 const detail=others.map(a=>{
   const title=a.translation_status==="translated"&&a.translated_title?a.translated_title:a.original_title;
   return '<div class="related-entry"><div class="related-meta">'
     +countryBadge(a.country)+'<span>'+safe(a.publisher||a.source)+'</span>'
     +'<span>· '+safe(fmt(a.published_at))+'</span></div>'
     +'<a href="'+safe(a.url)+'" target="_blank" rel="noopener noreferrer">'+safe(title)+' ↗</a></div>';
 }).join("");
 return '<div class="event-group">'+articleCard(lead)
   +'<details class="related-stories"><summary>📰 '+group.length
   +' publicações · '+publishers.size+' fontes <span>Ver cobertura ▾</span></summary>'
   +'<div class="related-list">'+detail+'</div></details></div>';
}
"""

LIVE = r"""function drawArticles(){
 const list=filteredArticles();
 const groups=groupedEvents(list);
 const secondary=list.length-groups.length;
 $("listcount").textContent=groups.length+" acontecimentos · "+list.length+" notícias"
   +(secondary?" · "+secondary+" agrupadas":"")+" · "+state.country+" / "+(state.category||"Todas as categorias");
 const items=groups.slice(0,state.visible);
 $("articles").innerHTML=items.length?items.map(eventCard).join("")
   :'<div class="empty">Sem notícias para estes filtros. Experimenta outra categoria ou alarga o período.</div>';
 $("more").hidden=state.visible>=groups.length;
}
"""

ARCHIVE = r"""function drawArchive(){
 $("archive-country").value=state.archiveCountry;
 $("archive-days").value=String(state.archiveDays);
 drawArchiveCategoryOptions();
 const list=filteredArchive();
 const groups=groupedEvents(list);
 const sources=new Set(list.map(a=>a.publisher||a.source).filter(Boolean)).size;
 const translated=list.filter(a=>a.translation_status==="translated").length;
 const markets=new Set(list.map(a=>a.country)).size;
 const metrics=[["Acontecimentos",groups.length],["Notícias arquivadas",list.length],
                ["Fontes diferentes",sources],["Países / empresa",markets]];
 $("archive-metrics").innerHTML=metrics.map(m=>'<div class="metric"><span class="name">'
   +safe(m[0])+'</span><span class="num">'+safe(m[1])+'</span></div>').join("");
 $("archive-listcount").textContent=groups.length+" acontecimentos · "+list.length+" notícias";
 $("archive-origin").innerHTML=(state.archiveCountry?(flagImage(state.archiveCountry)+" "+safe(state.archiveCountry)):"🌐 Todos os países e Bosch")
   +" · "+state.archiveDays+" dias";
 const part=groups.slice(0,state.archiveVisible);
 $("archive-articles").innerHTML=part.length?part.map(eventCard).join("")
   :'<div class="empty">Não existem notícias arquivadas para estes critérios. Altera os filtros ou limpa a pesquisa.</div>';
 $("archive-more").hidden=state.archiveVisible>=groups.length;
}
"""


def upgrade_dashboard(template):
    if START in template:
        # Already upgraded on a previous run; rewriting the embedded payload
        # should not add duplicate functions or styles.
        return template
    if "function drawArticles(){" not in template or "function drawArchive(){" not in template:
        raise RuntimeError("Dashboard no longer has expected article render functions")
    if "</style>" not in template or "function archiveCategories(){" not in template:
        raise RuntimeError("Dashboard template structure changed unexpectedly")
    updated = template.replace("</style>", START + STYLE + END + "</style>", 1)
    # Replace only the two functions by their following function anchors.
    live = re.compile(r'function drawArticles\(\)\{.*?\n\}(?=\nfunction archiveCategories\(\))', re.S)
    updated, n = live.subn(lambda _: HELPERS + LIVE.rstrip(), updated, count=1)
    if n != 1:
        raise RuntimeError("Could not update live article rendering")
    archived = re.compile(r'function drawArchive\(\)\{.*?\n\}(?=\nfunction render\(\))', re.S)
    updated, n = archived.subn(lambda _: ARCHIVE.rstrip(), updated, count=1)
    if n != 1:
        raise RuntimeError("Could not update archive rendering")
    return updated
