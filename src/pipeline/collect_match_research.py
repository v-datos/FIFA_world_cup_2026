"""Collect source-backed match research into a reviewable cache.

Default mode is a dry run. Use --write only after reviewing the manifest.
This script never writes summary.json, metrics.json, or production briefing.json.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.common.team_identity import canonical_team_slug, get_team_identity
from src.pipeline.discover_active_fixtures import manifest_path, parse_now_arg

DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "matches"
GENERATOR = "collect_match_research.py"
SCHEMA_VERSION = "0.1"
FORBIDDEN_OUTPUT_NAMES = {"summary.json", "metrics.json", "briefing.json"}
CLAIM_KEYWORDS = {
    "injury_watch": (
        "injury",
        "injured",
        "fitness",
        "fit",
        "fit to play",
        "doubtful",
        "ruled out",
        "return",
        "returned",
        "hamstring",
        "ankle",
        "knee",
    ),
    "lineup_watch": (
        "lineup",
        "line-up",
        "starting xi",
        "starts",
        "expected xi",
        "selection",
    ),
    "roster_watch": (
        "squad",
        "roster",
        "called up",
        "call-up",
        "replacement",
        "suspension",
        "suspended",
    ),
    "tactical_watch": (
        "formation",
        "press",
        "block",
        "transition",
        "possession",
        "counter",
        "tactical",
        "tactics",
    ),
}
VALID_CONFIDENCE = {"low", "medium", "high"}


def utc_now_dt() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_utc_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def load_json_payload(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fixture_datetime(meta: dict[str, Any]) -> datetime | None:
    date_value = str(meta.get("date") or "").strip()
    time_value = str(meta.get("time") or "00:00").strip()
    for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{date_value} {time_value}", fmt)
        except ValueError:
            pass
    return None


def infer_lifecycle(kickoff: datetime | None, now_value: datetime) -> str:
    if not kickoff:
        return "unknown"
    if kickoff.date() < now_value.date():
        return "finished"
    return "not_finished"


def briefing_window(kickoff: datetime | None, window_hours: int, now_value: datetime) -> dict[str, Any]:
    window_start = kickoff - timedelta(hours=window_hours) if kickoff else None
    return {
        "window_hours": window_hours,
        "kickoff": kickoff.isoformat(timespec="minutes") if kickoff else None,
        "window_start": window_start.isoformat(timespec="minutes") if window_start else None,
        "is_open": bool(window_start and kickoff and window_start <= now_value <= kickoff),
    }


def stable_id(prefix: str, value: str) -> str:
    safe_prefix = re.sub(r"[^a-z0-9]+", "-", prefix.lower()).strip("-") or "source"
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"{safe_prefix}-{digest}"


def compact_text(value: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def strip_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return html.unescape(value)


def split_sentences(value: str) -> list[str]:
    text = strip_html(value)
    pieces = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [compact_text(piece, 420) for piece in pieces if compact_text(piece)]


def team_aliases(team: str) -> set[str]:
    record = get_team_identity(team)
    values = {team, canonical_team_slug(team)}
    if record:
        values.add(str(record["display_name"]))
        values.add(str(record["slug"]))
        values.update(str(alias) for alias in record.get("aliases", []))
    return {value.lower() for value in values if value}


def detect_team(sentence: str, team1: str, team2: str) -> str | None:
    lowered = sentence.lower()
    for team in (team1, team2):
        for alias in team_aliases(team):
            if alias and alias in lowered:
                return team
    return None


def detect_claim_type(sentence: str) -> str | None:
    lowered = sentence.lower()
    for claim_type, keywords in CLAIM_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return claim_type
    return None


def source_record(
    source_id: str,
    source_name: str,
    path_or_url: str,
    collection_method: str,
    label: str,
    checked_at_utc: str,
    status: str,
    warnings: list[str] | None = None,
    blocked_reasons: list[str] | None = None,
    claim_scope: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_url": path_or_url,
        "path_or_url": path_or_url,
        "collection_method": collection_method,
        "checked_at_utc": checked_at_utc,
        "status": status,
        "label": label,
        "source_label": label,
        "warnings": warnings or [],
        "blocked_reasons": blocked_reasons or [],
        "claim_scope": claim_scope or [],
    }


def claim_record(
    claim_type: str,
    text: str,
    source_id: str,
    index: int,
    team: str | None = None,
    basis: str = "source_keyword_scan",
    confidence: str = "low",
) -> dict[str, Any]:
    confidence_value = confidence if confidence in VALID_CONFIDENCE else "low"
    return {
        "claim_id": f"{source_id}-claim-{index:02d}",
        "claim_type": claim_type,
        "team": team,
        "text": compact_text(text, 420),
        "basis": basis,
        "source_ids": [source_id],
        "confidence": confidence_value,
        "review_status": "draft",
    }


def claims_from_text(
    raw_text: str,
    source_id: str,
    team1: str,
    team2: str,
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for sentence in split_sentences(raw_text):
        claim_type = detect_claim_type(sentence)
        if not claim_type:
            continue
        key = (claim_type, sentence.lower())
        if key in seen:
            continue
        seen.add(key)
        claims.append(
            claim_record(
                claim_type=claim_type,
                text=sentence,
                source_id=source_id,
                index=len(claims) + 1,
                team=detect_team(sentence, team1, team2),
            )
        )
        if len(claims) >= 12:
            break
    return claims


def normalize_structured_claims(
    payload: dict[str, Any],
    source_id: str,
    team1: str,
    team2: str,
) -> list[dict[str, Any]]:
    raw_claims = payload.get("claims") or payload.get("items") or []
    if not isinstance(raw_claims, list):
        return []

    claims: list[dict[str, Any]] = []
    for item in raw_claims:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("claim") or "").strip()
        if not text:
            continue
        claim_type = str(item.get("claim_type") or detect_claim_type(text) or "match_note")
        team_value = str(item.get("team") or "").strip() or detect_team(text, team1, team2)
        team = team_value if team_value in (team1, team2) else detect_team(team_value, team1, team2)
        confidence = str(item.get("confidence") or "medium").strip().lower()
        claims.append(
            claim_record(
                claim_type=claim_type,
                text=text,
                source_id=source_id,
                index=len(claims) + 1,
                team=team,
                basis="structured_source_claim",
                confidence=confidence,
            )
        )
    return claims


def load_source_file(
    path: Path,
    checked_at_utc: str,
    team1: str,
    team2: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_id = stable_id(path.stem, str(path.resolve()))
    path_label = manifest_path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as exc:
        return source_record(
            source_id=source_id,
            source_name=path.name,
            path_or_url=path_label,
            collection_method="offline_file",
            label="blocked",
            checked_at_utc=checked_at_utc,
            status="blocked",
            blocked_reasons=[f"source_file_unreadable: {exc}"],
        ), []

    source_name = path.name
    label = "web_researched"
    claims: list[dict[str, Any]]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        source_name = str(payload.get("source_name") or payload.get("name") or source_name)
        label = str(payload.get("source_label") or payload.get("label") or label)
        source_url = str(payload.get("source_url") or payload.get("url") or path_label)
        claims = normalize_structured_claims(payload, source_id, team1, team2)
        if not claims:
            text = str(payload.get("text") or payload.get("body") or payload.get("content") or raw)
            claims = claims_from_text(text, source_id, team1, team2)
    else:
        source_url = path_label
        claims = claims_from_text(raw, source_id, team1, team2)

    warnings = [] if claims else ["No matchday claim keywords were detected in this source."]
    record = source_record(
        source_id=source_id,
        source_name=source_name,
        path_or_url=source_url,
        collection_method="offline_file",
        label=label,
        checked_at_utc=checked_at_utc,
        status="used",
        warnings=warnings,
        claim_scope=sorted({claim["claim_type"] for claim in claims}),
    )
    return record, claims


def load_source_url(
    url: str,
    checked_at_utc: str,
    timeout: int,
    team1: str,
    team2: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_id = stable_id("web-source", url)
    request = urllib.request.Request(url, headers={"User-Agent": "FWC26-research-prototype/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            raw_bytes = response.read(1_000_000)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return source_record(
            source_id=source_id,
            source_name=url,
            path_or_url=url,
            collection_method="http_get",
            label="blocked",
            checked_at_utc=checked_at_utc,
            status="blocked",
            blocked_reasons=[f"source_url_unavailable: {exc}"],
        ), []

    raw = raw_bytes.decode("utf-8", errors="replace")
    claims = claims_from_text(raw, source_id, team1, team2)
    record = source_record(
        source_id=source_id,
        source_name=url,
        path_or_url=url,
        collection_method="http_get",
        label="web_researched",
        checked_at_utc=checked_at_utc,
        status="used",
        warnings=[] if claims else ["No matchday claim keywords were detected in this source."],
        claim_scope=sorted({claim["claim_type"] for claim in claims}),
    )
    if "html" not in content_type and "text" not in content_type:
        record["warnings"].append(f"Unexpected content-type: {content_type or 'unknown'}.")
    return record, claims


def local_source_records(
    summary_path: Path,
    metrics_path: Path,
    checked_at_utc: str,
) -> list[dict[str, Any]]:
    records = [
        source_record(
            source_id="local-summary-json",
            source_name="summary.json",
            path_or_url=manifest_path(summary_path),
            collection_method="local_file",
            label="static_curated",
            checked_at_utc=checked_at_utc,
            status="used",
            claim_scope=["fixture_context"],
        )
    ]
    if metrics_path.exists():
        records.append(
            source_record(
                source_id="local-metrics-json",
                source_name="metrics.json",
                path_or_url=manifest_path(metrics_path),
                collection_method="local_file",
                label="static_curated",
                checked_at_utc=checked_at_utc,
                status="used",
                claim_scope=["forecast_context"],
            )
        )
    else:
        records.append(
            source_record(
                source_id="local-metrics-json",
                source_name="metrics.json",
                path_or_url=manifest_path(metrics_path),
                collection_method="local_file",
                label="missing",
                checked_at_utc=checked_at_utc,
                status="blocked",
                blocked_reasons=["missing_metrics_json"],
            )
        )
    return records


def group_claims(claims: list[dict[str, Any]], claim_type: str) -> list[str]:
    return [claim["text"] for claim in claims if claim["claim_type"] == claim_type]


def build_proposed_briefing(
    match_id: str,
    summary: dict[str, Any],
    claims: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    freshness: str,
    window: dict[str, Any],
    checked_at_utc: str,
    window_hours: int,
) -> dict[str, Any]:
    meta = summary.get("metadata", {})
    team1 = str(meta.get("team1") or "")
    team2 = str(meta.get("team2") or "")
    injury_claims = group_claims(claims, "injury_watch")
    lineup_claims = group_claims(claims, "lineup_watch")
    roster_claims = group_claims(claims, "roster_watch")
    tactical_claims = group_claims(claims, "tactical_watch")
    notes = [claim["text"] for claim in claims if claim["claim_type"] == "match_note"]

    return {
        "metadata": {
            "schema_version": "1.0-draft",
            "match_id": match_id,
            "generated_at_utc": checked_at_utc,
            "generator": GENERATOR,
            "mode": "source_backed_briefing_draft",
            "freshness": freshness,
            "valid_until_utc": to_utc_z(
                datetime.fromisoformat(checked_at_utc.replace("Z", "+00:00"))
                + timedelta(hours=window_hours)
            ),
            "briefing_window_hours": window_hours,
        },
        "fixture": {
            "team1": team1,
            "team2": team2,
            "date": meta.get("date"),
            "time": meta.get("time"),
            "venue": meta.get("venue"),
            "stage": meta.get("stage"),
        },
        "team_keys": {
            "team1": canonical_team_slug(team1),
            "team2": canonical_team_slug(team2),
        },
        "briefing": {
            "headline": f"Source-backed research draft for {team1} vs {team2}",
            "short_context": (
                "Draft generated from retained source records. Football Data "
                "Scientist review is required before publication."
            ),
            "injury_watch": injury_claims or ["No source-backed injury claim collected."],
            "lineup_watch": lineup_claims or ["No source-backed lineup claim collected."],
            "roster_updates": roster_claims or ["No source-backed roster claim collected."],
            "tactical_updates": tactical_claims or ["No source-backed tactical claim collected."],
            "operator_notes": notes or [
                "Review retained sources before copying any claim into production briefing.json."
            ],
        },
        "data_quality": {
            "freshness_state": freshness,
            "source_claim_count": len(claims),
            "warnings": [],
            "blocked_reasons": [] if claims else ["no_source_backed_claims"],
            "briefing_window": window,
        },
        "sources": source_records,
        "claims": claims,
        "review": {
            "status": "draft",
            "reviewer": None,
            "reviewed_at_utc": None,
            "notes": "Football Data Scientist approval required before publication.",
        },
    }


def build_research_cache(
    match_id: str,
    summary: dict[str, Any],
    source_records: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    target_path: Path,
    now_value: datetime,
    checked_at_utc: str,
    window_hours: int,
) -> dict[str, Any]:
    meta = summary.get("metadata", {})
    team1 = str(meta.get("team1") or "")
    team2 = str(meta.get("team2") or "")
    kickoff = fixture_datetime(meta)
    lifecycle = infer_lifecycle(kickoff, now_value)
    window = briefing_window(kickoff, window_hours, now_value)
    freshness = "skipped" if lifecycle == "finished" else "fresh" if window["is_open"] else "stale"
    if not claims and freshness != "skipped":
        freshness = "blocked"

    blocked_reasons: list[str] = []
    warnings: list[str] = [
        "Draft cache only; do not publish claims until football review is complete."
    ]
    if lifecycle == "finished":
        blocked_reasons.append("finished_fixture")
        warnings.append("Finished fixtures must not receive last-minute research.")
    if not claims:
        blocked_reasons.append("no_source_backed_claims")
    if not window["is_open"] and lifecycle != "finished":
        warnings.append("Collected outside the configured jornada briefing window.")

    return {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "match_id": match_id,
            "generated_at_utc": checked_at_utc,
            "generator": GENERATOR,
            "mode": "source_research_cache",
            "target_path": manifest_path(target_path),
            "write_safety": "never_writes_summary_metrics_or_production_briefing",
        },
        "fixture": {
            "team1": team1,
            "team2": team2,
            "date": meta.get("date"),
            "time": meta.get("time"),
            "venue": meta.get("venue"),
            "stage": meta.get("stage"),
            "lifecycle": lifecycle,
        },
        "team_keys": {
            "team1": canonical_team_slug(team1),
            "team2": canonical_team_slug(team2),
        },
        "data_quality": {
            "freshness_state": freshness,
            "source_count": len(source_records),
            "source_claim_count": len(claims),
            "warnings": warnings,
            "blocked_reasons": blocked_reasons,
            "briefing_window": window,
        },
        "source_records": source_records,
        "claims": claims,
        "proposed_briefing": build_proposed_briefing(
            match_id=match_id,
            summary=summary,
            claims=claims,
            source_records=source_records,
            freshness=freshness,
            window=window,
            checked_at_utc=checked_at_utc,
            window_hours=window_hours,
        ),
        "review": {
            "status": "draft",
            "reviewer": None,
            "reviewed_at_utc": None,
            "notes": "Research cache is not approved publication content.",
        },
    }


def validate_cache(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "metadata",
        "fixture",
        "team_keys",
        "data_quality",
        "source_records",
        "claims",
        "proposed_briefing",
        "review",
    ):
        if key not in payload:
            errors.append(key)

    for index, source in enumerate(payload.get("source_records", [])):
        for field in (
            "source_id",
            "source_name",
            "source_url",
            "path_or_url",
            "collection_method",
            "checked_at_utc",
            "status",
            "label",
            "source_label",
            "warnings",
            "blocked_reasons",
        ):
            if field not in source:
                errors.append(f"source_records[{index}].{field}")

    for index, claim in enumerate(payload.get("claims", [])):
        for field in (
            "claim_id",
            "claim_type",
            "text",
            "basis",
            "source_ids",
            "confidence",
            "review_status",
        ):
            if field not in claim:
                errors.append(f"claims[{index}].{field}")

    return errors


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    now_value = parse_now_arg(args.now)
    checked_at_utc = to_utc_z(utc_now_dt())
    match_dir = args.data_dir / args.match_id
    summary_path = match_dir / "summary.json"
    metrics_path = match_dir / "metrics.json"
    target_path = args.output_path or match_dir / "research_cache.json"

    if target_path.name in FORBIDDEN_OUTPUT_NAMES:
        return {
            "task": "T-036",
            "mode": "write" if args.write else "dry_run",
            "generated_at_utc": checked_at_utc,
            "status": "blocked",
            "reason": "forbidden_output_path",
            "blocked_reasons": [f"output path must not be {target_path.name}"],
        }, 1

    if not summary_path.exists():
        return {
            "task": "T-036",
            "mode": "write" if args.write else "dry_run",
            "generated_at_utc": checked_at_utc,
            "status": "blocked",
            "reason": "missing_summary_json",
            "blocked_reasons": [manifest_path(summary_path)],
        }, 1

    summary = load_json_payload(summary_path)
    meta = summary.get("metadata", {})
    team1 = str(meta.get("team1") or "")
    team2 = str(meta.get("team2") or "")
    lifecycle = infer_lifecycle(fixture_datetime(meta), now_value)
    source_records = local_source_records(summary_path, metrics_path, checked_at_utc)
    claims: list[dict[str, Any]] = []

    if lifecycle != "finished":
        for source_file in args.source_file:
            record, source_claims = load_source_file(
                source_file if source_file.is_absolute() else PROJECT_ROOT / source_file,
                checked_at_utc,
                team1,
                team2,
            )
            source_records.append(record)
            claims.extend(source_claims)

        for source_url in args.source_url:
            record, source_claims = load_source_url(
                source_url,
                checked_at_utc,
                args.http_timeout,
                team1,
                team2,
            )
            source_records.append(record)
            claims.extend(source_claims)

    cache = build_research_cache(
        match_id=args.match_id,
        summary=summary,
        source_records=source_records,
        claims=claims,
        target_path=target_path,
        now_value=now_value,
        checked_at_utc=checked_at_utc,
        window_hours=args.window_hours,
    )
    validation_errors = validate_cache(cache)
    status = "blocked" if validation_errors else "would_write" if args.write else "dry_run"
    action = "blocked" if validation_errors else "write" if args.write else "none"

    if args.write and not validation_errors:
        write_json(target_path, cache)
        status = "written"

    return {
        "task": "T-036",
        "mode": "write" if args.write else "dry_run",
        "generated_at_utc": checked_at_utc,
        "status": status,
        "action": action,
        "selection": {
            "match_id": args.match_id,
            "data_dir": manifest_path(args.data_dir),
            "target_path": manifest_path(target_path),
            "source_files": [manifest_path(path) for path in args.source_file],
            "source_urls": args.source_url,
            "window_hours": args.window_hours,
            "now": now_value.isoformat(timespec="minutes"),
        },
        "validation": {
            "status": "fail" if validation_errors else "pass",
            "errors": validation_errors,
        },
        "research_cache": cache,
    }, 1 if validation_errors else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect source-backed research for one match into a reviewable cache."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Accepted for readability; dry run is already the default.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the research cache. Omit for dry run.",
    )
    parser.add_argument(
        "--match-id",
        required=True,
        help="Canonical match id, e.g. canada_qatar_2026.",
    )
    parser.add_argument(
        "--source-file",
        type=Path,
        action="append",
        default=[],
        help="Offline source HTML, text, or structured JSON path. Repeatable.",
    )
    parser.add_argument(
        "--source-url",
        action="append",
        default=[],
        help="Optional public source URL fetched with a simple HTTP GET. Repeatable.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Write target. Defaults to data/matches/{match_id}/research_cache.json.",
    )
    parser.add_argument(
        "--window-hours",
        type=int,
        default=3,
        help="Freshness window before kickoff, aligned with T-032.",
    )
    parser.add_argument(
        "--now",
        help="QA override for current local time, format YYYY-MM-DDTHH:MM.",
    )
    parser.add_argument(
        "--http-timeout",
        type=int,
        default=15,
        help="Seconds before a source URL fetch is marked blocked.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Fixture data directory. Defaults to data/matches.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.window_hours <= 0:
        raise SystemExit("--window-hours must be greater than zero")
    if args.http_timeout <= 0:
        raise SystemExit("--http-timeout must be greater than zero")
    if not args.data_dir.is_absolute():
        args.data_dir = PROJECT_ROOT / args.data_dir
    if args.output_path and not args.output_path.is_absolute():
        args.output_path = PROJECT_ROOT / args.output_path

    manifest, exit_code = build_manifest(args)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
