"""
Antigravity Data Compilation Engine - Static Asset Generator
Executes single-pass analytics sweeps and saves payloads as static JSON files.
"""

import os
import json
from pathlib import Path
import pandas as pd
from google.cloud import bigquery

# Import your optimized production queries
from fifa_metrics_bq import (
    get_match_stats_both_teams,
    get_match_momentum_timeline,
    get_match_obv_breakdown,
    get_possession_adjusted_defensive_stats,
    get_match_radar_stats,
    get_match_progressive_actions,
    get_match_playing_styles
)

# Initialize Storage Paths
DATA_DIR = Path("./data/matches")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def serialize_dataframe(df: pd.DataFrame) -> list:
    """Safely converts DataFrames containing NaNs or infs to clean dictionary arrays."""
    if df.empty:
        return []
    return json.loads(df.replace({np.nan: None, np.inf: None, -np.inf: None}).to_json(orient="records"))

def process_match_to_static(client: bigquery.Client, match_id: int):
    """
    Executes a single-pass extraction of all advanced match metrics, 
    serializing data shapes to disk to eliminate BigQuery call overhead.
    """
    print(f"⚙️ Pre-calculating analytical profiles for Match ID: {match_id}...")
    match_folder = DATA_DIR / str(match_id)
    match_folder.mkdir(parents=True, exist_ok=True)
    
    # 1. Single-Pass Consolidated Base Stats
    t1_stats, t2_stats, t1_name, t2_name = get_match_stats_both_teams(client, match_id)
    
    # 2. Extract Spatio-Temporal & Style Timelines
    momentum_df = get_match_momentum_timeline(client, match_id)
    obv_df = get_match_obv_breakdown(client, match_id)
    padj_df = get_possession_adjusted_defensive_stats(client, match_id)
    styles_df = get_match_playing_styles(client, match_id)
    
    # 3. Extract Team-Specific Pitch Visual Arrays
    t1_radar = get_match_radar_stats(client, match_id, t1_name)
    t2_radar = get_match_radar_stats(client, match_id, t2_name)
    t1_prog = get_match_progressive_actions(client, match_id, t1_name)
    t2_prog = get_match_progressive_actions(client, match_id, t2_name)
    
    # Compile Unified Metric Object
    payload = {
        "metadata": {
            "match_id": match_id,
            "team1": t1_name,
            "team2": t2_name
        },
        "base_statistics": {
            "team1": t1_stats,
            "team2": t2_stats
        },
        "radar_profiles": {
            "team1": t1_radar,
            "team2": t2_radar
        },
        "timelines": {
            "momentum": serialize_dataframe(momentum_df),
            "obv_breakdown": serialize_dataframe(obv_df),
            "padj_defensive": serialize_dataframe(padj_df),
            "playing_styles": serialize_dataframe(styles_df)
        },
        "progressive_actions": {
            "team1": serialize_dataframe(t1_prog),
            "team2": serialize_dataframe(t2_prog)
        }
    }
    
    # Write directly to match workspace partition
    with open(match_folder / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
    print(f"✅ Match {match_id} successfully compiled as static file.")

def compile_all_completed_fixtures(match_ids: list):
    """Orchestrates the build loop using native machine credentials."""
    client = bigquery.Client()
    for mid in match_ids:
        try:
            process_match_to_static(client, mid)
        except Exception as e:
            print(f"❌ Failed to parse metrics for match {mid}: {str(e)}")

if __name__ == "__main__":
    # The Antigravity agent can dynamically replace this list based on fixture tracking sheets
    completed_matches = [1001, 1002, 1003] 
    compile_all_completed_fixtures(completed_matches)