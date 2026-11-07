"""Merge an hourly collector snapshot with newer data already on main.

The workflow rebases by reconstructing generated files on top of the latest
remote source, rather than text-merging JSON and the embedded HTML payload.
"""
from __future__ import annotations

import sys
from pathlib import Path
from .collector import DATA, STATUS, ARCHIVE_DAYS, read_json, save_json, retain_archive


TRANSLATED = ("translated_title", "translated_summary", "translated_lang",
              "translation_status", "last_translation_attempt_at")


def combine_articles(current, collected):
    """Union by article ID, keeping any successful translation already saved."""
    result = {}
    for article in current:
        if article.get("id"):
            result[article["id"]] = dict(article)
    for incoming in collected:
        ident = incoming.get("id")
        if not ident:
            continue
        old = result.get(ident)
        if old is None:
            result[ident] = dict(incoming)
            continue
        merged = dict(old)
        merged.update(incoming)
        # A successful translation must never regress to pending or failed.
        old_translated = old.get("translation_status") == "translated"
        incoming_translated = incoming.get("translation_status") == "translated"
        if old_translated and not incoming_translated:
            for k in TRANSLATED:
                merged[k] = old.get(k, "")
        if old.get("first_seen_at") and incoming.get("first_seen_at"):
            merged["first_seen_at"] = min(old["first_seen_at"], incoming["first_seen_at"])
        result[ident] = merged
    rows = retain_archive(result.values())
    return sorted(rows, key=lambda a: a.get("published_at", ""), reverse=True)


def reconcile_files(snapshot_articles, snapshot_status):
    latest = read_json(DATA, [])
    collected = read_json(snapshot_articles, [])
    rows = combine_articles(latest, collected)
    current_status = read_json(STATUS, {})
    new_status = read_json(snapshot_status, {})
    # Do not roll back last-run health information if a newer run already landed.
    status = (new_status if new_status.get("last_run", "") >= current_status.get("last_run", "")
              else current_status)
    status["articles_total"] = len(rows)
    status["archive_days"] = ARCHIVE_DAYS
    save_json(DATA, rows)
    save_json(STATUS, status)
    print(f"Reconciled article archive: {len(latest)} latest + {len(collected)} collected => {len(rows)} retained")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m asia_radar.reconcile SNAPSHOT_ARTICLES SNAPSHOT_STATUS")
    reconcile_files(Path(sys.argv[1]), Path(sys.argv[2]))
