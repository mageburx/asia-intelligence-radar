"""Hourly ingestion of public RSS metadata. No full-article scraping."""
from __future__ import annotations
import calendar, json, os, time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlencode,urlsplit
import feedparser, requests
from .core import article_id,clean_text,relevant_native_politics,topic_tags,parse_utc

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"articles.json"
STATUS=ROOT/"data"/"status.json"
SOURCES=ROOT/"config"/"sources.json"
USER_AGENT="AsiaIntelligenceRadar/1.0 (RSS headline research; respectful periodic fetching)"
def iso_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
def read_json(path,fallback):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError,ValueError): return fallback
def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    tmp.replace(path)
def feed_url(source):
    if source["kind"]=="rss": return source["url"]
    return "https://news.google.com/rss/search?"+urlencode({
        "q":source["query"],"hl":source["locale"],"gl":source["gl"],"ceid":source["ceid"]
    })
def published_time(entry,fallback):
    dt=entry.get("published_parsed") or entry.get("updated_parsed")
    if dt: return datetime.fromtimestamp(calendar.timegm(dt),tz=timezone.utc).isoformat(timespec="seconds")
    return fallback
def publisher_name(entry,source):
    p=entry.get("source")
    if isinstance(p,dict) and p.get("title"): return clean_text(p["title"])
    return source["name"]
def fetch_source(session,source,now,max_entries=40):
    resp=session.get(feed_url(source),timeout=(10,25),headers={"User-Agent":USER_AGENT})
    resp.raise_for_status()
    feed=feedparser.parse(resp.content)
    if not feed.entries and getattr(feed,"bozo",False): raise ValueError(f"Invalid RSS: {feed.bozo_exception}")
    rows=[]
    for entry in list(feed.entries)[:max_entries]:
        title=clean_text(entry.get("title",""))
        summary=clean_text(entry.get("summary",""))[:750]
        link=entry.get("link","")
        if not title or urlsplit(link).scheme not in {"http","https"}: continue
        if source.get("filter")=="politics" and not relevant_native_politics(title,summary): continue
        published=published_time(entry,now)
        if parse_utc(published)<datetime.now(timezone.utc)-timedelta(days=10): continue
        rows.append({"id":article_id(source["country"],source["category"],link,title),
            "country":source["country"],"category":source["category"],"source":source["name"],
            "source_id":source["id"],"publisher":publisher_name(entry,source),"url":link,
            "original_title":title,"original_summary":summary,"published_at":published,
            "first_seen_at":now,"topics":topic_tags(title,summary),
            "translation_status":"pending","translated_title":"","translated_summary":"",
            "translated_lang":"","last_translation_attempt_at":""})
    return rows

def translate_one(text,target):
    if not text: return ""
    key=os.getenv("DEEPL_API_KEY","").strip()
    if key:
        response=requests.post(os.getenv("DEEPL_API_URL","https://api-free.deepl.com/v2/translate"),
             data={"text":text[:4500],"target_lang":"PT-PT" if target=="pt" else "EN-GB"},
             headers={"Authorization":f"DeepL-Auth-Key {key}"},timeout=20)
        response.raise_for_status()
        return response.json()["translations"][0]["text"]
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source="auto",target=target).translate(text[:4500]) or ""
def translate_backlog(articles,lang,budget):
    now=datetime.now(timezone.utc)
    done=failed=0
    for row in sorted(articles,key=lambda a:a.get("first_seen_at",""),reverse=True):
        if done+failed>=budget or failed>=3: break
        if row.get("translated_lang")==lang and row.get("translation_status")=="translated": continue
        last=parse_utc(row.get("last_translation_attempt_at",""))
        if row.get("translation_status")=="failed" and now-last<timedelta(hours=6): continue
        try:
            row["last_translation_attempt_at"]=iso_now()
            row["translated_title"]=translate_one(row["original_title"],lang)
            row["translated_summary"]=translate_one(row["original_summary"],lang) if row["original_summary"] else ""
            if not row["translated_title"]: raise ValueError("Empty translation")
            row["translation_status"]="translated"
            row["translated_lang"]=lang
            done+=1
            if not os.getenv("DEEPL_API_KEY"): time.sleep(0.6)
        except Exception as exc:
            row["translation_status"]="failed"
            row["translation_error"]=type(exc).__name__
            failed+=1
            print(f"Translation failed: {row['id']} ({type(exc).__name__})")
    return done,failed
def main():
    now=iso_now()
    target=os.getenv("TARGET_LANG","pt").lower().strip()
    if target not in {"pt","en"}: raise SystemExit("TARGET_LANG must be pt or en")
    sources=read_json(SOURCES,[])
    previous=read_json(DATA,[])
    old_status=read_json(STATUS,{})
    index={a["id"]:a for a in previous}
    errors=[]; counts={}; added=0
    with requests.Session() as session:
        for source in sources:
            try:
                found=fetch_source(session,source,now)
                counts[source["id"]]=len(found)
                for row in found:
                    if row["id"] not in index:
                        index[row["id"]]=row
                        added+=1
            except Exception as exc:
                errors.append({"source":source["id"],"error":f"{type(exc).__name__}: {str(exc)[:180]}"})
                print(f"Source error [{source['id']}]: {exc}")
    threshold=datetime.now(timezone.utc)-timedelta(days=60)
    articles=[a for a in index.values() if parse_utc(a.get("first_seen_at",""))>=threshold]
    translated,failed=translate_backlog(articles,target,int(os.getenv("MAX_TRANSLATIONS","40")))
    articles.sort(key=lambda a:a.get("published_at",""),reverse=True)
    save_json(DATA,articles)
    save_json(STATUS,{"last_run":now,"first_run_at":old_status.get("first_run_at") or now,
                      "target_lang":target,"articles_total":len(articles),"added":added,
                      "translated_this_run":translated,"translation_failed_this_run":failed,
                      "sources_total":len(sources),"sources_ok":len(sources)-len(errors),
                      "sources_failed":errors,"items_seen_by_source":counts})
    print(f"Run: {now} | new={added} | stored={len(articles)} | translated={translated} | errors={len(errors)}")
    if sources and len(errors)==len(sources): raise SystemExit("All RSS sources failed")
if __name__=="__main__":
    main()
