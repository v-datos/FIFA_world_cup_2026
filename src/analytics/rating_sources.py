"""No-cost national-team rating source collectors."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.common.team_identity import normalize_team_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_PATH = (
    PROJECT_ROOT / "data" / "source_cache" / "world_football_elo" / "latest_ratings.json"
)
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "source_cache" / "world_football_elo" / "raw"
WORLD_FOOTBALL_ELO_URL = "https://www.eloratings.net/World.tsv"
WORLD_FOOTBALL_ELO_TEAMS_URL = "https://www.eloratings.net/en.teams.tsv"
FIFA_MENS_RANKING_URL = "https://inside.fifa.com/fifa-world-ranking/men"
PARSER_VERSION = "world_football_elo_tsv_v1"
REQUEST_HEADERS = {
    "User-Agent": "FIFA World Cup 2026 dashboard source collector/1.0"
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def fetch_text(url: str, timeout: int = 20) -> tuple[str, dict[str, Any]]:
    request = Request(url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return body, {
            "url": url,
            "status_code": getattr(response, "status", None),
            "last_modified": response.headers.get("Last-Modified"),
            "content_type": response.headers.get("Content-Type"),
        }


def relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def parse_team_dictionary(team_tsv: str) -> dict[str, dict[str, str]]:
    teams: dict[str, dict[str, str]] = {}
    for line in team_tsv.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        code = fields[0].strip()
        if not code or code.endswith("_loc") or len(fields) < 2:
            continue
        source_team_name = fields[1].strip()
        teams[code] = {
            "source_team_name": source_team_name,
            "team": normalize_team_name(source_team_name),
        }
    return teams


def parse_world_football_elo(world_tsv: str, team_names: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in world_tsv.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) < 4:
            continue
        code = fields[2].strip()
        team_entry = team_names.get(code)
        if not team_entry:
            continue
        try:
            rank = int(fields[1])
            rating = int(fields[3])
        except ValueError:
            continue
        rows.append(
            {
                "team": team_entry["team"],
                "source_team_name": team_entry["source_team_name"],
                "source_team_code": code,
                "rank": rank,
                "rating_rank": rank,
                "elo_rating": rating,
                "rating_value": rating,
            }
        )
    return rows


def collect_world_football_elo(
    cache_path: Path = DEFAULT_CACHE_PATH,
    raw_dir: Path = DEFAULT_RAW_DIR,
    write: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    checked_at = utc_now()
    try:
        world_tsv, world_meta = fetch_text(WORLD_FOOTBALL_ELO_URL)
        teams_tsv, teams_meta = fetch_text(WORLD_FOOTBALL_ELO_TEAMS_URL)
        rows = parse_world_football_elo(world_tsv, parse_team_dictionary(teams_tsv))
        if not rows:
            warnings.append("World Football Elo TSV parsed with zero rows.")
            status = "blocked"
        else:
            status = "used"
        payload = {
            "metadata": {
                "source_label": "web_researched",
                "source_name": "World Football Elo Ratings",
                "source_url": WORLD_FOOTBALL_ELO_URL,
                "team_dictionary_url": WORLD_FOOTBALL_ELO_TEAMS_URL,
                "collection_method": "tsv_fetch",
                "parser_version": PARSER_VERSION,
                "status": status,
                "checked_at_utc": checked_at,
                "source_last_modified": world_meta.get("last_modified"),
                "team_dictionary_last_modified": teams_meta.get("last_modified"),
                "row_count": len(rows),
                "warnings": warnings,
                "blocked_reasons": [] if rows else ["empty_world_football_elo_parse"],
            },
            "ratings": rows,
        }
        if write:
            raw_dir.mkdir(parents=True, exist_ok=True)
            world_raw_path = raw_dir / "World.tsv"
            teams_raw_path = raw_dir / "en.teams.tsv"
            world_raw_path.write_text(world_tsv, encoding="utf-8")
            teams_raw_path.write_text(teams_tsv, encoding="utf-8")
            payload["metadata"]["raw_source_paths"] = {
                "world_ratings": relative_path(world_raw_path),
                "team_dictionary": relative_path(teams_raw_path),
            }
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        warnings.append(f"World Football Elo live fetch failed: {exc}")
        cached = load_rating_cache(cache_path)
        if cached:
            cached.setdefault("metadata", {})
            cached["metadata"]["status"] = "used_cache_after_live_fetch_failed"
            cached["metadata"]["last_attempted_at_utc"] = checked_at
            cached["metadata"]["warnings"] = [
                *cached["metadata"].get("warnings", []),
                *warnings,
            ]
            return cached
        return {
            "metadata": {
                "source_label": "blocked",
                "source_name": "World Football Elo Ratings",
                "source_url": WORLD_FOOTBALL_ELO_URL,
                "team_dictionary_url": WORLD_FOOTBALL_ELO_TEAMS_URL,
                "collection_method": "tsv_fetch",
                "parser_version": PARSER_VERSION,
                "status": "blocked",
                "checked_at_utc": checked_at,
                "row_count": 0,
                "warnings": warnings,
                "blocked_reasons": ["world_football_elo_unavailable"],
            },
            "ratings": [],
        }


def load_rating_cache(cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, Any] | None:
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def get_cached_world_football_elo_rating(
    team_name: str,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> dict[str, Any] | None:
    cache = load_rating_cache(cache_path)
    if not cache:
        return None
    normalized = normalize_team_name(team_name)
    for row in cache.get("ratings", []):
        if normalize_team_name(row.get("team", "")) == normalized:
            metadata = cache.get("metadata", {})
            return {
                "team": normalized,
                "elo_rating": row.get("elo_rating"),
                "rank": row.get("rank"),
                "source_team_code": row.get("source_team_code"),
                "source_label": metadata.get("source_label", "web_researched"),
                "source_name": metadata.get("source_name", "World Football Elo Ratings"),
                "source_url": metadata.get("source_url", WORLD_FOOTBALL_ELO_URL),
                "checked_at_utc": metadata.get("checked_at_utc"),
                "source_last_modified": metadata.get("source_last_modified"),
                "parser_version": metadata.get("parser_version"),
            }
    return None


def build_world_football_elo_ratings(
    teams: list[str],
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> tuple[dict[str, float], dict[str, Any]]:
    cache = load_rating_cache(cache_path)
    ratings: dict[str, float] = {}
    missing: list[str] = []
    if not cache:
        return ratings, {
            "rating_source": "missing",
            "rating_status": "missing_cache",
            "missing_rating_teams": sorted({normalize_team_name(team) for team in teams}),
            "message": "World Football Elo cache is missing.",
            "source_label": "missing",
        }

    by_team = {
        normalize_team_name(row.get("team", "")): row
        for row in cache.get("ratings", [])
        if row.get("team")
    }
    for team in sorted({normalize_team_name(team) for team in teams}):
        row = by_team.get(team)
        if row and row.get("elo_rating") is not None:
            ratings[team] = float(row["elo_rating"])
        else:
            missing.append(team)

    metadata = cache.get("metadata", {})
    return ratings, {
        "rating_source": "world_football_elo",
        "rating_status": "partial_missing" if missing else "complete",
        "missing_rating_teams": missing,
        "source_label": metadata.get("source_label", "web_researched"),
        "source_name": metadata.get("source_name", "World Football Elo Ratings"),
        "source_url": metadata.get("source_url", WORLD_FOOTBALL_ELO_URL),
        "source_checked_at_utc": metadata.get("checked_at_utc"),
        "source_last_modified": metadata.get("source_last_modified"),
        "parser_version": metadata.get("parser_version"),
        "message": (
            "Simulation ratings use cached World Football Elo national-team ratings. "
            "FIFA rankings remain a sanity-check fallback, not the primary model source."
        ),
    }


def collect_fifa_ranking_metadata() -> dict[str, Any]:
    checked_at = utc_now()
    try:
        html, meta = fetch_text(FIFA_MENS_RANKING_URL)
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
        )
        if not match:
            raise ValueError("FIFA Next.js data block not found")
        data = json.loads(unescape(match.group(1)))
        ranking = data["props"]["pageProps"]["pageData"]["ranking"]
        return {
            "source_label": "web_researched",
            "source_name": "FIFA/Coca-Cola Men's World Ranking",
            "source_url": FIFA_MENS_RANKING_URL,
            "collection_method": "next_data_metadata",
            "status": "metadata_only",
            "checked_at_utc": checked_at,
            "last_update_date": ranking.get("lastUpdateDate"),
            "next_update_date": ranking.get("nextUpdateDate"),
            "content_type": meta.get("content_type"),
            "warnings": [
                "Official page metadata is available, but ranking rows are loaded by the FIFA web app and are not used as the primary rating source."
            ],
        }
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return {
            "source_label": "blocked",
            "source_name": "FIFA/Coca-Cola Men's World Ranking",
            "source_url": FIFA_MENS_RANKING_URL,
            "collection_method": "next_data_metadata",
            "status": "blocked",
            "checked_at_utc": checked_at,
            "warnings": [f"FIFA ranking metadata fetch failed: {exc}"],
            "blocked_reasons": ["fifa_ranking_metadata_unavailable"],
        }


def active_tournament_teams() -> list[str]:
    identity_path = PROJECT_ROOT / "data" / "reference" / "team_identity.json"
    teams = json.loads(identity_path.read_text(encoding="utf-8"))
    return sorted(normalize_team_name(row["display_name"]) for row in teams)


def build_spike_report(
    cache: dict[str, Any],
    fifa_metadata: dict[str, Any],
    teams: list[str],
) -> str:
    by_team = {
        normalize_team_name(row.get("team", "")): row
        for row in cache.get("ratings", [])
        if row.get("team")
    }
    ratings = {
        team: float(by_team[team]["elo_rating"])
        for team in teams
        if team in by_team and by_team[team].get("elo_rating") is not None
    }
    missing = [team for team in teams if team not in ratings]
    sample = sorted(
        (
            row
            for row in cache.get("ratings", [])
            if normalize_team_name(row.get("team", "")) in set(teams)
        ),
        key=lambda row: row.get("rank", 9999),
    )[:12]
    metadata = cache.get("metadata", {})
    lines = [
        "# T-039 No-Cost Rating Source Spike",
        "",
        f"Last updated: {utc_now()[:10]}",
        "Owner: Data Pipeline Engineer",
        "",
        "## Finding",
        "",
        (
            "World Football Elo is practical as the no-cost national-team rating source. "
            f"The current cache parsed {metadata.get('row_count', 0)} ratings and covered "
            f"{len(ratings)}/{len(teams)} tournament teams."
        ),
        "",
        "FIFA ranking remains useful as an official sanity check and fallback reference, "
        "but the public page is a dynamic application. This spike captures update metadata "
        "instead of using FIFA as the primary machine-readable rating feed.",
        "",
        "## Source Metadata",
        "",
        f"- World Football Elo source: `{metadata.get('source_url', WORLD_FOOTBALL_ELO_URL)}`",
        f"- World Football Elo checked at: `{metadata.get('checked_at_utc')}`",
        f"- World Football Elo last modified: `{metadata.get('source_last_modified')}`",
        f"- World Football Elo status: `{metadata.get('status')}`",
        f"- World Football Elo parser version: `{metadata.get('parser_version')}`",
        f"- World Football Elo raw ratings snapshot: `{(metadata.get('raw_source_paths') or {}).get('world_ratings')}`",
        f"- World Football Elo raw team dictionary snapshot: `{(metadata.get('raw_source_paths') or {}).get('team_dictionary')}`",
        f"- FIFA ranking page: `{fifa_metadata.get('source_url', FIFA_MENS_RANKING_URL)}`",
        f"- FIFA metadata status: `{fifa_metadata.get('status')}`",
        f"- FIFA last update date: `{fifa_metadata.get('last_update_date')}`",
        f"- FIFA next update date: `{fifa_metadata.get('next_update_date')}`",
        "",
        "## Coverage",
        "",
        f"- Tournament teams checked: {len(teams)}",
        f"- World Football Elo matches: {len(ratings)}",
        f"- Missing teams: {', '.join(missing) if missing else 'None'}",
        "",
        "## Sample Tournament Ratings",
        "",
        "| Rank | Team | Elo | Code |",
        "|---:|---|---:|---|",
    ]
    for row in sample:
        lines.append(
            f"| {row.get('rank')} | {row.get('team')} | {row.get('elo_rating')} | {row.get('source_team_code')} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Cache Contract",
            "",
            "- Cache parsed source rows in `data/source_cache/world_football_elo/latest_ratings.json`.",
            "- Cache raw source snapshots in `data/source_cache/world_football_elo/raw/`.",
            "- Keep `source_url`, `team_dictionary_url`, `checked_at_utc`, `source_last_modified`, `parser_version`, `status`, `warnings`, and `blocked_reasons` in metadata.",
            "- Use World Football Elo ratings for model strength. Use FIFA ranking only for official sanity checks or fallback ranking context.",
            "- Do not use ClubElo as a national-team source.",
            "",
            "## Risks",
            "",
            "- World Football Elo has no documented public API contract; the TSV path is public but could change.",
            "- Fetch frequency should be low and cached; refresh once per matchday or before the 3-hour jornada window, not per API request.",
            "- FIFA official ranking rows are not as easy to consume from a stable public data endpoint; use the page metadata and manual/automated browser verification until a stable official feed is identified.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect no-cost football rating sources.")
    parser.add_argument("--cache-path", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument(
        "--report-path",
        type=Path,
        default=PROJECT_ROOT / "docs" / "source_spikes" / "t039_no_cost_rating_sources.md",
    )
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--skip-fifa", action="store_true")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write cache, raw snapshots, and report. Without this flag the command only probes sources.",
    )
    args = parser.parse_args()

    cache = collect_world_football_elo(args.cache_path, args.raw_dir, write=args.write)
    fifa_metadata = (
        {
            "source_url": FIFA_MENS_RANKING_URL,
            "status": "skipped",
            "last_update_date": None,
            "next_update_date": None,
        }
        if args.skip_fifa
        else collect_fifa_ranking_metadata()
    )
    report = build_spike_report(cache, fifa_metadata, active_tournament_teams())
    if args.write:
        args.report_path.parent.mkdir(parents=True, exist_ok=True)
        args.report_path.write_text(report, encoding="utf-8")
    print(
        json.dumps(
            {
                "mode": "write" if args.write else "dry_run",
                "cache_path": str(args.cache_path),
                "report_path": str(args.report_path),
                "world_football_elo_status": cache.get("metadata", {}).get("status"),
                "world_football_elo_rows": cache.get("metadata", {}).get("row_count"),
                "fifa_metadata_status": fifa_metadata.get("status"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
