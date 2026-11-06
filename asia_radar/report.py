"""Update self-contained dashboard HTML using the currently stored news metadata."""
from __future__ import annotations
import json,re
from datetime import datetime,timedelta,timezone
from pathlib import Path
from .core import parse_utc,trend_data
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"articles.json"
STATUS=ROOT/"data"/"status.json"
OUT=ROOT/"docs"/"index.html"
def read(path,fallback):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError,ValueError):return fallback
def make_payload(articles,status,now=None):
    now=now or datetime.now(timezone.utc)
    recent=[x for x in articles if timedelta(0)<=now-parse_utc(x.get("published_at",""))<timedelta(hours=24)]
    counts={}
    for country in ["China","Japão","Alemanha","Coreia do Sul","Taiwan","Índia","Singapura"]:
        for category in ("Política","Automóvel"):
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
    return {"articles":articles[:4500],"status":status,"trends":trends,"counts24":counts,
            "generated_at":now.isoformat(timespec="seconds")}
def main():
    articles=read(DATA,[])
    status=read(STATUS,{})
    payload=json.dumps(make_payload(articles,status),ensure_ascii=False,separators=(",",":"))
    payload=payload.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    template=OUT.read_text(encoding="utf-8")
    marker=r'(<script id="payload" type="application/json">).*?(</script>)'
    if not re.search(marker,template,re.S): raise RuntimeError("Missing dashboard payload marker")
    page=re.sub(marker,lambda m:m.group(1)+payload+m.group(2),template,count=1,flags=re.S)
    OUT.write_text(page,encoding="utf-8")
    print(f"Dashboard saved: {OUT} ({len(articles)} articles)")
if __name__=="__main__":
    main()
