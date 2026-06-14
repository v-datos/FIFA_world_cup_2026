"""
FIFA Dashboard Metrics Helper Functions - BigQuery Version
Adapted for BigQuery database queries on StatsBomb event data
"""

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from typing import Dict, Union, Optional, Tuple
from bigquery_helpers import execute_query

def get_match_stats_both_teams(client: bigquery.Client, match_id: int) -> Tuple[Dict[str, Union[int, float]], Dict[str, Union[int, float]], str, str]:
    """
    Get comprehensive match statistics for BOTH teams in a single optimized query.
    """
    query = """
    SELECT
        team,
        total_xg, shots, shots_on_target, woodwork_shots, goals,
        passes, successful_passes, throw_ins, carries,
        free_kicks, final_3rd_passes, final_3rd_carries,
        dribbles, successful_dribbles, miscontrols_errors,
        goalkeeper_saves, corners, tackles, fouls,
        interceptions, successful_interceptions, cards,
        pressure, counterpress, ball_recoveries, successful_ball_recoveries,
        offensive_fouls, fouls_won, blocks, block_shot_to_goal,
        clearances, aerial_clearances,
        pass_accuracy, dribble_success_percentage,
        interception_success_percentage, ball_recovery_success_percentage,
        possession_pct
    FROM `midyear-castle-328020.fifa_data.match_team_stats_summary`
    WHERE match_id = @match_id
    ORDER BY team
    """

    params = [bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id))]
    result_df = execute_query(client, query, params)

    if result_df.empty or len(result_df) < 2:
        empty_stats = {
            'total_xg': 0.0, 'shots': 0, 'shots_on_target': 0, 'woodwork_shots': 0, 'goals': 0,
            'passes': 0, 'successful_passes': 0, 'throw_ins': 0, 'carries': 0,
            'free_kicks': 0, 'final_3rd_passes': 0, 'final_3rd_carries': 0,
            'dribbles': 0, 'successful_dribbles': 0, 'miscontrols_errors': 0,
            'goalkeeper_saves': 0, 'corners': 0, 'tackles': 0, 'fouls': 0,
            'interceptions': 0, 'successful_interceptions': 0, 'cards': 0,
            'counterpress': 0, 'ball_recoveries': 0, 'successful_ball_recoveries': 0,
            'offensive_fouls': 0, 'fouls_won': 0, 'blocks': 0, 'block_shot_to_goal': 0,
            'clearances': 0, 'aerial_clearances': 0,
            'pressure': 0, 'possession_pct': 0, 'pass_accuracy': 0,
            'dribble_success_percentage': 0, 'interception_success_percentage': 0,
            'ball_recovery_success_percentage': 0, '50_50_success_percentage': 0
        }
        return empty_stats, empty_stats, "Unknown", "Unknown"

    team1_name = result_df.iloc[0]['team']
    team2_name = result_df.iloc[1]['team']

    team1_stats = result_df.iloc[0].to_dict()
    team2_stats = result_df.iloc[1].to_dict()

    del team1_stats['team']
    del team2_stats['team']

    for stats in [team1_stats, team2_stats]:
        for key in stats:
            if pd.isna(stats[key]):
                stats[key] = 0

    return team1_stats, team2_stats, team1_name, team2_name

def get_match_momentum_timeline(client: bigquery.Client, match_id: int) -> pd.DataFrame:
    query = """
    WITH match_events AS (
        SELECT
            team,
            minute,
            second,
            player,
            type,
            shot_outcome,
            shot_statsbomb_xg,
            foul_committed_card
        FROM events
        WHERE match_id = @match_id
          AND (
               (type = 'Shot' AND shot_type != 'Penalty' AND shot_statsbomb_xg IS NOT NULL)
               OR
               (foul_committed_card IN ('Yellow Card', 'Red Card'))
          )
    ),
    all_events AS (
        SELECT
            team,
            minute,
            second,
            player,
            type,
            shot_outcome,
            COALESCE(shot_statsbomb_xg, 0.0) as shot_statsbomb_xg,
            CASE
                WHEN type = 'Shot' AND shot_outcome = 'Goal' THEN 'Goal'
                WHEN type = 'Shot' THEN 'Shot'
                WHEN foul_committed_card = 'Yellow Card' THEN 'Yellow Card'
                WHEN foul_committed_card = 'Red Card' THEN 'Red Card'
                ELSE 'Card'
            END as event_type,
            CASE
                WHEN type = 'Shot' THEN CONCAT(
                    player, ' - ',
                    CASE WHEN shot_outcome = 'Goal' THEN '⚽ GOAL' ELSE 'Shot' END,
                    ' (xG: ', ROUND(shot_statsbomb_xg, 2), ')'
                )
                ELSE CONCAT(player, ' - ', foul_committed_card)
            END as description
        FROM match_events
    ),
    cumulative_xg_cte AS (
        SELECT
            team,
            minute,
            second,
            player,
            event_type,
            description,
            shot_statsbomb_xg,
            SUM(shot_statsbomb_xg) OVER (
                PARTITION BY team
                ORDER BY minute, second
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ) as cumulative_xg
        FROM all_events
    )
    SELECT
        team,
        minute,
        ROUND(cumulative_xg, 3) as cumulative_xg,
        event_type,
        player,
        description
    FROM cumulative_xg_cte
    ORDER BY minute, second
    """
    params = [bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id))]
    return execute_query(client, query, params)


def get_match_playing_styles(client: bigquery.Client, match_id: int) -> pd.DataFrame:
    query = """
    WITH
    match_events AS (
        SELECT
            team,
            type,
            x,
            shot_type,
            shot_statsbomb_xg
        FROM events
        WHERE match_id = @match_id
            AND team IS NOT NULL
    ),
    total_events AS (
        SELECT COUNT(*) as total_count FROM match_events
    ),
    team_metrics AS (
        SELECT
            me.team,
            ROUND(
                SAFE_DIVIDE(
                    COUNTIF(me.x > 60 AND me.x IS NOT NULL),
                    NULLIF(COUNTIF(me.x IS NOT NULL), 0)
                ) * 100,
                1
            ) as field_tilt_pct,
            COUNTIF(me.type IN ('Pressure', 'Tackle', 'Interception', 'Block')) as defensive_actions,
            COUNTIF(me.type = 'Pass') as pass_count,
            ROUND(
                SUM(CASE WHEN me.type = 'Shot' AND me.shot_type != 'Penalty' THEN me.shot_statsbomb_xg ELSE 0.0 END),
                2
            ) as xg_for,
            ROUND(
                SAFE_DIVIDE(COUNT(*), (SELECT total_count FROM total_events)) * 100,
                1
            ) as possession_pct
        FROM match_events me
        GROUP BY me.team
    )
    SELECT
        tm1.team,
        tm1.field_tilt_pct,
        ROUND(
            SAFE_DIVIDE(tm2.pass_count, NULLIF(tm1.defensive_actions, 0)),
            2
        ) as ppda,
        tm1.possession_pct,
        tm1.xg_for,
        tm2.xg_for as xg_against,
        ROUND(tm1.xg_for - tm2.xg_for, 2) as net_xg
    FROM team_metrics tm1
    CROSS JOIN team_metrics tm2
    WHERE tm1.team != tm2.team
    ORDER BY tm1.team
    """
    params = [bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id))]
    return execute_query(client, query, params)


def get_match_progressive_actions(client: bigquery.Client, match_id: int, team: str) -> pd.DataFrame:
    query = """
    WITH
    team_events AS (
        SELECT
            type,
            player,
            x,
            y,
            pass_end_x,
            pass_end_y,
            carry_end_x,
            carry_end_y,
            CASE
                WHEN type = 'Pass'
                     AND pass_outcome IS NULL
                     AND x IS NOT NULL
                     AND pass_end_x IS NOT NULL
                     AND (
                         (CAST(x AS FLOAT64) < 80 AND CAST(pass_end_x AS FLOAT64) >= 80)
                         OR
                         (CAST(x AS FLOAT64) >= 80 AND CAST(pass_end_x AS FLOAT64) > CAST(x AS FLOAT64) + 10)
                         OR
                         (CAST(pass_end_x AS FLOAT64) - CAST(x AS FLOAT64) >= 30)
                     )
                THEN TRUE
                ELSE FALSE
            END as is_progressive_pass,
            CASE
                WHEN type = 'Carry'
                     AND x IS NOT NULL
                     AND carry_end_x IS NOT NULL
                     AND (
                         (CAST(x AS FLOAT64) < 80 AND CAST(carry_end_x AS FLOAT64) >= 80)
                         OR
                         (CAST(x AS FLOAT64) >= 80 AND CAST(carry_end_x AS FLOAT64) > CAST(x AS FLOAT64) + 10)
                         OR
                         (CAST(carry_end_x AS FLOAT64) - CAST(x AS FLOAT64) >= 20)
                     )
                THEN TRUE
                ELSE FALSE
            END as is_progressive_carry
        FROM events
        WHERE match_id = @match_id
            AND team = @team
            AND type IN ('Pass', 'Carry')
    )
    SELECT
        CASE
            WHEN is_progressive_pass THEN 'Progressive Pass'
            WHEN is_progressive_carry THEN 'Progressive Carry'
        END as action_type,
        player,
        CAST(x AS FLOAT64) as x,
        CAST(y AS FLOAT64) as y,
        CASE
            WHEN is_progressive_pass THEN CAST(pass_end_x AS FLOAT64)
            WHEN is_progressive_carry THEN CAST(carry_end_x AS FLOAT64)
        END as end_x,
        CASE
            WHEN is_progressive_pass THEN CAST(pass_end_y AS FLOAT64)
            WHEN is_progressive_carry THEN CAST(carry_end_y AS FLOAT64)
        END as end_y
    FROM team_events
    WHERE is_progressive_pass OR is_progressive_carry
    ORDER BY CAST(x AS FLOAT64)
    """
    params = [
        bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)),
        bigquery.ScalarQueryParameter("team", "STRING", team)
    ]
    return execute_query(client, query, params)

def get_match_obv_breakdown(client: bigquery.Client, match_id: int) -> pd.DataFrame:
    query = """
    WITH
    all_obv_components AS (
        SELECT
            team,
            COUNTIF(
                type = 'Pass'
                AND pass_outcome IS NULL
                AND CAST(x AS FLOAT64) < 80.0
                AND CAST(pass_end_x AS FLOAT64) >= 80.0
            ) * 0.02 as progressive_pass_value,
            COUNTIF(pass_shot_assist = TRUE OR pass_goal_assist = TRUE) * 0.05 as assist_value,
            COUNTIF(
                type = 'Pass'
                AND pass_outcome IS NULL
                AND under_pressure = TRUE
            ) * 0.01 as pressure_pass_value,
            SUM(CASE WHEN type = 'Shot' AND shot_type != 'Penalty' THEN shot_statsbomb_xg ELSE 0.0 END) as shot_xg_value,
            COUNTIF(shot_statsbomb_xg > 0.3) * 0.03 as high_quality_shot_value,
            COUNTIF(type = 'Dribble' AND dribble_outcome = 'Complete') * 0.015 as dribble_success_value,
            COUNTIF(
                type = 'Carry'
                AND CAST(x AS FLOAT64) < 80.0
                AND CAST(carry_end_x AS FLOAT64) >= 80.0
            ) * 0.02 as progressive_carry_value,
            (COUNTIF(type = 'Interception') * 0.01 +
             COUNTIF(type = 'Block') * 0.015 +
             COUNTIF(type = 'Clearance') * 0.005 +
             COUNTIF(type = 'Duel' AND duel_outcome = 'Won') * 0.01) as defensive_action_value
        FROM events
        WHERE match_id = @match_id AND team IS NOT NULL
        GROUP BY team
    )
    SELECT
        team,
        ROUND(progressive_pass_value + assist_value + pressure_pass_value, 3) as pass_obv_proxy,
        ROUND(shot_xg_value + high_quality_shot_value, 3) as shot_obv_proxy,
        ROUND(dribble_success_value + progressive_carry_value, 3) as dribble_obv_proxy,
        ROUND(defensive_action_value, 3) as defensive_obv_proxy,
        ROUND(
            progressive_pass_value + assist_value + pressure_pass_value +
            shot_xg_value + high_quality_shot_value +
            dribble_success_value + progressive_carry_value +
            defensive_action_value,
            3
        ) as total_obv_proxy
    FROM all_obv_components
    ORDER BY total_obv_proxy DESC
    """
    params = [bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id))]
    return execute_query(client, query, params)

def get_possession_adjusted_defensive_stats(client: bigquery.Client, match_id: int) -> pd.DataFrame:
    query = """
    WITH
    combined_stats AS (
        SELECT
            team,
            possession_team,
            type,
            duel_type,
            duel_outcome,
            shot_type,
            shot_statsbomb_xg
        FROM events
        WHERE match_id = @match_id
            AND (team IS NOT NULL OR possession_team IS NOT NULL)
            AND type != 'Starting XI'
    ),
    possession_pct AS (
        SELECT
            possession_team as team,
            COUNT(*) as possession_events,
            SUM(COUNT(*)) OVER () as total_events,
            ROUND(CAST(COUNT(*) AS FLOAT64) / CAST(SUM(COUNT(*)) OVER () AS FLOAT64) * 100, 1) as possession_percentage,
            ROUND((1 - CAST(COUNT(*) AS FLOAT64) / CAST(SUM(COUNT(*)) OVER () AS FLOAT64)) * 100, 1) as out_of_possession_pct
        FROM combined_stats
        WHERE possession_team IS NOT NULL
        GROUP BY possession_team
    ),
    defensive_stats AS (
        SELECT
            team,
            COUNTIF(type = 'Duel' AND duel_type = 'Tackle') as tackles,
            COUNTIF(type = 'Interception') as interceptions,
            COUNTIF(type = 'Pressure') as pressures,
            COUNTIF(type = 'Clearance') as clearances,
            COUNTIF(type = 'Block') as blocks,
            SAFE_DIVIDE(
                COUNTIF(type = 'Duel' AND duel_type = 'Tackle' AND duel_outcome = 'Won'),
                NULLIF(COUNTIF(type = 'Duel' AND duel_type = 'Tackle'), 0)
            ) * 100 as tackle_success_pct,
            COUNTIF(type = 'Dribbled Past') as dribbled_past
        FROM combined_stats
        WHERE team IS NOT NULL
        GROUP BY team
    ),
    shots_by_team AS (
        SELECT
            team as attacking_team,
            COUNT(*) as shots_by,
            SUM(CASE WHEN shot_type != 'Penalty' THEN shot_statsbomb_xg ELSE 0.0 END) as xg_by
        FROM combined_stats
        WHERE type = 'Shot'
        GROUP BY team
    ),
    shots_faced AS (
        SELECT
            ds.team as defending_team,
            COALESCE(sbt.shots_by, 0) as shots_against,
            COALESCE(sbt.xg_by, 0.0) as xg_against
        FROM defensive_stats ds
        LEFT JOIN shots_by_team sbt ON ds.team != sbt.attacking_team
    )
    SELECT
        pp.team,
        pp.possession_percentage,
        ds.tackles,
        ds.interceptions,
        ROUND(CAST(ds.tackles + ds.interceptions AS FLOAT64) / (pp.out_of_possession_pct / 100), 1) as padj_tackles_interceptions,
        ds.pressures,
        ROUND(CAST(ds.pressures AS FLOAT64) / (pp.out_of_possession_pct / 100), 1) as padj_pressures,
        ds.clearances,
        ROUND(CAST(ds.clearances AS FLOAT64) / (pp.out_of_possession_pct / 100), 1) as padj_clearances,
        ds.blocks,
        sf.shots_against,
        ROUND(SAFE_DIVIDE(CAST(ds.blocks AS FLOAT64), CAST(sf.shots_against AS FLOAT64)), 2) as blocks_per_shot,
        ROUND(ds.tackle_success_pct, 1) as tackle_success_pct,
        ds.dribbled_past,
        ROUND(
            SAFE_DIVIDE(
                CAST(ds.tackles AS FLOAT64),
                CAST(ds.tackles + ds.dribbled_past AS FLOAT64)
            ) * 100,
            1
        ) as tackle_dribbled_past_pct,
        ROUND(sf.xg_against, 2) as xg_against
    FROM possession_pct pp
    JOIN defensive_stats ds ON pp.team = ds.team
    JOIN shots_faced sf ON pp.team = sf.defending_team
    ORDER BY pp.possession_percentage DESC
    """
    params = [bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id))]
    return execute_query(client, query, params)

def get_match_radar_stats(client: bigquery.Client, match_id: int, team: str) -> Dict[str, float]:
    query = """
    SELECT
        SUM(CASE WHEN team = @team AND type = 'Shot' AND shot_type != 'Penalty' THEN shot_statsbomb_xg ELSE 0.0 END) as np_xg,
        COUNTIF(team = @team AND type = 'Shot' AND shot_type != 'Penalty') as total_shots,
        COUNTIF(team = @team AND type = 'Shot' AND shot_outcome IN ('Goal', 'Saved', 'Saved to Post')) as shots_on_target,
        COUNTIF(team = @team AND type = 'Pass') as total_passes,
        COUNTIF(team = @team AND type = 'Pass' AND pass_outcome IS NULL) as completed_passes,
        COUNTIF(
            team = @team
            AND type = 'Pass'
            AND pass_outcome IS NULL
            AND CAST(x AS FLOAT64) < 80.0
            AND CAST(pass_end_x AS FLOAT64) >= 80.0
        ) as progressive_passes,
        COUNTIF(team = @team AND (pass_shot_assist = TRUE OR pass_goal_assist = TRUE)) as key_passes,
        COUNTIF(team = @team AND type = 'Dribble' AND dribble_outcome = 'Complete') as dribbles_completed,
        COUNTIF(team = @team AND type = 'Duel' AND duel_type = 'Tackle') as tackles,
        COUNTIF(team = @team AND type = 'Interception') as interceptions,
        COUNTIF(team = @team AND type = 'Pressure') as pressures,
        COUNTIF(team = @team AND type = 'Duel' AND duel_type IN ('Aerial Lost', 'Aerial Won')) as aerial_duels,
        COUNTIF(team = @team AND type = 'Duel' AND duel_type = 'Aerial Won') as aerial_wins,
        COUNTIF(team = @team AND type = 'Foul Won') as fouls_won,
        MAX(minute) as max_minute
    FROM events
    WHERE match_id = @match_id
    """
    params = [
        bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)),
        bigquery.ScalarQueryParameter("team", "STRING", team)
    ]
    df = execute_query(client, query, params)
    if df.empty:
        return {}
    row = df.iloc[0]
    
    max_min = row['max_minute'] if pd.notna(row['max_minute']) and row['max_minute'] > 0 else 90.0
    np_xg = row['np_xg'] if pd.notna(row['np_xg']) else 0.0
    total_shots = row['total_shots'] if pd.notna(row['total_shots']) else 0
    shots_on_target = row['shots_on_target'] if pd.notna(row['shots_on_target']) else 0
    total_passes = row['total_passes'] if pd.notna(row['total_passes']) else 0
    completed_passes = row['completed_passes'] if pd.notna(row['completed_passes']) else 0
    progressive_passes = row['progressive_passes'] if pd.notna(row['progressive_passes']) else 0
    key_passes = row['key_passes'] if pd.notna(row['key_passes']) else 0
    dribbles_completed = row['dribbles_completed'] if pd.notna(row['dribbles_completed']) else 0
    tackles = row['tackles'] if pd.notna(row['tackles']) else 0
    interceptions = row['interceptions'] if pd.notna(row['interceptions']) else 0
    pressures = row['pressures'] if pd.notna(row['pressures']) else 0
    aerial_duels = row['aerial_duels'] if pd.notna(row['aerial_duels']) else 0
    aerial_wins = row['aerial_wins'] if pd.notna(row['aerial_wins']) else 0
    fouls_won = row['fouls_won'] if pd.notna(row['fouls_won']) else 0

    return {
        'Non-Penalty xG': round(np_xg, 2),
        'Shots on Target %': round((shots_on_target / total_shots * 100), 1) if total_shots > 0 else 0.0,
        'Shots/90': round(total_shots / (max_min / 90.0), 1),
        'Pass Completion %': round((completed_passes / total_passes * 100), 1) if total_passes > 0 else 0.0,
        'Progressive Passes/90': round(progressive_passes / (max_min / 90.0), 1),
        'Key Passes/90': round(key_passes / (max_min / 90.0), 2),
        'Dribbles/90': round(dribbles_completed / (max_min / 90.0), 1),
        'Tackles+Int/90': round((tackles + interceptions) / (max_min / 90.0), 1),
        'Pressures/90': round(pressures / (max_min / 90.0), 1),
        'Aerial Win %': round((aerial_wins / aerial_duels * 100), 1) if aerial_duels > 0 else 0.0,
        'Foul Won/90': round(fouls_won / (max_min / 90.0), 1)
    }