#!/usr/bin/env python3
"""AI tactical headline generator for the FIFA World Cup 2026 dashboard.

Uses Google Vertex AI Gemini (gemini-2.5-flash) to write a real tactical headline +
3 insights for a match from the structured data the dashboard already has — team Elo
ratings, a win expectancy, ESPN style metrics (possession/shots/goals), and formations.
Replaces the generic "Baseline preview pending for X vs Y" stub.

Designed to run in the matchday refresh: it grounds the model in real numbers and
writes the result back to each fixture's summary.json `ai_summary`.

Usage:
  python3 -m src.pipeline.generate_match_headlines --match-id germany_ivory_coast_2026 --write
  python3 -m src.pipeline.generate_match_headlines --date 20260620          # all today's fixtures (dry-run)

Dry-run (default) assembles and prints the context without calling the API.
`--write` calls Vertex AI Gemini and updates summary.json.
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
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
PROJECT = os.environ.get("GEMINI_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT") or "midyear-castle-328020"
LOCATION = os.environ.get("GEMINI_LOCATION", "us-central1")
MAX_TOKENS = 4000

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "insights": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "insights"],
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


def generate(context: dict) -> tuple[dict, str]:
    """Call Vertex AI Gemini to produce {headline, insights[3]} and return the source label."""
    from google import genai
    from google.genai import types

    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

    t1 = context["team1"]["team"]
    t2 = context["team2"]["team"]
    search_prompt = (
        f"Using current web sources, research the upcoming 2026 FIFA World Cup match between {t1} and {t2}.\n"
        "1. List recent news, manager updates, and tactical previews for both teams.\n"
        "2. Identify key players to watch, recent team form, and projected styles/tactics for this match.\n"
        "Focus on the tactical setup, match significance, and key match insights."
    )

    research_text = ""
    source_label = "ai_web_grounded"
    try:
        grounded = client.models.generate_content(
            model=MODEL,
            contents=search_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
                max_output_tokens=2500,
            ),
        )
        research_text = (grounded.text or "").strip()
    except Exception as e:
        print(f"  WARNING: Grounded web search failed ({type(e).__name__}: {e}). Falling back to local data only.")
        source_label = "ai_generated"

    if research_text:
        prompt = (
            "You are an expert football (soccer) tactical analyst writing pre-match previews for a World Cup dashboard.\n"
            "Given the structured match data and the web-grounded research report below, write one punchy tactical headline (under 12 words) and exactly three short tactical insights (each one sentence, under 25 words).\n\n"
            "Rules:\n"
            "- Ground your response heavily in the specific real-world storylines, manager news, player matchups, and tournament context from the Web Research Report. Do NOT just repeat generic statistics (like possession %, shot numbers, or win expectancies) if they make the insights sound dry and generic.\n"
            "- The headline must capture a major narrative (e.g. recent form adjustments, key manager changes, or qualification context).\n"
            "- The three insights must cover:\n"
            "  1. A key player match-up, tactical duel, or player storyline.\n"
            "  2. A recent tournament result, team form impact, or qualification context.\n"
            "  3. A tactical manager/setup matchup (e.g. defensive low-block vs high pressing vertical styles).\n"
            "- Neutral, analytical tone. No betting language. No emojis.\n\n"
            f"Structured Match Data:\n{json.dumps(context, ensure_ascii=False)}\n\n"
            f"Web Research Report:\n{research_text}"
        )
    else:
        prompt = (
            "You are an expert football (soccer) tactical analyst writing pre-match previews for a World Cup dashboard.\n"
            "Given the structured match data below, write one punchy tactical headline (under 12 words) and exactly three short tactical insights (each one sentence, under 25 words).\n\n"
            "Rules:\n"
            "- Ground every claim ONLY in the provided structured data. Do not invent players, injuries, scores, or stats.\n"
            "- The headline is one line, specific to these two teams.\n"
            "- Reference the favourite (by Elo / win expectancy), the style contrast (possession, shots), or formations when supported.\n"
            "- Neutral, analytical tone. No betting language. No emojis.\n\n"
            f"Structured Match Data:\n{json.dumps(context, ensure_ascii=False)}"
        )

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=OUTPUT_SCHEMA,
        temperature=0.0,
        max_output_tokens=MAX_TOKENS,
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=config,
    )
    text = response.text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as jde:
        print(f"JSON DECODE ERROR: {jde}")
        print(f"RAW TEXT: {repr(text)}")
        print(f"RESPONSE METADATA: {response}")
        raise
    insights = [str(i).strip() for i in data.get("insights", []) if str(i).strip()][:3]
    return {"headline": data.get("headline", "").strip(), "insights": insights}, source_label


def write_summary(match_id: str, result: dict, source_label: str) -> None:
    path = DATA_DIR / "matches" / match_id / "summary.json"
    summary = _load(path)
    ai = summary.setdefault("ai_summary", {})
    ai["key_headline"] = result["headline"]
    if result["insights"]:
        ai["tactical_insights"] = result["insights"]
    ai["headline_source"] = source_label
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
    ap.add_argument("--all", action="store_true", help="Regenerate all fixtures under data/matches/")
    ap.add_argument("--write", action="store_true", help="Call Vertex AI Gemini and update summary.json")
    args = ap.parse_args()

    if args.match_id:
        match_ids = [args.match_id]
    elif args.all:
        match_ids = [folder.name for folder in sorted((DATA_DIR / "matches").glob("*_2026"))]
    elif args.date:
        match_ids = _today_match_ids(args.date)
    else:
        match_ids = _today_match_ids(dt.datetime.now().strftime("%Y%m%d"))

    print(f"model={MODEL} fixtures={len(match_ids)} mode={'write' if args.write else 'dry-run'}")
    for mid in match_ids:
        ctx = build_context(mid)
        if not ctx:
            print(f"  {mid}: skipped (no summary/teams)")
            continue
        if args.write:
            result, source_label = generate(ctx)
            write_summary(mid, result, source_label)
            print(f"  {mid}: {result['headline']}")
            for ins in result["insights"]:
                print(f"      - {ins}")
        else:
            print(f"  {mid} context: {json.dumps(ctx, ensure_ascii=False)}")
        print("(dry-run; pass --write to generate and update summary.json)")


if __name__ == "__main__":
    main()
