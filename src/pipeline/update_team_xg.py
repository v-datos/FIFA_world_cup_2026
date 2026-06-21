#!/usr/bin/env python3
"""Team xG extractor via FotMob (headless browser).

No free *no-browser* source exposes 2026 World Cup team xG: FBref and Sofascore
are Cloudflare/IP-blocked, API-Football carries no World Cup xG, and ESPN has
none. FotMob does expose it, behind a signed request header that a real browser
generates automatically. This loads the FotMob World Cup league page with
Playwright, intercepts the league JSON, and writes per-team
`expected_goals_per_90` / `expected_goals_conceded_per_90` into the squad_style
cache (the per-90 value is the team's cumulative xG divided by matches played).

This path is fragile by nature: it depends on FotMob's page structure and may be
blocked from datacenter IPs. The matchday workflow runs it with `|| true` so a
block never breaks the rest of the refresh. Dry-run by default; --write persists.

Usage:
  python3 -m src.pipeline.update_team_xg            # dry-run (prints)
  python3 -m src.pipeline.update_team_xg --write
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STYLE_CACHE = PROJECT_ROOT / "data" / "source_cache" / "squad_style" / "latest_metrics.json"
# Dedicated fallback snapshot of just the xG values, refreshed on every
# successful scrape and restored into the cache if a later FotMob fetch fails.
BACKUP = PROJECT_ROOT / "data" / "source_cache" / "team_xg" / "latest.json"
LEAGUE_ID = 77  # FotMob FIFA World Cup
LEAGUE_URL = f"https://www.fotmob.com/leagues/{LEAGUE_ID}/overview"
LEAGUE_API = f"/api/data/leagues?id={LEAGUE_ID}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_league() -> dict:
    """Load the FotMob league page in a headless browser and return its JSON."""
    from playwright.sync_api import sync_playwright

    cap: dict = {}

    def on_resp(r):
        if LEAGUE_API in r.url:
            try:
                cap["lg"] = r.json()
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA)
        page.on("response", on_resp)
        page.goto(LEAGUE_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)
        browser.close()

    if "lg" not in cap:
        raise RuntimeError("FotMob league payload not captured (blocked or page changed)")
    return cap["lg"]


def team_xg(lg: dict) -> list[dict]:
    """Per-team xG/90 + xGA/90 across all group tables that have xG data."""
    tables = lg["table"][0]["data"]["tables"]
    rows: list[dict] = []
    for group in tables:
        table = group.get("table", {})
        for e in (table.get("xg") or []) if isinstance(table, dict) else []:
            mp = e.get("played") or 0
            if mp:
                rows.append({
                    "name": e.get("name"),
                    "xg90": round(e["xg"] / mp, 2),
                    "xga90": round(e["xgConceded"] / mp, 2),
                    "mp": mp,
                })
    return rows


def write_backup(rows: list[dict], checked_at: str) -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(json.dumps({
        "metadata": {
            "checked_at_utc": checked_at,
            "source": "FotMob",
            "league_id": LEAGUE_ID,
            "note": "Fallback xG snapshot; restored into squad_style if a live FotMob fetch fails.",
        },
        "teams": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")


def load_backup() -> tuple[list[dict], str | None]:
    if BACKUP.exists():
        d = json.loads(BACKUP.read_text(encoding="utf-8"))
        return d.get("teams", []), (d.get("metadata") or {}).get("checked_at_utc")
    return [], None


def write_cache(rows: list[dict], checked_at: str | None = None) -> tuple[int, list[str]]:
    cache = json.loads(STYLE_CACHE.read_text(encoding="utf-8"))
    by_norm = {normalize_team_name(t["team"]): t for t in cache.get("teams", [])}
    now = checked_at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def field(value: float, n: int) -> dict:
        return {
            "value": value,
            "unit": "xG per 90",
            "status": "available",
            "source_label": "fotmob",
            "source_name": f"FotMob World Cup team table (avg of {n} matches)",
            "source_url": f"https://www.fotmob.com/leagues/{LEAGUE_ID}",
            "checked_at_utc": now,
            "retrieval_method": "fotmob_headless_browser",
        }

    updated, missed = 0, []
    for r in rows:
        entry = by_norm.get(normalize_team_name(r["name"]))
        if not entry:
            missed.append(r["name"])
            continue
        fields = entry.setdefault("fields", {})
        fields["expected_goals_per_90"] = field(r["xg90"], r["mp"])
        fields["expected_goals_conceded_per_90"] = field(r["xga90"], r["mp"])
        updated += 1
    cache.setdefault("metadata", {})["field_record_count"] = sum(len(t.get("fields", {})) for t in cache["teams"])
    STYLE_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return updated, missed


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive team xG from FotMob (headless).")
    ap.add_argument("--write", action="store_true", help="Update the squad_style cache")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, source, checked_at = [], "fotmob_live", now
    try:
        rows = team_xg(fetch_league())
    except Exception as e:  # network/page/parse failure — fall back to the backup
        print(f"FotMob fetch failed: {type(e).__name__}: {str(e)[:120]}")
    if not rows:
        rows, backup_ts = load_backup()
        source, checked_at = "backup", backup_ts or now
        print(f"falling back to xG backup: {len(rows)} teams (snapshot {backup_ts})"
              if rows else "no xG backup available")
    if not rows:
        raise SystemExit("no xG data: live FotMob fetch failed and no backup file exists")

    print(f"teams with xG: {len(rows)} (source={source})")
    for r in sorted(rows, key=lambda x: -x["xg90"])[:6]:
        print(f"  {r['name']:16} xG/90={r['xg90']} xGA/90={r['xga90']} (MP={r['mp']})")

    if not args.write:
        print("(dry-run; pass --write to update the squad_style cache)")
        return
    updated, missed = write_cache(rows, checked_at)
    print(f"updated xG for {updated} teams in {STYLE_CACHE.relative_to(PROJECT_ROOT)}")
    if source == "fotmob_live":
        write_backup(rows, now)
        print(f"backup refreshed: {BACKUP.relative_to(PROJECT_ROOT)}")
    if missed:
        print(f"unmatched FotMob names (no cache team): {missed}")


if __name__ == "__main__":
    main()
