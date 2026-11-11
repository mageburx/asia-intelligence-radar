"""Versioned, idempotent Bosch analysis UI: inserted at dashboard report time."""
from __future__ import annotations
MARKER="/* BOSCH_GROUP_ANALYSIS_V1 */"
STYLE=r"""
/* BOSCH_GROUP_ANALYSIS_V1 */
.bga{margin:16px 0 0;padding:15px;border-radius:14px;border:1px solid #3b5c63;background:linear-gradient(145deg,#142b36,#101b2a)}
.bga-head{display:flex;align-items:center;justify-content:space-between;gap:9px;flex-wrap:wrap;margin-bottom:14px}
.bga-head h3{font-size:20px;margin:0;letter-spacing:-.03em}
.bga-head p{font-size:11px;color:#a7bdc8;margin:4px 0 0}
.bga-eyebrow{color:#78ddc8;font-size:10px;font-weight:700;letter-spacing:.11em;text-transform:uppercase}
.bga-link{color:#a5f1df;font-size:12px;border:1px solid #44766e;border-radius:9px;padding:7px 10px}
.bga-tabs{display:flex;gap:6px;margin-bottom:12px;overflow-x:auto}
.bga-tabs button{background:#172b3b;border:1px solid #375565;border-radius:9px;padding:10px 12px;white-space:nowrap;color:#c1d5db;font-size:12px;font-weight:700}
.bga-tabs button[aria-selected="true"]{background:#215149;border-color:#75ddc6;color:#fff}
.bga-pane[hidden]{display:none!important}
.bga-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.bga-stat{background:#0e2030;border:1px solid #2b4654;border-radius:10px;padding:12px;min-width:0}
.bga-stat small{display:block;font-size:11px;color:#aabfc9}
.bga-stat strong{display:block;margin:6px 0 4px;font-size:22px;color:#edf9f5;letter-spacing:-.04em}
.bga-stat span{display:block;font-size:11px;color:#a7d4cb}
.bga-insights{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:9px}
.bga-insight,.bga-sector{background:#132939;border:1px solid #32505c;border-radius:10px;padding:12px}
.bga-insight strong,.bga-sector h4{color:#e6f3f2;font-size:13px;margin:0}
.bga-insight p,.bga-sector p{font-size:12px;color:#adc5cf;line-height:1.55;margin:7px 0 0}
.bga-note{color:#a5bac7;font-size:11px;line-height:1.65;margin:12px 0 0}
.bga-note a{color:#8ff0da;text-decoration:underline}
.bga-sectors{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.bga-sector strong{font-size:19px;color:#f5faf7}
.bga-sector .bga-delta{margin-left:10px;color:#bad0d8;font-size:12px}
.bga-categories{display:grid;gap:7px;margin:11px 0}
.bga-cat{display:grid;grid-template-columns:118px minmax(0,1fr) 27px;gap:8px;align-items:center;font-size:11px;color:#deedec}
.bga-track{background:#263b48;height:7px;border-radius:50px;overflow:hidden}
.bga-track span{display:block;background:#72d5c0;height:100%;border-radius:50px}
.bga-topics{display:flex;flex-wrap:wrap;gap:5px;margin:10px 0}
.bga-topics span{font-size:11px;background:#193c39;color:#b8e7da;padding:4px 8px;border-radius:7px}
.bga-news h4{font-size:13px;margin:14px 0 7px}
.bga-story{padding:9px 0;border-top:1px solid #294652;display:grid;gap:3px}
.bga-story a{font-size:12px;color:#dcf6ea;text-decoration:underline;text-decoration-color:#3c7f73;overflow-wrap:anywhere}
.bga-story small{font-size:11px;color:#a6c1cb}
@media(max-width:760px){.bga-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.bga-insights,.bga-sectors{grid-template-columns:1fr}}
@media(max-width:480px){.bga{padding:11px}.bga-tabs button{padding:9px 8px;font-size:11px}.bga-stat strong{font-size:19px}.bga-head h3{font-size:18px}.bga-cat{grid-template-columns:95px minmax(0,1fr) 22px}}
"""
PANEL=r"""
<section class="bga" id="bosch-group-analysis" aria-labelledby="bga-title">
<div class="bga-head"><div><span class="bga-eyebrow">Bosch Group · inteligência empresarial</span>
<h3 id="bga-title">Análise do Grupo</h3>
<p>Indicadores oficiais com data · monitorização de notícias de hora a hora</p></div>
<a class="bga-link" href="https://www.bosch.pt/imprensa/2026/resultados-semestrais-2026-bosch-reafirma-previsoes/" target="_blank" rel="noopener noreferrer">Dados oficiais ↗</a></div>
<div class="bga-tabs" role="tablist" aria-label="Vistas da análise do grupo">
<button type="button" role="tab" aria-selected="true" data-bga="general">Visão geral</button>
<button type="button" role="tab" aria-selected="false" data-bga="sectors">Áreas de negócio</button>
<button type="button" role="tab" aria-selected="false" data-bga="monitor">Sinais do radar</button></div>
<div class="bga-pane" data-bga-pane="general"><div class="bga-metrics" id="bga-metrics"></div><div class="bga-insights" id="bga-insights"></div><p class="bga-note" id="bga-note"></p></div>
<div class="bga-pane" data-bga-pane="sectors" hidden><div class="bga-sectors" id="bga-sectors"></div><p class="bga-note">Resultados do 1.º semestre de 2026 e variação homóloga, não previsões. Fontes: relatório oficial Bosch.</p></div>
<div class="bga-pane" data-bga-pane="monitor" hidden><div class="bga-metrics" id="bga-coverage"></div><div class="bga-categories" id="bga-categories"></div><div class="bga-topics" id="bga-topics"></div><div class="bga-news"><h4>Notícias a acompanhar</h4><div id="bga-stories"></div></div><p class="bga-note" id="bga-news-note"></p></div>
</section>
"""
SCRIPT=r"""
<script>
(function(){
 "use strict";
 const root=document.getElementById("bosch-group-analysis");
 if(!root)return;
 const el=id=>document.getElementById(id);
 const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
 const a=JSON.parse(document.getElementById("payload").textContent).bosch_analysis||{};
 const f=a.facts||{},h=f.h1||{},yr=f.year2025||{},m=a.monitor||{};
 const n=(v,dec=1)=>Number(v||0).toLocaleString("pt-PT",{maximumFractionDigits:dec});
 const card=(label,value,note)=>'<div class="bga-stat"><small>'+esc(label)+'</small><strong>'+esc(value)+'</strong><span>'+esc(note)+'</span></div>';
 el("bga-metrics").innerHTML=[
  card("Faturação · 1.º sem. 2026",n(h.sales)+" mil M€","+"+n(h.sales_yoy)+"% homólogo"),
  card("Margem EBIT operacional",n(h.operating_margin)+"%","Anterior: "+n(h.prior_margin)+"%"),
  card("Colaboradores · jun. 2026",n(h.headcount,0),"Dez. 2025: "+n(h.headcount_dec_2025,0)),
  card("Faturação · 2025",n(yr.sales)+" mil M€","EBIT: "+n(yr.operating_ebit)+" mil M€")
 ].join("");
 el("bga-insights").innerHTML=(f.assessment||[]).map(x=>'<div class="bga-insight"><strong>'+esc(x.title)+'</strong><p>'+esc(x.text)+'</p></div>').join("");
 el("bga-note").innerHTML="Fonte: resultados oficiais publicados em "+esc(f.report_date)+
   ". Perspetiva 2026: vendas +"+n((h.outlook_sales||[])[0],0)+"% a +"+n((h.outlook_sales||[])[1],0)+
   "%; margem EBIT "+n((h.outlook_margin||[])[0],0)+"% a "+n((h.outlook_margin||[])[1],0)+
   "%. As previsões não são resultados. <a target='_blank' rel='noopener noreferrer' href='"+esc(f.report_url)+"'>Resultados semestrais</a> · "+
   "<a target='_blank' rel='noopener noreferrer' href='"+esc(f.annual_url)+"'>Relatório anual 2025</a>.";
 el("bga-sectors").innerHTML=(f.sectors||[]).map(s=>'<div class="bga-sector"><h4>'+esc(s.name)+
   '</h4><strong>'+n(s.sales)+' mil M€</strong><span class="bga-delta">'+(s.yoy>0?"+":"")+n(s.yoy)+
   '% homólogo</span><p>'+esc(s.note)+'</p></div>').join("");
 const comp=m.comparison_ready?"Anterior: "+n(m.previous_events,0)+" acontecimentos":"A comparação de 7 dias ainda não tem histórico suficiente";
 el("bga-coverage").innerHTML=[
  card("Acontecimentos · 7 dias",n(m.events,0),comp),
  card("Notícias recolhidas",n(m.articles,0),"Últimos 7 dias"),
  card("Publicadores",n(m.publishers,0),"Não equivale a fontes independentes"),
  card("Comunicados oficiais",n(m.official_articles,0),"Incluídos nas notícias")
 ].join("");
 const cats=m.categories||{},maximum=Math.max(1,...Object.values(cats).map(Number));
 el("bga-categories").innerHTML=Object.entries(cats).map(([cat,v])=>
   '<div class="bga-cat"><span>'+esc(cat)+'</span><div class="bga-track"><span style="width:'+
   Math.round(100*v/maximum)+'%"></span></div><strong>'+esc(v)+'</strong></div>').join("");
 el("bga-topics").innerHTML=(m.top_topics||[]).map(t=>'<span>'+esc(t.topic)+' · '+esc(t.events)+'</span>').join("");
 const date=d=>d?new Date(d).toLocaleDateString("pt-PT",{day:"2-digit",month:"short"}):"";
 const link=u=>/^https:\/\//.test(u||"")?u:"";
 el("bga-stories").innerHTML=(m.focus||[]).map(x=>'<div class="bga-story"><a href="'+esc(link(x.url))+
   '" target="_blank" rel="noopener noreferrer">'+esc(x.title)+'</a><small>'+
   esc(x.category)+' · '+esc(x.publisher)+' · '+esc(date(x.date))+'</small></div>').join("")
   ||'<p class="bga-note">Sem notícias recentes.</p>';
 el("bga-news-note").textContent="O radar mede cobertura das fontes RSS monitorizadas, não o desempenho financeiro real, sentimento confirmado ou risco individual para trabalhadores. "+
   (m.comparison_ready?"A comparação usa a semana anterior.":"Os dados ainda não cobrem duas semanas completas.");
 root.querySelectorAll("[data-bga]").forEach(tab=>tab.addEventListener("click",()=>{
   root.querySelectorAll("[data-bga]").forEach(t=>t.setAttribute("aria-selected",String(t===tab)));
   root.querySelectorAll("[data-bga-pane]").forEach(p=>{p.hidden=p.dataset.bgaPane!==tab.dataset.bga;});
 }));
})();
</script>
"""

def upgrade_bosch_group_dashboard(html):
    if MARKER in html:
        return html
    start=html.find('<section class="bosch-picker" id="bosch-view"')
    if start<0: raise RuntimeError("Bosch navigation missing")
    end=html.find("</section>",start)
    if end<0 or 'id="bosch-categories"' not in html[start:end]:
        raise RuntimeError("Bosch categories missing")
    if "</style>" not in html or "</body>" not in html:
        raise RuntimeError("Dashboard anchors missing")
    html=html[:end]+PANEL+html[end:]
    return html.replace("</style>",STYLE+"</style>",1).replace("</body>",SCRIPT+"</body>",1)
