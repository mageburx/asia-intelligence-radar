"""Update self-contained dashboard HTML using the currently stored news metadata."""
from __future__ import annotations
import csv,json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .core import parse_utc,trend_data
from .events import group_events, grouping_stats
from .dashboard_upgrade import upgrade_dashboard
from .geo_upgrade import upgrade_geo_dashboard
from .braga_local import filter_records
from .braga_upgrade import upgrade_braga_dashboard
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"articles.json"
STATUS=ROOT/"data"/"status.json"
OUT=ROOT/"docs"/"index.html"
ARCHIVE_CSV=ROOT/"docs"/"arquivo-30-dias.csv"
def read(path,fallback):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError,ValueError):return fallback
def make_payload(articles,status,now=None):
    now=now or datetime.now(timezone.utc)
    articles=filter_records(articles)
    recent=[x for x in articles if timedelta(0)<=now-parse_utc(x.get("published_at",""))<timedelta(hours=24)]
    counts={}
    for country in ["China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura","Portugal","Braga"]:
        for category in ("Política","Automóvel","Economia","Atualidade"):
            counts[f"{country}|{category}"]=sum(1 for a in recent if a.get("country")==country and a.get("category")==category)
    trends=trend_data(articles,now)
    first_run=status.get("first_run_at")
    # New markets need their own 48-hour observation window, independent of the bot's original start.
    country_first={}
    for a in articles:
        country=a.get("country")
        seen=parse_utc(a.get("first_seen_at",""))
        if country and (country not in country_first or seen<country_first[country]):
            country_first[country]=seen
    for trend in trends:
        started=country_first.get(trend["country"])
        if started and now-started<timedelta(hours=48):
            trend["status"]="Histórico inicial"
    grouped=group_events(articles)
    return {"articles":grouped,"status":status,"trends":trends,"counts24":counts,
            "event_stats":grouping_stats(grouped),
            "generated_at":now.isoformat(timespec="seconds")}
def safe_csv(value):
    """Avoid spreadsheet formula execution in untrusted RSS titles or excerpts."""
    s=str(value or "")
    if s.lstrip().startswith(("=","+","-","@")) or s.startswith(("\\t","\\r")):
        return "'"+s
    return s

def export_archive_csv(articles, path=ARCHIVE_CSV):
    columns=("published_at","country","category","publisher","source_type",
             "translated_title","original_title","translated_summary","original_summary","url")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f,delimiter=";")
        writer.writerow(columns)
        for a in articles:
            writer.writerow([safe_csv(a.get(k,"")) for k in columns])

def main():
    articles=filter_records(read(DATA,[]))
    status=read(STATUS,{})
    export_archive_csv(articles)
    payload=json.dumps(make_payload(articles,status),ensure_ascii=False,separators=(",",":"))
    payload=payload.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    template=upgrade_braga_dashboard(upgrade_geo_dashboard(upgrade_dashboard(OUT.read_text(encoding="utf-8"))))
    marker=r'(<script id="payload" type="application/json">).*?(</script>)'
    if not re.search(marker,template,re.S): raise RuntimeError("Missing dashboard payload marker")
    page=re.sub(marker,lambda m:m.group(1)+payload+m.group(2),template,count=1,flags=re.S)
    OUT.write_text(page,encoding="utf-8")
    print(f"Dashboard saved: {OUT} ({len(articles)} articles)")
if __name__=="__main__":
    main()
