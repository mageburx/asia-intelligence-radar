"""Pure functions for categorization, deduplication, and coverage-trend signals."""
from __future__ import annotations
import hashlib, html, re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
    def handle_data(self,data):
        self.parts.append(data)

def clean_text(value):
    parser=_TextExtractor()
    parser.feed(value or "")
    return re.sub(r"\s+"," ",html.unescape(" ".join(parser.parts))).strip()

def canonical_url(value):
    try:
        p=urlsplit(value)
        params=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True)
                if not (k.lower().startswith("utm_") or k.lower() in {"fbclid","gclid"})]
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/"),urlencode(params),""))
    except ValueError:
        return value

def article_id(country,category,url,title):
    base=canonical_url(url) or title.casefold()
    return hashlib.sha256(f"{country}|{category}|{base}".encode()).hexdigest()[:20]

TOPICS={
 "Baterias":["battery","batteries","catl","lithium","solid-state","电池","固态","リチウム","全固体","Batterie","Akkus","배터리","전고체","電池","बैटरी"],
 "Veículos elétricos":["ev ","evs","electric vehicle","electric car","新能源车","新能源汽车","电动车","電気自動車","bev","phev","elektroauto","elektromobilität","전기차","電動車","इलेक्ट्रिक वाहन","electric mobility"],
 "Condução autónoma":["autonomous","self-driving","autopilot","自动驾驶","自動運転","无人驾驶","autonomes fahren","자율주행","自動駕駛","autonomous mobility"],
 "Tarifas e comércio":["tariff","export","import duty","trade war","关税","出口","贸易","関税","輸出","貿易","Zoll","Außenhandel","수출","관세","關稅","出口","आयात"],
 "Indústria e produção":["factory","plant","production","manufacturing","投资","工厂","产能","制造","生産","工場","投資","Produktion","Fertigung","Werk","공장","생산","製造","工廠","manufacturing hub"],
 "Política industrial":["subsid","industrial policy","regulation","incentive","补贴","产业政策","监管","補助","産業政策","規制","Förderung","Industriepolitik","보조금","산업정책","補助","產業政策"],
 "Semicondutores":["semiconductor","chipmaking","semiconductors","半导体","芯片","半導体","チップ","Halbleiter","반도체","晶片","半導體","semiconductor"],
 "BYD":["byd","比亚迪","比亞迪"],
 "Toyota":["toyota","トヨタ","丰田","豐田"],
 "Honda":["honda","ホンダ","本田"],
 "Nissan":["nissan","日産","日产"],
 "Geopolítica":["diplomac","sanction","security","外交","制裁","安全保障","Außenpolitik","외교","외교부","地緣政治"],
 "Crescimento e PIB":["economy","economic growth","gdp","economia","crescimento económico","pib","经济","經濟","経済","wirtschaft","bip","경제"],
 "Inflação e preços":["inflation","inflação","inflacao","preços","preise","インフレ","物價","물가","通胀","通脹"],
 "Emprego e trabalho":["employment","unemployment","desemprego","emprego","arbeitsmarkt","失業","실업"],
 "Investimento e empresas":["investment","investimento","investitionen","invest","企業","企业","empresas","기업","投資","投资"],
 "Habitação":["habitação","housing","imobiliário","renda","alojamento","wohnungen","주택"],
 "Eleições e governação":["election","parliament","cabinet","选举","国务院","人大","選挙","国会","内閣","Bundestag","Bundesregierung","국회","정부","대통령","立法院","行政院","Lok Sabha","parliamentary"]
}
POLITICAL_WORDS=(
 "politic","parliament","minister","government","policy","diplomac","regulat","sanction","tariff","trade",
 "政治","政府","国务院","国会","政策","外交","选举","改革","关税","法规","习近平","总统","首相",
 "政権","選挙","国会","内閣","外交","規制","法案","総理","安全保障","関税",
 "Bundesregierung","Bundestag","Bundeskanzler","Koalition","Gesetz","politisch","Wahl","Zoll",
 "정부","국회","대통령","정책","선거","관세","외교","총리","법안",
 "台灣","行政院","立法院","總統","政府","政策","選舉","關稅",
 "सरकार","संसद","चुनाव","नीति",
 "legislatur","legislation","national assembly","assembly passes","lawmakers","presidential","cabinet",
 "federal government","policy maker","ministerial","Bundesministerium","Bundeswirtschaft","Bundestagsfraktion",
 "Verordnung","Regierungsentwurf","대통령실","국무회의","입법","국회의원",
 "governo","autarquia","câmara municipal","município","vereador","ministério","parlamento português","primeiro-ministro","orçamento do estado"
)
def relevant_native_politics(title,summary):
    t=f"{title} {summary}".casefold()
    return any(w.casefold() in t for w in POLITICAL_WORDS)
AUTO_WORDS=(
 "automotive","automaker","automobile","car maker","car sales","car production","vehicle",
 "electric car","electric bus","electric truck","electric mobility","ev market","ev battery","battery pack",
 "mobility industry","motor industry","drivetrain","charging infrastructure","self-driving","driverless",
 "hyundai","kia motors","hyundai motor","kia corp","genesis motor","renault korea","samsung motors",
 "auto parts","car parts","parts supplier","engine production","factory production",
 "자동차","전기차","완성차","차량","자동차부품","현대차","기아차","車両","汽車","電動車"
)
def relevant_native_auto(title,summary):
    """Only auto-related items from multi-topic RSS feeds, not unrelated business news."""
    t=f" {title} {summary} ".casefold()
    return any(w.casefold() in t for w in AUTO_WORDS)

ECONOMIC_WORDS=(
 "economia","económico","economica","economy","economic","financeiro","finanças",
 "investimento","investir","investment","inflation","inflação","pib","gdp",
 "exportaç","export","importaç","taxa de juro","banco central","emprego","desemprego",
 "produção","empresas","business","finance","trade","growth",
 "wirtschaft","konjunktur","arbeitsmarkt","inflationsrate",
 "经济","經濟","景気","経済","物価","物價","成長率","貿易","경제","물가","성장률",
 "निवेश","अर्थव्यवस्था"
)
def relevant_native_economy(title,summary=""):
    t=f" {title} {summary} ".casefold()
    return any(w.casefold() in t for w in ECONOMIC_WORDS)

def relevant_braga(title,summary=""):
    """Compatibility layer, Braga as a municipality rather than a surname."""
    from .braga_local import is_braga_local
    return is_braga_local(title,summary,source_id="braga-ominho")

def topic_tags(title,summary=""):
    t=f" {title} {summary} ".casefold()
    return [tag for tag,words in TOPICS.items() if any(w.casefold() in t for w in words)]

# Classification based on public headline wording only, not on confidential company data.
BOSCH_CATEGORIES = {
    "Portugal": ("braga","aveiro","ovar","portugal","portugues","português"),
    "Pessoas": ("stellenabbau","arbeitsplatz","entlassung","betriebsrat","beschäftigt",
                 "layoff","job cut","workforce","workers","hiring","recruit","trabalhador","despedimento","sindicat","warnstreik","streik","mitarbeit","tarifverhandlung"),
    "Indústria": ("rexroth","ctrlx","werk ","werke ","factory","plant ","production",
                  "fertigung","fabrik","manufac","manufactur","logistic","automatis","industrial","indústria",
                  "montagem","robotik","robótica","fornecedor"),
    "Mobilidade": ("mobility","mobilität","automotive","autoindustrie","vehicle","fahrzeug","elektroauto",
                   "e-mobility","powertrain","e-bike","brake","brems","motorização","hydrogen","wasserstoff",
                   "antrieb","mobility aftermarket","adas"),
    "Tecnologia": ("halbleiter","semiconductor","chip","sensor","software","artificial intelligence",
                   "künstliche intelligenz","machine learning","ai ","ia ","tecnologia","forschung","robotics"),
    "Estratégia": ("umsatz","gewinn","ergebnis","strategie","results","profit","investment",
                   "investimento","acquisition","restructur","struktur","turnover","portfolio","growth")
}
def bosch_category(title, summary="", fallback="Estratégia"):
    """Use headline first; fall back to the source theme if no strong match is visible."""
    t=f" {title} ".casefold()
    for cat, words in BOSCH_CATEGORIES.items():
        if any(w in t for w in words):
            return cat
    return fallback

# Bosch also occurs as a surname. Avoid confusing hockey coach Edo Bosch
# (and the painter Hieronymus Bosch) with the Robert Bosch group.
BOSCH_PERSON_EXACT=re.compile(r"\b(?:edo|hieronymus|jeronimo|jerónimo)\s+bosch\b",re.IGNORECASE)

def bosch_name_collision(title,summary=""):
    """Reject known unrelated people named Bosch, including media excerpts."""
    t=f"{title or ''} {summary or ''}"
    return bool(BOSCH_PERSON_EXACT.search(t))

def bosch_relevant(title, summary="", official=False):
    """Bosch Group only: separate the company from unrelated people named Bosch."""
    if bosch_name_collision(title,summary):
        return False
    if official:
        return True
    t=f"{title} {summary}".casefold()
    return bool(re.search(r"\bbosch\b",t))


BOSCH_SIGNALS = {
    "Emprego e reorganização": ("stellenabbau","personalabbau","betriebsrat","entlass","warnstreik",
                                 "layoff","job cut","workforce","despediment","trabalhador","sindicat","mitarbeit"),
    "Bosch Rexroth": ("bosch rexroth","ctrlx"),
    "IA e automação": ("automatis","automation","robot","agentic","künstliche intelligenz",
                       "artificial intelligence","inteligência artificial"),
    "Mobilidade": ("mobility","mobilität","electric vehicle","elektroauto","brake","wasserstoff","hydrogen","adas"),
    "Semicondutores e sensores": ("halbleiter","semiconductor","chip","sensor"),
    "Fábricas e produção": ("fabrik","factory","production","fertigung","werk ","werke ","plant ",
                            "braga","ovar","aveiro","produção"),
    "Resultados e investimentos": ("umsatz","ergebnis","gewinn","revenue","investment","investimento",
                                   "millionen","milliarden","resultados")
}
def bosch_topic_tags(title,summary=""):
    t=f" {title} {summary} ".casefold()
    return [tag for tag,terms in BOSCH_SIGNALS.items() if any(term in t for term in terms)]

def parse_utc(value):
    try:
        d=datetime.fromisoformat(value.replace("Z","+00:00"))
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except (ValueError,TypeError,AttributeError):
        return datetime.fromtimestamp(0,tz=timezone.utc)
def trend_data(articles,now=None):
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    grouped=defaultdict(lambda:{"recent":set(),"previous":set(),"publishers":set()})
    for a in articles:
        when=parse_utc(a.get("published_at") or a.get("first_seen_at",""))
        age=now-when
        if age<timedelta(0) or age>=timedelta(hours=48):
            continue
        period="recent" if age<timedelta(hours=24) else "previous"
        for tag in a.get("topics",[]):
            key=(a["country"],a["category"],tag)
            grouped[key][period].add(a["id"])
            if period=="recent":
                grouped[key]["publishers"].add(a.get("publisher") or a.get("source",""))
    rows=[]
    for (country,category,tag),counts in grouped.items():
        recent=len(counts["recent"])
        previous=len(counts["previous"])
        if not recent:
            continue
        sources=len(counts["publishers"])
        status="Cobertura crescente" if recent>=3 and recent>=previous+2 and sources>=2 else "A monitorizar"
        if previous==0 and recent>=2 and sources>=2:
            status="Tema emergente"
        rows.append({"country":country,"category":category,"topic":tag,"recent":recent,
                     "previous":previous,"publishers":sources,"status":status})
    return sorted(rows,key=lambda x:(x["status"] in ("Tema emergente","Cobertura crescente"),x["recent"]-x["previous"],x["recent"]),reverse=True)
