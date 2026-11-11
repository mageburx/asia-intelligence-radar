"""Bosch corporate analysis, strictly separating dated official facts from RSS counts."""
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .core import parse_utc

FACTS=Path(__file__).resolve().parents[1]/"config"/"bosch_facts.json"
CATS=("Estratégia","Mobilidade","Indústria","Tecnologia","Pessoas","Portugal")

def load_facts():
    return json.loads(FACTS.read_text(encoding="utf-8"))

def analyze_bosch(articles,status=None,now=None):
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    status=status or {}
    data=[a for a in articles if a.get("country")=="Bosch"]
    def period(days_before,days_after):
        return [a for a in data if timedelta(days=days_before)<=
                now-parse_utc(a.get("published_at",""))<timedelta(days=days_after)]
    latest=period(0,7)
    prev=period(7,14)
    def eid(a): return a.get("event_id") or a.get("id") or a.get("url")
    def count(rows): return len({eid(a) for a in rows if eid(a)})
    categories={c:count(a for a in latest if a.get("category")==c) for c in CATS}
    publishers={a.get("publisher") or a.get("source") for a in latest}
    publishers.discard(None); publishers.discard("")
    topics=defaultdict(set)
    for a in latest:
        for topic in a.get("topics") or ():
            if topic and eid(a): topics[topic].add(eid(a))
    top=[{"topic":t,"events":len(v)} for t,v in sorted(
        topics.items(),key=lambda item:(-len(item[1]),item[0])) if len(v)>=2][:6]
    order={"Portugal":0,"Pessoas":1,"Indústria":2,"Estratégia":3,"Mobilidade":4,"Tecnologia":5}
    sorted_news=sorted(latest,key=lambda a:a.get("published_at",""),reverse=True)
    sorted_news.sort(key=lambda a:order.get(a.get("category"),10))
    focus=[]; used=set()
    for a in sorted_news:
        if eid(a) in used: continue
        used.add(eid(a))
        title=(a.get("translated_title") if a.get("translation_status")=="translated"
               and a.get("translated_title") else a.get("original_title",""))
        focus.append({"title":title,"category":a.get("category",""),
                      "publisher":a.get("publisher") or a.get("source",""),
                      "date":a.get("published_at",""),"url":a.get("url","")})
        if len(focus)==5: break
    first=parse_utc(status.get("first_run_at",""))
    ready=now-first>=timedelta(days=14)
    return {
       "facts":load_facts(),
       "monitor":{"articles":len(latest),"events":count(latest),
          "previous_events":count(prev) if ready else None,
          "comparison_ready":ready,"publishers":len(publishers),
          "official_articles":sum(a.get("source_type")=="Comunicado oficial" for a in latest),
          "categories":categories,"top_topics":top,"focus":focus,
          "last_run":status.get("last_run","")}
    }
