"""Conservative headline-level grouping for public news metadata.

Groups are presentation-only; original articles and source URLs stay intact.
No ML API or external network calls are required.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
import unicodedata
from collections import defaultdict
from datetime import timedelta

from .core import canonical_url, parse_utc

STOPWORDS = frozenset("""
a an and are as at be by for from has have in into is it its of on or the their this
to was were will with after amid over about says say new latest report reports update
o a os as um uma uns umas de do da dos das em no na nos nas e ou para por com sem
que se ao aos à às seu sua seus suas foi são mais sobre após entre
der die das den dem des ein eine einer einen einem und auf für mit von vom zum zur
ist im am zu nach als bei aus wird werden neue neuen neuer neues
le la les des un une du et en dans sur pour par avec au aux est sont
""".split())

# A suffix from a headline aggregator often identifies the publisher, not the event.
SUFFIX = re.compile(r"\s(?:-|\||—)\s")
TOKEN = re.compile(r"[\w]+", re.UNICODE)


def headline_forms(article):
    """Produce conservative comparable headline token sets, original and translated."""
    options = [article.get("original_title", "")]
    if article.get("translation_status") == "translated":
        options.append(article.get("translated_title", ""))
    forms = []
    for title in options:
        if not title:
            continue
        parts = SUFFIX.split(title.strip())
        if len(parts) > 1 and len(parts[-1].split()) <= 6 and len(parts[-1]) <= 65:
            title = " - ".join(parts[:-1])
        normalized = unicodedata.normalize("NFKD", title.casefold())
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        words = [w for w in TOKEN.findall(normalized) if len(w) > 1 and w not in STOPWORDS]
        words = tuple(dict.fromkeys(words))
        if len(words) >= 3 and words not in forms:
            forms.append(words)
        elif len(words) == 1 and len(words[0]) >= 8 and words not in forms:
            # An unsegmented CJK headline can match exactly, but never fuzzily.
            forms.append(words)
    return forms


def same_event(a_forms, b_forms):
    """Require near-identical informative wording, including matching numeric details."""
    for a in a_forms:
        for b in b_forms:
            if a == b:
                return True
            if len(a) < 5 or len(b) < 5:
                continue
            a_nums = {w for w in a if w.isdigit()}
            b_nums = {w for w in b if w.isdigit()}
            if a_nums != b_nums:
                continue
            shared = len(set(a) & set(b))
            union = len(set(a) | set(b))
            if (shared >= 5 and shared / union >= .76
                    and shared / min(len(a), len(b)) >= .85
                    and SequenceMatcher(None, a, b, autojunk=False).ratio() >= .75):
                return True
    return False


def group_events(articles, max_age_hours=48):
    """Attach event_id to each *copy*; do not modify historical source records.

    Only match within the same country and category. Bosch is a separate
    company namespace; items from different Bosch categories are kept apart.
    """
    rows = [dict(article) for article in articles]
    ordered = sorted(rows, key=lambda a: a.get("published_at", ""), reverse=True)
    groups = defaultdict(list)
    for article in ordered:
        article["event_id"] = article.get("id", "")
        scope = (article.get("country", ""), article.get("category", ""))
        stamp = parse_utc(article.get("published_at", ""))
        forms = headline_forms(article)
        url = canonical_url(article.get("url", ""))
        selected = None
        for cluster in groups[scope]:
            lead = cluster["lead"]
            if abs(stamp - cluster["date"]) > timedelta(hours=max_age_hours):
                continue
            # Same canonical URL is stronger evidence than headline overlap.
            if url and url == cluster["url"]:
                selected = cluster
                break
            if forms and same_event(forms, cluster["forms"]):
                selected = cluster
                break
        if selected is None:
            groups[scope].append({
                "lead": article, "date": stamp, "url": url, "forms": forms
            })
        else:
            article["event_id"] = selected["lead"]["event_id"]
    return rows


def grouping_stats(articles):
    clusters = defaultdict(list)
    for a in articles:
        clusters[a.get("event_id") or a.get("id")].append(a)
    return {
        "events": len(clusters),
        "grouped_events": sum(len(v) > 1 for v in clusters.values()),
        "secondary_articles": sum(max(len(v) - 1, 0) for v in clusters.values()),
    }
