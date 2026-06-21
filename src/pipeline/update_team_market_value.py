#!/usr/bin/env python3
"""Squad market value via FotMob (headless browser).

`squad_market_value_m` was hand-researched from Transfermarkt for only 16/48
teams, leaving 32 MISSING (no free no-browser source carries it reliably).
FotMob exposes per-player market values in each team's last-lineup data, so this
derives the matchday-squad value (starters + named subs, which covers nearly all
the valuable players) for every team via a real browser and writes
`squad_market_value_m` (EUR millions) into the squad_style cache.

Market value is slow-changing, so run this on demand (not every matchday). Every
successful run refreshes a backup snapshot; a failed run restores from it so the
field never blanks. Dry-run by default; --write persists.

Usage:
  python3 -m src.pipeline.update_team_market_value            # dry-run
  python3 -m src.pipeline.update_team_market_value --write
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STYLE_CACHE = PROJECT_ROOT / "data" / "source_cache" / "squad_style" / "latest_metrics.json"
BACKUP = PROJECT_ROOT / "data" / "source_cache" / "team_market_value" / "latest.json"
LEAGUE_ID = 77
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_values() -> list[dict]:
    """Per-team matchday squad market value (EUR millions) from FotMob."""
    from playwright.sync_api import sync_playwright

    captured: dict = {"teams": {}}

    def on_resp(r):
        url = r.url
        if f"/api/data/leagues?id={LEAGUE_ID}" in url:
            try:
                captured["lg"] = r.json()
            except Exception:
                pass
        elif "/api/data/teams?id=" in url:
            m = re.search(r"teams\?id=(\d+)", url)
            if m:
                try:
                    captured["teams"][m.group(1)] = r.json()
                except Exception:
                    pass

    rows: list[dict] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA)
        page.on("response", on_resp)
        page.goto(f"https://www.fotmob.com/leagues/{LEAGUE_ID}/overview", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        lg = captured.get("lg")
        if not lg:
            browser.close()
            raise RuntimeError("FotMob league payload not captured")

        id_name: dict[str, str] = {}
        for group in lg["table"][0]["data"]["tables"]:
            table = group.get("table", {})
            for e in (table.get("xg") or []) if isinstance(table, dict) else []:
                tid, nm = e.get("teamId"), e.get("name")
                if tid and nm:
                    id_name[str(tid)] = nm

        for tid, nm in id_name.items():
            try:
                page.goto(f"https://www.fotmob.com/teams/{tid}/overview", wait_until="domcontentloaded", timeout=45000)
            except Exception:
                continue
            # Poll up to ~8s for this team's API response (timing varies per page).
            for _ in range(16):
                if tid in captured["teams"]:
                    break
                page.wait_for_timeout(500)
            tp = captured["teams"].get(tid)
            if not tp:
                continue
            lls = (tp.get("overview", {}) or {}).get("lastLineupStats") or {}
            total = sum((pl.get("marketValue") or 0) for pl in lls.get("starters", []))
            total += sum((pl.get("marketValue") or 0) for pl in lls.get("subs", []))
            if total > 0:
                rows.append({"name": nm, "value_m": round(total / 1e6, 1)})
        browser.close()
    return rows


def write_backup(rows: list[dict], checked_at: str) -> None:
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(json.dumps({
        "metadata": {"checked_at_utc": checked_at, "source": "FotMob", "league_id": LEAGUE_ID,
                     "note": "Fallback squad market value snapshot; restored if a live fetch fails."},
        "teams": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")


def load_backup() -> tuple[list[dict], str | None]:
    if BACKUP.exists():
        d = json.loads(BACKUP.read_text(encoding="utf-8"))
        return d.get("teams", []), (d.get("metadata") or {}).get("checked_at_utc")
    return [], None


def write_cache(rows: list[dict], checked_at: str) -> tuple[int, list[str]]:
    cache = json.loads(STYLE_CACHE.read_text(encoding="utf-8"))
    by_norm = {normalize_team_name(t["team"]): t for t in cache.get("teams", [])}
    updated, missed = 0, []
    for r in rows:
        entry = by_norm.get(normalize_team_name(r["name"]))
        if not entry:
            missed.append(r["name"])
            continue
        entry.setdefault("fields", {})["squad_market_value_m"] = {
            "value": r["value_m"],
            "unit": "EUR millions",
            "status": "available",
            "source_label": "fotmob",
            "source_name": "FotMob matchday squad market value (starters + subs)",
            "source_url": f"https://www.fotmob.com/leagues/{LEAGUE_ID}",
            "checked_at_utc": checked_at,
            "retrieval_method": "fotmob_headless_browser",
        }
        updated += 1
    cache.setdefault("metadata", {})["field_record_count"] = sum(len(t.get("fields", {})) for t in cache["teams"])
    STYLE_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return updated, missed


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive squad market value from FotMob (headless).")
    ap.add_argument("--write", action="store_true", help="Update the squad_style cache")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows, source, checked_at = [], "fotmob_live", now
    try:
        rows = fetch_values()
    except Exception as e:
        print(f"FotMob fetch failed: {type(e).__name__}: {str(e)[:120]}")
    if not rows:
        rows, backup_ts = load_backup()
        source, checked_at = "backup", backup_ts or now
        print(f"falling back to backup: {len(rows)} teams (snapshot {backup_ts})" if rows else "no backup available")
    if not rows:
        raise SystemExit("no market-value data: live fetch failed and no backup file")

    print(f"teams with market value: {len(rows)} (source={source})")
    for r in sorted(rows, key=lambda x: -x["value_m"])[:6]:
        print(f"  {r['name']:16} EUR {r['value_m']}M")

    if not args.write:
        print("(dry-run; pass --write to update the squad_style cache)")
        return
    updated, missed = write_cache(rows, checked_at)
    print(f"updated squad_market_value_m for {updated} teams in {STYLE_CACHE.relative_to(PROJECT_ROOT)}")
    if source == "fotmob_live":
        write_backup(rows, now)
        print(f"backup refreshed: {BACKUP.relative_to(PROJECT_ROOT)}")
    if missed:
        print(f"unmatched FotMob names: {missed}")


if __name__ == "__main__":
    main()
