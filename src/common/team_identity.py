"""Shared team identity, alias, and slug helpers."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IDENTITY_PATH = PROJECT_ROOT / "data" / "reference" / "team_identity.json"


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.replace("&", " and ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", ascii_value.lower())).strip()


def _slugify_raw(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.replace("&", " and ")
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", ascii_value.lower())).strip("_")


@lru_cache(maxsize=1)
def team_identities() -> tuple[dict[str, Any], ...]:
    with open(IDENTITY_PATH, "r", encoding="utf-8") as f:
        return tuple(json.load(f))


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in team_identities():
        names = [record["display_name"], record["slug"], *record.get("aliases", [])]
        for name in names:
            index[_fold(name)] = record
            index[_slugify_raw(name)] = record
    return index


@lru_cache(maxsize=1)
def _slug_index() -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for record in team_identities():
        names = [record["display_name"], record["slug"], *record.get("aliases", [])]
        for name in names:
            index[_slugify_raw(name)] = record
    return index


@lru_cache(maxsize=1)
def team_id_to_name_map() -> dict[str, str]:
    return {record["team_id"]: record["display_name"] for record in team_identities()}


TEAM_ID_TO_NAME = team_id_to_name_map()


def get_team_identity(name: str | None) -> Optional[dict[str, Any]]:
    if not name:
        return None
    return _alias_index().get(_fold(name))


def normalize_team_name(name: str | None) -> str:
    if not name:
        return ""
    record = get_team_identity(name)
    return record["display_name"] if record else name.strip()


def canonical_team_slug(name: str | None) -> str:
    if not name:
        return ""
    record = get_team_identity(name)
    return record["slug"] if record else _slugify_raw(name)


def team_id_to_name(team_id: str | int | None) -> Optional[str]:
    if team_id is None:
        return None
    return TEAM_ID_TO_NAME.get(str(team_id))


def teams_from_match_id(match_id: str) -> tuple[Optional[str], Optional[str]]:
    base = re.sub(r"_2026$", "", match_id.strip())
    slug_index = _slug_index()
    known_slugs = sorted(slug_index, key=len, reverse=True)

    for first_slug in known_slugs:
        prefix = f"{first_slug}_"
        if not base.startswith(prefix):
            continue
        second_slug = base[len(prefix):]
        if second_slug in slug_index:
            return slug_index[first_slug]["display_name"], slug_index[second_slug]["display_name"]

    return None, None
