#!/usr/bin/env python3
"""AI tactical headline generator for the FIFA World Cup 2026 dashboard.

Uses Claude (Anthropic API) to write a real tactical headline + 3 insights for a
match from the structured data the dashboard already has — team Elo ratings, a
win expectancy, ESPN style metrics (possession/shots/goals), and formations.
Replaces the generic "Baseline preview pending for X vs Y" stub.

Designed to run in the matchday refresh: it grounds the model in real numbers and
writes the result back to each fixture's summary.json `ai_summary`.

Usage:
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 -m src.pipeline.generate_match_headlines --match-id germany_ivory_coast_2026 --write
  python3 -m src.pipeline.generate_match_headlines --date 20260620          # all today's fixtures (dry-run)

Dry-run (default) assembles and prints the context without calling the API, so it
works without an API key. `--write` calls Claude and updates summary.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Optional

from src.common.team_identity import canonical_team_slug, normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
# Low-cost / fast model for a simple, high-volume per-fixture generation; override
# with ANTHROPIC_MODEL if you want a more capable (and costlier) model.
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
MAX_TOKENS = 500

SYSTEM_PROMPT = (
    "You are an expert football (soccer) tactical analyst writing pre-match "
    "previews for a World Cup dashboard. Given structured match data, write one "
    "punchy tactical headline and exactly three short tactical insights.\n"
    "Rules:\n"
    "- Ground every claim ONLY in the data provided. Do not invent players, "
    "injuries, scores, or stats that are not in the data.\n"
    "- The headline is one line, under 12 words, specific to these two teams.\n"
    "- Each insight is one sentence (under 25 words) about the tactical matchup, "
    "form, or style contrast implied by the numbers.\n"
    "- Reference the favourite (by Elo / win expectancy), the style contrast "
    "(possession, shots), and formations when the data supports it.\n"
    "- Neutral, analytical tone. No betting language. No emojis."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "insights": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "insights"],
    "additionalProperties": False,
}


def _load(path: Path) -> Any:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _elo_map() -> dict[str, float]:
    cache = _load(DATA_DIR / "source_cache" / "world_football_elo" / "latest_ratings.json") or {}
    out: dict[str, float] = {}
    for row in cache.get("ratings", []):
        name = normalize_team_name(row.get("team"))
        elo = row.get("elo_rating")
        if name and elo is not None:
            out[name] = float(elo)
    return out


def _style_map() -> dict[str, dict[str, float]]:
    cache = _load(DATA_DIR / "source_cache" / "squad_style" / "latest_metrics.json") or {}
    out: dict[str, dict[str, float]] = {}
    for entry in cache.get("teams", []):
        name = entry.get("team")
        fields = entry.get("fields", {})
        vals = {k: v.get("value") for k, v in fields.items() if isinstance(v, dict) and v.get("value") is not None}
        if name and vals:
            out[name] = vals
    return out


def _win_expectancy(elo1: Optional[float], elo2: Optional[float]) -> Optional[int]:
    if elo1 is None or elo2 is None:
        return None
    return round(100 / (1 + 10 ** ((elo2 - elo1) / 400)))


def build_context(match_id: str) -> Optional[dict]:
    summary = _load(DATA_DIR / "matches" / match_id / "summary.json")
    if not summary:
        return None
    meta = summary.get("metadata", {})
    t1, t2 = meta.get("team1"), meta.get("team2")
    if not t1 or not t2:
        return None
    elo, style = _elo_map(), _style_map()
    tactics = (summary.get("ai_summary", {}) or {}).get("confirmed_tactics", {})

    def team_block(name: str) -> dict:
        slug = canonical_team_slug(name)
        s = style.get(name, {})
        return {
            "team": name,
            "elo": elo.get(name),
            "formation": (tactics.get(slug) or {}).get("formation"),
            "manager": (tactics.get(slug) or {}).get("manager") or None,
            "possession_pct": s.get("possession_avg"),
            "shots_per_game": s.get("shots_per_90"),
            "goals_per_game": s.get("goals_per_90"),
            "goals_conceded_per_game": s.get("goals_conceded_per_90"),
            "pass_completion_pct": s.get("pass_completion_pct"),
        }

    return {
        "stage": meta.get("stage"),
        "team1": team_block(t1),
        "team2": team_block(t2),
        "team1_win_expectancy_pct": _win_expectancy(elo.get(t1), elo.get(t2)),
        "team2_win_expectancy_pct": _win_expectancy(elo.get(t2), elo.get(t1)),
    }


def generate(context: dict) -> dict:
    """Call Claude to produce {headline, insights[3]}."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    user = (
        "Write the tactical headline and three insights for this match. "
        "Return JSON only.\n\n" + json.dumps(context, ensure_ascii=False)
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
        output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
    )
    text = next((b.text for b in resp.content if b.type == "text"), "{}")
    data = json.loads(text)
    insights = [str(i).strip() for i in data.get("insights", []) if str(i).strip()][:3]
    return {"headline": data.get("headline", "").strip(), "insights": insights}


def write_summary(match_id: str, result: dict) -> None:
    path = DATA_DIR / "matches" / match_id / "summary.json"
    summary = _load(path)
    ai = summary.setdefault("ai_summary", {})
    ai["key_headline"] = result["headline"]
    if result["insights"]:
        ai["tactical_insights"] = result["insights"]
    ai["headline_source"] = "ai_generated"
    ai["headline_model"] = MODEL
    ai["headline_generated_at_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def _today_match_ids(date_yyyymmdd: str) -> list[str]:
    """Fixture folders whose summary.json date matches the given date."""
    target = dt.datetime.strptime(date_yyyymmdd, "%Y%m%d").strftime("%m/%d/%Y")
    ids = []
    for folder in sorted((DATA_DIR / "matches").glob("*_2026")):
        meta = (_load(folder / "summary.json") or {}).get("metadata", {})
        if meta.get("date") == target:
            ids.append(folder.name)
    return ids


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate AI tactical headlines.")
    ap.add_argument("--match-id", help="Single fixture id, e.g. germany_ivory_coast_2026")
    ap.add_argument("--date", help="YYYYMMDD: all fixtures on that date")
    ap.add_argument("--write", action="store_true", help="Call Claude and update summary.json (needs ANTHROPIC_API_KEY)")
    args = ap.parse_args()

    if args.match_id:
        match_ids = [args.match_id]
    elif args.date:
        match_ids = _today_match_ids(args.date)
    else:
        match_ids = _today_match_ids(dt.datetime.now().strftime("%Y%m%d"))

    if args.write and not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set; required for --write.")

    print(f"model={MODEL} fixtures={len(match_ids)} mode={'write' if args.write else 'dry-run'}")
    for mid in match_ids:
        ctx = build_context(mid)
        if not ctx:
            print(f"  {mid}: skipped (no summary/teams)")
            continue
        if args.write:
            result = generate(ctx)
            write_summary(mid, result)
            print(f"  {mid}: {result['headline']}")
            for ins in result["insights"]:
                print(f"      - {ins}")
        else:
            print(f"  {mid} context: {json.dumps(ctx, ensure_ascii=False)}")
    if not args.write:
        print("(dry-run; set ANTHROPIC_API_KEY and pass --write to generate)")


if __name__ == "__main__":
    main()
