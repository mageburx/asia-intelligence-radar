"""Only public news verifiably about Braga municipality, Portugal."""
from __future__ import annotations
import re
import unicodedata
from urllib.parse import urlsplit

BRAGA_IDS=frozenset({"braga-diario-minho","braga-correio-minho","braga-ominho","braga-bragatv","braga-vmtv"})

def norm(value):
    value=unicodedata.normalize("NFKD",str(value or "").casefold())
    return "".join(ch for ch in value if not unicodedata.combining(ch))

CITY=re.compile(
    r"\b(?:cidade|concelho|municipio|camara|autarquia|"
    r"assembleia|hospital|tribunal|diocese|arcebispado)\s+(?:municipal\s+)?(?:de|do|da)\s+braga\b"
    r"|\b(?:em|na|no|de|do|da|para|por)\s+braga\b"
    r"|\bbraga\s*(?::|,|[–—-])"
    r"|\bbraga\s+(?:acolhe|recebe|anuncia|celebra|regista|inaugura|aprova|apresenta|"
    r"promove|abre|lanca|vive|assinala|investe|prepara|arranca|avanca|"
    r"ganha|reforca|cria|realiza|reune|organiza|disponibiliza|tem|elege)\b")
LANDMARK=re.compile(
    r"\b(?:theatro circo|forum braga|braga parque|startup braga|hospital de braga|"
    r"tub\b|agere\b|se de braga|bom jesus do monte|universidade do minho.*gualtar|"
    r"parque da rodovia|gualtar|sao vicente|sao victor|sao lazaro|maximinos|"
    r"lamacaes|palmeira|priscos|dume|frossos|sequeira|semelhe|tadim|fraiao|"
    r"nogueiro|esporaes|ferreiros|real de braga|braga retail center)\b")
DISTRICT=re.compile(r"\b(?:distrito|distrital|regiao)\s+(?:de\s+)?braga\b")
BRAZIL=re.compile(
    r"\b(?:brasil|brasileir[oa]s?|manaus|amazonas|sao paulo|rio de janeiro|"
    r"brasilia|distrito federal|congresso nacional|senado federal|"
    r"camara dos deputados|prefeitura|prefeito|ibge|stf|"
    r"maranhao|pernambuco|ceara|mato grosso|paraiba)\b")
SPORT=re.compile(
    r"\b(?:sc\s*braga|s\.c\.\s*braga|sporting clube de braga|"
    r"futebol|football|liga portugal|golos?|europa league|champions league|"
    r"ricardo horta|pontape de saida)\b")
POLITICS=re.compile(r"\b(?:camara|autarquia|municipio|vereador|assembleia municipal|junta de freguesia|freguesia|eleic|autarca|executivo municipal|orcamento municipal|oposicao|deputados?|presidente da camara|partido|psd|chega)\b")
MOBILITY=re.compile(r"\b(?:mobilidade|transporte|autocarro|tub\b|transito|estacionamento|ciclovia|rodovia|estrada|via rapida|mobilidade eletrica|veiculo eletrico|carregamento|automovel|acessibilidade|passes)\b")
ECONOMY=re.compile(r"\b(?:economia|empresa|emprego|investimento|comercio|comerciante|industria|industrial|fabrica|bosch|habitacao|construcao|mercado imobiliario|negocio|loja|startup|turismo|financeiro|financiamento|empreendedorismo|obra|trabalhadores|desemprego)\b")
STRONG_SUMMARY=re.compile(r"\b(?:camara municipal de braga|municipio de braga|concelho de braga|cidade de braga|autarquia de braga)\b")

def is_braga_local(title, summary="", url="", source_id=""):
    if source_id not in BRAGA_IDS:
        return False
    if (urlsplit(url or "").hostname or "").endswith(".br"):
        return False
    t,s=norm(title),norm(summary)
    if BRAZIL.search(t) or SPORT.search(t):
        return False
    if DISTRICT.search(t) and not LANDMARK.search(t) and not CITY.search(DISTRICT.sub("",t)):
        return False
    if LANDMARK.search(t) or CITY.search(t):
        return True
    return bool(STRONG_SUMMARY.search(s) and not BRAZIL.search(s))

def classify_braga(title, summary=""):
    t=norm(title)
    if POLITICS.search(t): return "Política"
    if MOBILITY.search(t): return "Automóvel"
    if ECONOMY.search(t): return "Economia"
    return "Atualidade"

def keep_record(article):
    if article.get("country")!="Braga":
        return True
    return is_braga_local(article.get("original_title",""),
                          article.get("original_summary",""),
                          article.get("url",""),article.get("source_id",""))

def filter_records(articles):
    return [a for a in articles if keep_record(a)]
