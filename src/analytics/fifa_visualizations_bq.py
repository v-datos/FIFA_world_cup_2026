# FIFA Dashboard Visualization Functions - BigQuery Version
# Using mplsoccer for pitch-based visualizations with BigQuery backend

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from pathlib import Path
from mplsoccer import Pitch, VerticalPitch, Radar
from matplotlib.font_manager import FontProperties
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Tuple
from google.cloud import bigquery

# Import BigQuery helpers
from bigquery_helpers import execute_query


# Load custom fonts (if available)
_FONT_PATH = Path(__file__).parent / "Play-Regular.ttf"
try:
    font_play = FontProperties(fname=str(_FONT_PATH))
    font_play_bold = FontProperties(fname=str(_FONT_PATH), weight='bold')
except OSError:
    font_play = FontProperties()
    font_play_bold = FontProperties(weight='bold')


def create_shot_map(client: bigquery.Client, team: str,
                   competition: Optional[str] = None,
                   match_id: Optional[int] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create shot map visualization for a team using mplsoccer.
    """
    conditions = ["team = @team", "type = 'Shot'", "x IS NOT NULL", "y IS NOT NULL"]
    params = [bigquery.ScalarQueryParameter("team", "STRING", team)]

    if competition:
        conditions.append("competition_name = @competition")
        params.append(bigquery.ScalarQueryParameter("competition", "STRING", competition))

    if match_id:
        conditions.append("match_id = @match_id")
        params.append(bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)))

    where_clause = " AND ".join(conditions)

    query = f"""
    SELECT
        x, y,
        shot_outcome,
        shot_statsbomb_xg,
        shot_type
    FROM events
    WHERE {where_clause}
    """

    shots_df = execute_query(client, query, params)

    if shots_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'No shot data available for {team}',
                ha='center', va='center', fontsize=14)
        return fig, ax

    fig, ax = plt.subplots(figsize=(10, 6))
    pitch = VerticalPitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='white',
                          half=True, pad_bottom=0.5)
    pitch.draw(ax=ax)

    goals = shots_df[shots_df['shot_outcome'] == 'Goal']
    other_shots = shots_df[shots_df['shot_outcome'] != 'Goal']

    if not other_shots.empty:
        pitch.scatter(other_shots.x, other_shots.y,
                     s=other_shots.shot_statsbomb_xg * 800,
                     c='red', alpha=0.7, ax=ax, label='Shots')

    if not goals.empty:
        pitch.scatter(goals.x, goals.y,
                     s=goals.shot_statsbomb_xg * 800,
                     marker='football', c='white', alpha=0.9,
                     ax=ax, label='Goals')

    title = f'{team} - Shot Map (Size = xG)'
    ax.set_title(title, fontsize=22, pad=20, fontproperties=font_play_bold)

    ax.legend(loc='upper right')

    plt.tight_layout()
    return fig, ax

def create_pass_network(client: bigquery.Client, team: str, match_id: int,
                       half: Optional[int] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create pass network visualization for a team in a match.
    """
    params = [
        bigquery.ScalarQueryParameter("team",     "STRING", team),
        bigquery.ScalarQueryParameter("match_id", "INT64",  int(match_id)),
    ]
    half_clause = "AND period = @half" if half is not None else ""
    if half is not None:
        params.append(bigquery.ScalarQueryParameter("half", "INT64", int(half)))

    if half is not None:
        query = f"""
        WITH passes AS (
            SELECT player, pass_recipient, x, y, pass_end_x, pass_end_y
            FROM events
            WHERE team = @team
              AND match_id = @match_id
              AND type = 'Pass'
              AND pass_outcome IS NULL
              {half_clause}
              AND x IS NOT NULL AND y IS NOT NULL
              AND pass_end_x IS NOT NULL AND pass_end_y IS NOT NULL
              AND pass_recipient IS NOT NULL
        ),
        player_pos AS (
            SELECT player, AVG(x) AS x, AVG(y) AS y
            FROM passes
            GROUP BY player
        ),
        pass_conn AS (
            SELECT player AS passer, pass_recipient AS recipient, COUNT(*) AS cnt
            FROM passes
            GROUP BY passer, recipient
        ),
        conn_with_pos AS (
            SELECT 'connection' AS row_type,
                   passer AS player,
                   recipient,
                   cnt AS count,
                   pp1.x AS x_start, pp1.y AS y_start,
                   pp2.x AS x_end, pp2.y AS y_end
            FROM pass_conn
            LEFT JOIN player_pos pp1 ON pp1.player = passer
            LEFT JOIN player_pos pp2 ON pp2.player = recipient
        ),
        pos_rows AS (
            SELECT 'position' AS row_type, player, CAST(NULL AS STRING) AS recipient, CAST(NULL AS INT64) AS count,
                   x AS x_start, y AS y_start, CAST(NULL AS FLOAT64) AS x_end, CAST(NULL AS FLOAT64) AS y_end
            FROM player_pos
        )
        SELECT * FROM conn_with_pos
        UNION ALL
        SELECT * FROM pos_rows
        """
    else:
        query = """
        WITH summary AS (
            SELECT
                player, avg_x AS x, avg_y AS y, pass_count,
                pass_recipient AS recipient, pass_volume AS count,
                recipient_avg_x AS x_end, recipient_avg_y AS y_end
            FROM `midyear-castle-328020.fifa_data.pass_network_summary`
            WHERE match_id = @match_id AND team = @team
        ),
        conn_with_pos AS (
            SELECT 'connection' AS row_type,
                   player, recipient, count,
                   x AS x_start, y AS y_start,
                   x_end, y_end
            FROM summary
        ),
        pos_rows AS (
            SELECT 'position' AS row_type,
                   player, CAST(NULL AS STRING) AS recipient, CAST(NULL AS INT64) AS count,
                   x AS x_start, y AS y_start, CAST(NULL AS FLOAT64) AS x_end, CAST(NULL AS FLOAT64) AS y_end
            FROM summary
            GROUP BY player, x, y
        )
        SELECT * FROM conn_with_pos
        UNION ALL
        SELECT * FROM pos_rows
        """

    net_df = execute_query(client, query, params)

    if net_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'No pass data available',
                ha='center', va='center', fontsize=14)
        return fig, ax

    positions = net_df[net_df['row_type'] == 'position'][['player', 'x_start', 'y_start']].rename(columns={'x_start': 'x', 'y_start': 'y'})
    connections = net_df[net_df['row_type'] == 'connection']

    fig, ax = plt.subplots(figsize=(14, 10))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#22312b', line_color='white')
    pitch.draw(ax=ax)

    top_connections = connections[connections['count'] >= 3]

    if not top_connections.empty:
        for _, row in top_connections.iterrows():
            pitch.lines(row['x_start'], row['y_start'],
                       row['x_end'], row['y_end'],
                       lw=row['count'] / 3, color='white', alpha=0.5,
                       ax=ax, zorder=1)

    pitch.scatter(positions.x, positions.y,
                 s=300, c='#FF4444', edgecolors='white',
                 linewidth=2, alpha=0.9, ax=ax, zorder=2)

    for _, row in positions.iterrows():
        last_name = row['player'].split()[-1] if ' ' in row['player'] else row['player']
        ax.text(row['x'], row['y'], last_name[:8], fontsize=7,
               ha='center', va='center', color='white', weight='bold',
               zorder=3)

    half_text = f" - Half {half}" if half else ""
    ax.set_title(f'{team} Pass Network{half_text}', fontsize=16, pad=20,
                fontproperties=font_play_bold, color='white')

    plt.tight_layout()
    return fig, ax

def create_touch_heatmap(client: bigquery.Client, team: str,
                        competition: Optional[str] = None,
                        player: Optional[str] = None,
                        match_id: Optional[int] = None) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create touch/action heatmap for a team or player.
    """
    conditions = ["team = @team", "x IS NOT NULL", "y IS NOT NULL"]
    params = [bigquery.ScalarQueryParameter("team", "STRING", team)]

    if competition:
        conditions.append("competition_name = @competition")
        params.append(bigquery.ScalarQueryParameter("competition", "STRING", competition))

    if player:
        conditions.append("player = @player")
        params.append(bigquery.ScalarQueryParameter("player", "STRING", player))

    if match_id:
        conditions.append("match_id = @match_id")
        params.append(bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)))

    where_clause = " AND ".join(conditions)

    if match_id is not None and not competition and not player:
        query = """
        SELECT t.x, t.y
        FROM `midyear-castle-328020.fifa_data.touch_heatmap_summary` s,
        UNNEST(s.touches) as t
        WHERE s.match_id = @match_id AND s.team = @team
        """
    else:
        query = f"""
        SELECT x, y
        FROM events
        WHERE {where_clause}
            AND type IN (
                'Pass',
                'Ball Receipt*',
                'Carry',
                'Ball Recovery',
                'Duel',
                'Clearance',
                'Block',
                'Foul Committed',
                'Dribble',
                'Foul Won',
                'Shot',
                'Miscontrol',
                'Dispossessed',
                'Interception',
                'Dribbled Past',
                '50/50',
                'Shield',
                'Offside'
            )
        LIMIT 50000
        """

    touches_df = execute_query(client, query, params)

    if touches_df.empty:
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, 'No touch data available',
                ha='center', va='center', fontsize=14, color='white')
        fig.set_facecolor('#0e1116')
        return fig, ax

    fig, ax = plt.subplots(figsize=(14, 10))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#0e1116', line_color='white',
                  line_zorder=2)
    pitch.draw(ax=ax)

    pitch.kdeplot(touches_df.x, touches_df.y, ax=ax,
                  fill=True, levels=100,
                  thresh=0,
                  cut=4,
                  cmap='Reds',
                  cbar=False)

    cbar = fig.colorbar(
        ScalarMappable(cmap='Reds', norm=Normalize(vmin=0, vmax=1)),
        ax=ax, orientation='vertical', pad=0.02, shrink=0.7
    )
    cbar.set_label('Density of Touches', color='white', fontproperties=font_play, fontsize=14)
    cbar.ax.tick_params(colors='white')

    title = f"{player if player else team} Touch Heatmap"
    ax.set_title(title, fontsize=22, fontproperties=font_play_bold, color='white')

    fig.set_facecolor('#0e1116')

    plt.tight_layout()
    return fig, ax

def plot_attacking_passes(_client: bigquery.Client, team: str,
                          competition: Optional[str] = None,
                          match_id: Optional[int] = None) -> Tuple[plt.Figure, object]:
    """
    Plots a map of attacking passes (crosses, cutbacks, switches, and through balls) for a given team.
    """
    conditions = [
        "team = @team",
        "type = 'Pass'",
        "x IS NOT NULL AND y IS NOT NULL",
        "pass_end_x IS NOT NULL AND pass_end_y IS NOT NULL",
    ]
    params = [bigquery.ScalarQueryParameter("team", "STRING", team)]

    if competition:
        conditions.append("competition_name = @competition")
        params.append(bigquery.ScalarQueryParameter("competition", "STRING", competition))
    if match_id:
        conditions.append("match_id = @match_id")
        params.append(bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)))

    where_clause = " AND ".join(conditions)

    query = f"""
    WITH base AS (
      SELECT x, y, pass_end_x, pass_end_y, pass_outcome,
             ARRAY_CONCAT(
               IF(pass_cross = TRUE, ['cross'], []),
               IF(pass_cut_back = TRUE, ['cutback'], []),
               IF(pass_switch = TRUE, ['switch'], []),
               IF(pass_through_ball = TRUE, ['through'], [])
             ) AS kinds
      FROM events
      WHERE {where_clause}
    )
    SELECT x, y, pass_end_x, pass_end_y, pass_outcome, kind
    FROM base, UNNEST(kinds) AS kind
    """

    pass_df = execute_query(_client, query, params)

    if pass_df.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'No pass data available for {team}',
                ha='center', va='center', fontsize=14)
        return fig, ax

    cross_passes = pass_df[pass_df['kind'] == 'cross']
    cutback_passes = pass_df[pass_df['kind'] == 'cutback']
    switch_passes = pass_df[pass_df['kind'] == 'switch']
    through_ball_passes = pass_df[pass_df['kind'] == 'through']

    completed_passes = pass_df[pass_df['pass_outcome'].isna()]

    pitch = VerticalPitch(
        pitch_type='statsbomb',
        line_color='black',
    )

    fig, axs = pitch.grid(ncols=4, endnote_height=0, axis=False)
    fig.set_facecolor("#f4f4f4")

    if not cross_passes.empty:
        pitch.arrows(
            cross_passes.x, cross_passes.y, cross_passes.pass_end_x, cross_passes.pass_end_y,
            width=1, headwidth=8, headlength=8, color='#d73728', ax=axs['pitch'][0],
            label=f'{team} Cross Passes'
        )

    if not cutback_passes.empty:
        pitch.arrows(
            cutback_passes.x, cutback_passes.y, cutback_passes.pass_end_x, cutback_passes.pass_end_y,
            width=1, headwidth=8, headlength=8, color='blue', ax=axs['pitch'][1],
            label=f'{team} Cut Back Passes'
        )

    if not switch_passes.empty:
        pitch.arrows(
            switch_passes.x, switch_passes.y, switch_passes.pass_end_x, switch_passes.pass_end_y,
            width=1, headwidth=10, headlength=8, color='green', ax=axs['pitch'][2],
            label=f'{team} Switch Passes'
        )

    if not through_ball_passes.empty:
        pitch.arrows(
            through_ball_passes.x, through_ball_passes.y, through_ball_passes.pass_end_x, through_ball_passes.pass_end_y,
            width=1, headwidth=8, headlength=8, color='orange', ax=axs['pitch'][3],
            label=f'{team} Through ball Passes'
        )

    title_text = f'Attacking Passes for {team}'
    if match_id:
        title_text += f' - Match {match_id}'
    elif competition:
        title_text += f' - {competition}'

    axs['title'].text(
        0.55, 0.6, title_text, fontproperties=font_play_bold,
        color='#000009', va='center', ha='center', fontsize=36
    )

    axs['title'].text(
        0.06, 0.8, f"Total Passes: {len(pass_df)}",
        color='#000009', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    axs['title'].text(
        0.08, 0.6, f"Completed Passes: {len(completed_passes)}",
        color='#000009', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    completion_rate = (len(completed_passes) / len(pass_df) * 100) if len(pass_df) > 0 else 0
    axs['title'].text(
        0.08, 0.4, f"Completion Rate: {completion_rate:.2f}%",
        color='#000009', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    axs['title'].text(
        0.12, 0.1, f'Cross Passes: {len(cross_passes)}',
        color='#d73728', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    axs['title'].text(
        0.37, 0.1, f'Cut Back Passes: {len(cutback_passes)}',
        color='blue', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    axs['title'].text(
        0.63, 0.1, f'Switch Passes: {len(switch_passes)}',
        color='green', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    axs['title'].text(
        0.89, 0.1, f'Through Balls: {len(through_ball_passes)}',
        color='orange', va='center', ha='center', fontsize=18, fontproperties=font_play,
    )

    return fig, axs

def create_xg_distribution_comparison(client: bigquery.Client,
                                      team1: str, team2: str,
                                      match_id: Optional[int] = None,
                                      competition: Optional[str] = None) -> go.Figure:
    """
    Create an interactive histogram with rug plot to compare xG distributions.
    """
    teams = [team1, team2]
    colors = ["#667eea", "#f5576c"]
    
    plot_data = []
    for team, color in zip(teams, colors):
        conditions = ["team = @team", "type = 'Shot'", "shot_type != 'Penalty'", "shot_statsbomb_xg IS NOT NULL"]
        params = [bigquery.ScalarQueryParameter("team", "STRING", team)]

        if match_id:
            conditions.append("match_id = @match_id")
            params.append(bigquery.ScalarQueryParameter("match_id", "INT64", int(match_id)))
        if competition:
            conditions.append("competition_name = @competition")
            params.append(bigquery.ScalarQueryParameter("competition", "STRING", competition))

        where_clause = " AND ".join(conditions)
        query = f"SELECT shot_statsbomb_xg FROM events WHERE {where_clause}"
        xg_df = execute_query(client, query, params)
        
        if not xg_df.empty and not xg_df['shot_statsbomb_xg'].empty:
            temp_df = xg_df['shot_statsbomb_xg'].dropna().to_frame(name='xG')
            temp_df['team'] = team
            temp_df['color'] = color
            plot_data.append(temp_df)

    if not plot_data:
        fig = go.Figure()
        fig.add_annotation(text="No xG data available for comparison.", showarrow=False)
        fig.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig

    full_df = pd.concat(plot_data)

    fig = px.violin(
        full_df,
        x="xG",
        color="team",
        color_discrete_map={team1: colors[0], team2: colors[1]},
        violinmode='overlay',
        orientation='h',
        points='all',
        title='Non-Penalty xG Distribution Comparison',
    )

    fig.update_traces(side='positive')

    fig.update_layout(
        font=dict(family="Play, sans-serif", color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=''),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)')
    )

    return fig

def display_match_statistics(team1_stats, team2_stats, team1, team2):
    """
    Displays match statistics in a compact, easy-to-read 3-column layout.
    """
    team1_color = "#667eea"
    team2_color = "#f5576c"

    def _display_stat(metric_label, key, color1, color2, formatter="{:.0f}"):
        val1 = team1_stats.get(key, 0)
        val2 = team2_stats.get(key, 0)
        
        s_col1, s_col2, s_col3 = st.columns([1, 2, 1])
        with s_col1:
            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color: {color1};'>{formatter.format(val1)}</div>", unsafe_allow_html=True)
        with s_col2:
            st.markdown(f"<div style='text-align: center;'>{metric_label}</div>", unsafe_allow_html=True)
        with s_col3:
            st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color: {color2};'>{formatter.format(val2)}</div>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='text-align: center;'><span style='color:{team1_color};'>{team1}</span> vs <span style='color:{team2_color};'>{team2}</span></h3>", unsafe_allow_html=True)
    goals1 = int(team1_stats.get('goals', 0))
    goals2 = int(team2_stats.get('goals', 0))
    st.markdown(f"<h4 style='text-align: center;'><span style='color:{team1_color};'>{goals1}</span> - <span style='color:{team2_color};'>{goals2}</span></h4>", unsafe_allow_html=True)
    st.markdown("---")

    possession1 = team1_stats.get('possession_pct', 0)
    possession2 = team2_stats.get('possession_pct', 0)
    st.markdown(f"<div style='text-align: center;'>Possession</div>", unsafe_allow_html=True)
    p_col1, _, p_col3 = st.columns([1, 2, 1])
    p_col1.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color:{team1_color};'>{possession1:.1f}%</div>", unsafe_allow_html=True)
    p_col3.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color:{team2_color};'>{possession2:.1f}%</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="background-color: {team2_color}; border-radius: 5px; height: 10px;">
            <div style="background-color: {team1_color}; width: {possession1}%; border-radius: 5px; height: 10px;"></div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    attacking_stats = [
        {"label": "Total xG", "key": "total_xg", "formatter": "{:.2f}"},
        {"label": "Shots", "key": "shots"},
        {"label": "Shots on Target", "key": "shots_on_target"},
        {"label": "Corners", "key": "corners"},
        {"label": "Woodwork Shots", "key": "woodwork_shots"},
        {"label": "Offensive Fouls", "key": "offensive_fouls"},
        {"label": "Fouls Won", "key": "fouls_won"},
        {"label": "Blocks", "key": "blocks"},
        {"label": "Block Shot to Goal", "key": "block_shot_to_goal"},
        {"label": "Clearances", "key": "clearances"},
    ]
    
    passing_stats = [
        {"label": "Passes", "key": "passes"},
        {"label": "Pass Accuracy", "key": "pass_accuracy", "formatter": "{:.1f}%"},
        {"label": "Carries", "key": "carries"},
        {"label": "Final 3rd Passes", "key": "final_3rd_passes"},
        {"label": "Final 3rd Carries", "key": "final_3rd_carries"},
        {"label": "Dribbles", "key": "dribbles"},
        {"label": "Dribble Success %", "key": "dribble_success_percentage", "formatter": "{:.1f}%"},
        {"label": "Free Kicks", "key": "free_kicks"},
        {"label": "Throw Ins", "key": "throw_ins"},
        {"label": "Aerial Clearances", "key": "aerial_clearances"},
    ]

    defensive_stats = [
        {"label": "Goalkeeper Saves", "key": "goalkeeper_saves"},
        {"label": "Tackles", "key": "tackles"},
        {"label": "Fouls", "key": "fouls"},
        {"label": "Cards", "key": "cards"},
        {"label": "Interceptions", "key": "interceptions"},
        {"label": "Interception Success %", "key": "interception_success_percentage", "formatter": "{:.1f}%"},
        {"label": "Miscontrols/Errors", "key": "miscontrols_errors"},
        {"label": "Ball Recoveries", "key": "ball_recoveries"},
        {"label": "Ball Recovery Success %", "key": "ball_recovery_success_percentage", "formatter": "{:.1f}%"},
    ]

    col1, div1, col2, div2, col3 = st.columns([3, 0.1, 3, 0.1, 3])

    with col1:
        st.markdown("<h4 style='text-align: center;'>Attacking</h4>", unsafe_allow_html=True)
        for stat in attacking_stats:
            formatter = stat.get("formatter", "{:.0f}")
            _display_stat(stat["label"], stat["key"], team1_color, team2_color, formatter)

    with div1:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown("<div style='border-left: 1px solid #e0e0e0; height: 200px;'></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='text-align: center;'>Passing</h4>", unsafe_allow_html=True)
        for stat in passing_stats:
            formatter = stat.get("formatter", "{:.0f}")
            _display_stat(stat["label"], stat["key"], team1_color, team2_color, formatter)
            
    with div2:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        st.markdown("<div style='border-left: 1px solid #e0e0e0; height: 200px;'></div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<h4 style='text-align: center;'>Defensive</h4>", unsafe_allow_html=True)
        for stat in defensive_stats:
            _display_stat(stat["label"], stat["key"], team1_color, team2_color)

def _display_dual_stat_row(label: str, v1, v2, formatter="{:.2f}", color1="#667eea", color2="#f5576c"):
    try:
        v1_fmt = formatter.format(v1)
    except Exception:
        v1_fmt = str(v1)
    try:
        v2_fmt = formatter.format(v2)
    except Exception:
        v2_fmt = str(v2)
    s_col1, s_col2, s_col3 = st.columns([1, 2, 1])
    with s_col1:
        st.markdown(
            f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color: {color1};'>{v1_fmt}</div>",
            unsafe_allow_html=True,
        )
    with s_col2:
        st.markdown(f"<div style='text-align: center;'>{label}</div>", unsafe_allow_html=True)
    with s_col3:
        st.markdown(
            f"<div style='text-align: center; font-weight: bold; font-size: 1.1em; color: {color2};'>{v2_fmt}</div>",
            unsafe_allow_html=True,
        )

@st.cache_data(ttl=600)
def create_match_momentum_timeline(_client: bigquery.Client, match_id: int, team1: str, team2: str) -> go.Figure:
    from fifa_metrics_bq import get_match_momentum_timeline

    timeline_df = get_match_momentum_timeline(_client, match_id)

    if timeline_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text='No timeline data available',
            x=0.5, y=0.5,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=16, color='white')
        )
        fig.update_layout(
            plot_bgcolor='#0e1116',
            paper_bgcolor='#0e1116',
            font=dict(family='Play', color='white')
        )
        return fig

    fig = go.Figure()

    team_colors = {
        team1: '#667eea',
        team2: '#f5576c'
    }

    for team in [team1, team2]:
        team_data = timeline_df[timeline_df['team'] == team].copy()

        if not team_data.empty:
            start_row = pd.DataFrame([{
                'minute': 0,
                'cumulative_xg': 0,
                'team': team,
                'event_type': None,
                'player': None,
                'description': None
            }])
            team_data = pd.concat([start_row, team_data], ignore_index=True)

            fig.add_trace(go.Scatter(
                x=team_data['minute'],
                y=team_data['cumulative_xg'],
                mode='lines+markers',
                name=team,
                line=dict(color=team_colors.get(team, '#888888'), width=3),
                marker=dict(size=6, color=team_colors.get(team, '#888888')),
                hovertemplate='<b>%{fullData.name}</b><br>' + 
                              'Minute: %{x}<br>' + 
                              'Cumulative xG: %{y:.2f}<br>' + 
                              '<extra></extra>'
            ))

            goals = team_data[team_data['event_type'] == 'Goal']
            if not goals.empty:
                fig.add_trace(go.Scatter(
                    x=goals['minute'],
                    y=goals['cumulative_xg'],
                    mode='markers',
                    name=f'{team} Goals',
                    marker=dict(
                        symbol='star',
                        size=20,
                        color='gold',
                        line=dict(color=team_colors.get(team, '#888888'), width=2)
                    ),
                    text=goals['description'],
                    hovertemplate='<b>⚽ GOAL!</b><br>%{text}<br>Minute: %{x}<br><extra></extra>',
                    showlegend=False
                ))

            cards = team_data[team_data['event_type'].isin(['Yellow Card', 'Red Card'])]
            if not cards.empty:
                card_colors = cards['event_type'].map({
                    'Yellow Card': 'yellow',
                    'Red Card': 'red'
                })
                fig.add_trace(go.Scatter(
                    x=cards['minute'],
                    y=cards['cumulative_xg'],
                    mode='markers',
                    name=f'{team} Cards',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color=card_colors,
                        line=dict(color='black', width=1)
                    ),
                    text=cards['description'],
                    hovertemplate='%{text}<br>Minute: %{x}<br><extra></extra>',
                    showlegend=False
                ))

    fig.update_layout(
        title=dict(
            text=f'Match Momentum Timeline: {team1} vs {team2}',
            font=dict(size=20, family='Play', color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Match Minute',
            range=[0, 95],
            gridcolor='#333333',
            showgrid=True,
            zeroline=True,
            tickfont=dict(family='Play', color='white')
        ),
        yaxis=dict(
            title='Cumulative xG',
            gridcolor='#333333',
            showgrid=True,
            zeroline=True,
            tickfont=dict(family='Play', color='white')
        ),
        plot_bgcolor='#0e1116',
        paper_bgcolor='#0e1116',
        font=dict(family='Play', color='white'),
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            font=dict(family='Play', size=12)
        ),
        height=500
    )

    return fig

def display_obv_breakdown(_client: bigquery.Client, match_id: int, team1: str, team2: str):
    from fifa_metrics_bq import get_match_obv_breakdown

    obv_df = get_match_obv_breakdown(_client, match_id)

    if obv_df.empty:
        st.warning("No OBV data available for this match")
        return

    team1_data = obv_df[obv_df['team'] == team1]
    team2_data = obv_df[obv_df['team'] == team2]

    if team1_data.empty or team2_data.empty:
        st.warning("OBV data incomplete for one or both teams")
        return

    team1_vals = team1_data.iloc[0]
    team2_vals = team2_data.iloc[0]

    st.markdown("### 📊 On-Ball Value (OBV) Breakdown")
    st.markdown("*Quantifies value added by each action type (StatsBomb 2023 metric)*")

    team1_color = "#667eea"
    team2_color = "#f5576c"

    rows = [
        ("Total OBV", team1_vals['total_obv_proxy'], team2_vals['total_obv_proxy'], "{:.3f}"),
        ("Pass OBV", team1_vals['pass_obv_proxy'], team2_vals['pass_obv_proxy'], "{:.3f}"),
        ("Shot OBV", team1_vals['shot_obv_proxy'], team2_vals['shot_obv_proxy'], "{:.3f}"),
        ("Dribble & Carry OBV", team1_vals['dribble_obv_proxy'], team2_vals['dribble_obv_proxy'], "{:.3f}"),
        ("Defensive Action OBV", team1_vals['defensive_obv_proxy'], team2_vals['defensive_obv_proxy'], "{:.3f}"),
    ]
    for label, v1, v2, fmt in rows:
        _display_dual_stat_row(label, v1, v2, formatter=fmt, color1=team1_color, color2=team2_color)


def display_possession_adjusted_defensive_stats(_client: bigquery.Client, match_id: int, team1: str, team2: str):
    from fifa_metrics_bq import get_possession_adjusted_defensive_stats

    def_df = get_possession_adjusted_defensive_stats(_client, match_id)

    if def_df.empty:
        st.warning("No defensive statistics available for this match")
        return

    team1_data = def_df[def_df['team'] == team1]
    team2_data = def_df[def_df['team'] == team2]

    if team1_data.empty or team2_data.empty:
        st.warning("Defensive data incomplete for one or both teams")
        return

    team1_vals = team1_data.iloc[0]
    team2_vals = team2_data.iloc[0]

    st.markdown("### 🛡️ Possession-Adjusted Defensive Statistics")
    st.markdown("*Normalized defensive metrics accounting for possession share (StatsBomb 2023 standard)*")

    team1_color = "#667eea"
    team2_color = "#f5576c"

    _display_dual_stat_row("Possession %", team1_vals['possession_percentage'], team2_vals['possession_percentage'],
                           formatter="{:.1f}%", color1=team1_color, color2=team2_color)

    padj_rows = [
        ("PAdj Tackles & Interceptions", team1_vals['padj_tackles_interceptions'], team2_vals['padj_tackles_interceptions'], "{:.1f}"),
        ("PAdj Pressures", team1_vals['padj_pressures'], team2_vals['padj_pressures'], "{:.1f}"),
        ("PAdj Clearances", team1_vals['padj_clearances'], team2_vals['padj_clearances'], "{:.1f}"),
        ("Blocks / Shot Faced", team1_vals['blocks_per_shot'], team2_vals['blocks_per_shot'], "{:.2f}"),
        ("Tackle Success %", team1_vals['tackle_success_pct'], team2_vals['tackle_success_pct'], "{:.1f}%"),
        ("Tackle/Dribbled Past %", team1_vals['tackle_dribbled_past_pct'], team2_vals['tackle_dribbled_past_pct'], "{:.1f}%"),
        ("xG Against", team1_vals['xg_against'], team2_vals['xg_against'], "{:.2f}"),
    ]
    for label, v1, v2, fmt in padj_rows:
        _display_dual_stat_row(label, v1, v2, formatter=fmt, color1=team1_color, color2=team2_color)


@st.cache_data(ttl=600)
def get_cached_radar_chart(_client, match_id: int, team: str, team_color: str, params: list, low: list, high: list, values: list) -> bytes:
    from mplsoccer import Radar
    import matplotlib.pyplot as plt
    from bigquery_helpers import fig_to_png_bytes

    radar = Radar(
        params,
        low,
        high,
        round_int=[False] * len(params),
        num_rings=4,
        ring_width=1,
        center_circle_radius=1
    )

    fig, ax = radar.setup_axis(facecolor='None')
    rings_inner = radar.draw_circles(
        ax=ax,
        facecolor='#ffb2b2',
        edgecolor='#fc5f5f'
    )

    radar_output = radar.draw_radar(
        values,
        ax=ax,
        kwargs_radar={'facecolor': team_color, 'alpha': 0.6},
        kwargs_rings={'facecolor': '#66d8ba', 'alpha': 0.5}
    )

    range_labels = radar.draw_range_labels(
        ax=ax,
        fontsize=10,
        fontproperties=font_play,
        color='white'
    )

    param_labels = radar.draw_param_labels(
        ax=ax,
        fontsize=11,
        fontproperties=font_play,
        color='white'
    )

    ax.set_title(f"{team}\nMatch Radar",
                fontproperties=font_play_bold,
                fontsize=16,
                color='white',
                pad=20)

    fig.set_facecolor('#0e1116')
    fig.set_size_inches(8, 8)
    
    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes


def create_match_radar_comparison(_client: bigquery.Client, match_id: int, team1: str, team2: str):
    from fifa_metrics_bq import get_match_radar_stats

    team1_stats = get_match_radar_stats(_client, match_id, team1)
    team2_stats = get_match_radar_stats(_client, match_id, team2)

    if not team1_stats or not team2_stats:
        st.warning("Insufficient data for radar charts")
        return

    params = list(team1_stats.keys())
    team1_values = [v if v is not None else 0 for v in team1_stats.values()]
    team2_values = [v if v is not None else 0 for v in team2_stats.values()]

    low = []
    high = []

    for i, param in enumerate(params):
        val1 = team1_values[i]
        val2 = team2_values[i]

        min_val = min(val1, val2)
        max_val = max(val1, val2)

        range_pad = (max_val - min_val) * 0.2 if max_val > min_val else max_val * 0.2
        low.append(max(0, min_val - range_pad))
        high.append(max_val + range_pad)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### ⚔️ {team1} Match Performance")
        png1 = get_cached_radar_chart(_client, match_id, team1, '#1f77b4', params, low, high, team1_values)
        st.image(png1, use_container_width=True)

    with col2:
        st.markdown(f"#### ⚔️ {team2} Match Performance")
        png2 = get_cached_radar_chart(_client, match_id, team2, '#ff7f0e', params, low, high, team2_values)
        st.image(png2, use_container_width=True)


@st.cache_data(ttl=600)
def get_cached_progressive_actions_map(_client, match_id: int, team: str, arrow_color: str, carry_color: str) -> bytes:
    from fifa_metrics_bq import get_match_progressive_actions
    from mplsoccer import Pitch
    import matplotlib.pyplot as plt
    from bigquery_helpers import fig_to_png_bytes

    team_actions = get_match_progressive_actions(_client, match_id, team)

    pitch = Pitch(
        pitch_type='statsbomb',
        pitch_color='#0e1116',
        line_color='white',
        linewidth=2
    )

    fig, ax = pitch.draw(figsize=(10, 7))
    fig.patch.set_facecolor('#0e1116')

    if team_actions.empty:
        ax.text(60, 40, "No progressive actions recorded",
                ha='center', va='center', color='white', fontsize=14, fontproperties=font_play)
    else:
        prog_passes = team_actions[team_actions['action_type'] == 'Progressive Pass']
        if not prog_passes.empty:
            pitch.arrows(
                prog_passes['x'], prog_passes['y'],
                prog_passes['end_x'], prog_passes['end_y'],
                ax=ax,
                width=2,
                headwidth=4,
                headlength=4,
                color=arrow_color,
                alpha=0.6,
                label='Progressive Pass'
            )

        prog_carries = team_actions[team_actions['action_type'] == 'Progressive Carry']
        if not prog_carries.empty:
            pitch.arrows(
                prog_carries['x'], prog_carries['y'],
                prog_carries['end_x'], prog_carries['end_y'],
                ax=ax,
                width=2,
                headwidth=4,
                headlength=4,
                color=carry_color,
                alpha=0.6,
                label='Progressive Carry'
            )

        ax.legend(
            loc='upper left',
            fontsize=10,
            framealpha=0.8,
            facecolor='#0e1116',
            edgecolor='white',
            labelcolor='white',
            prop={'family': 'Play', 'size': 10}
        )

    ax.set_title(
        f'{team} - Progressive Actions',
        fontsize=16,
        fontweight='bold',
        color='white',
        fontproperties=font_play_bold,
        pad=20
    )

    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes


def create_match_progressive_actions_map(_client: bigquery.Client, match_id: int, team1: str, team2: str):
    from fifa_metrics_bq import get_match_progressive_actions

    team1_actions = get_match_progressive_actions(_client, match_id, team1)
    team2_actions = get_match_progressive_actions(_client, match_id, team2)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {team1}")
        passes_count = len(team1_actions[team1_actions['action_type'] == 'Progressive Pass']) if not team1_actions.empty else 0
        carries_count = len(team1_actions[team1_actions['action_type'] == 'Progressive Carry']) if not team1_actions.empty else 0
        st.markdown(f"**Progressive Passes:** {passes_count} | **Progressive Carries:** {carries_count}")
        
        png1 = get_cached_progressive_actions_map(_client, match_id, team1, '#1f77b4', '#ff7f0e')
        st.image(png1, use_container_width=True)

    with col2:
        st.markdown(f"### {team2}")
        passes_count = len(team2_actions[team2_actions['action_type'] == 'Progressive Pass']) if not team2_actions.empty else 0
        carries_count = len(team2_actions[team2_actions['action_type'] == 'Progressive Carry']) if not team2_actions.empty else 0
        st.markdown(f"**Progressive Passes:** {passes_count} | **Progressive Carries:** {carries_count}")
        
        png2 = get_cached_progressive_actions_map(_client, match_id, team2, '#1f77b4', '#ff7f0e')
        st.image(png2, use_container_width=True)


def create_match_playing_styles_scatter(_client: bigquery.Client, match_id: int, team1: str, team2: str):
    from fifa_metrics_bq import get_match_playing_styles
    import plotly.graph_objects as go

    styles_df = get_match_playing_styles(_client, match_id)

    if styles_df.empty:
        st.warning("No playing styles data available for this match")
        return None

    fig = go.Figure()

    for idx, row in styles_df.iterrows():
        team_name = row['team']

        net_xg = row['net_xg']
        if net_xg > 0.5:
            color = '#2ca02c'
        elif net_xg < -0.5:
            color = '#d62728'
        else:
            color = '#7f7f7f'

        size = max(20, row['possession_pct'] * 0.8)

        fig.add_trace(go.Scatter(
            x=[row['field_tilt_pct']],
            y=[row['ppda']],
            mode='markers+text',
            name=team_name,
            marker=dict(
                size=size,
                color=color,
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=team_name,
            textposition='top center',
            textfont=dict(
                family='Play',
                size=14,
                color='white'
            ),
            hovertemplate=(
                f'<b>{team_name}</b><br>'
                'Field Tilt: %{x:.1f}%<br>'
                'PPDA: %{y:.2f}<br>'
                f'Net xG: {net_xg:+.2f}<br>'
                f'Possession: {row["possession_pct"]:.1f}%<br>'
                '<extra></extra>'
            )
        ))

    fig.update_layout(
        title=dict(
            text='Playing Styles Analysis - Match Tactics',
            font=dict(family='Play', size=20, color='white'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(text='Field Tilt % (Attacking Territory)', font=dict(family='Play', size=14, color='white')),
            tickfont=dict(family='Play', size=12, color='white'),
            gridcolor='#333333',
            showgrid=True,
            zeroline=False,
            range=[35, 65]
        ),
        yaxis=dict(
            title=dict(text='PPDA (Pressing Intensity - Lower = More Pressing)', font=dict(family='Play', size=14, color='white')),
            tickfont=dict(family='Play', size=12, color='white'),
            gridcolor='#333333',
            showgrid=True,
            zeroline=False,
            autorange='reversed'
        ),
        plot_bgcolor='#0e1116',
        paper_bgcolor='#0e1116',
        font=dict(family='Play', color='white'),
        showlegend=False,
        height=500,
        margin=dict(l=80, r=80, t=100, b=80),
        annotations=[
            dict(
                x=0.25, y=0.95,
                xref='paper', yref='paper',
                text='High Press + Defensive',
                showarrow=False,
                font=dict(family='Play', size=11, color='#888888'),
                xanchor='center'
            ),
            dict(
                x=0.75, y=0.95,
                xref='paper', yref='paper',
                text='High Press + Attacking',
                showarrow=False,
                font=dict(family='Play', size=11, color='#888888'),
                xanchor='center'
            ),
            dict(
                x=0.25, y=0.05,
                xref='paper', yref='paper',
                text='Low Press + Defensive',
                showarrow=False,
                font=dict(family='Play', size=11, color='#888888'),
                xanchor='center'
            ),
            dict(
                x=0.75, y=0.05,
                xref='paper', yref='paper',
                text='Low Press + Attacking',
                showarrow=False,
                font=dict(family='Play', size=11, color='#888888'),
                xanchor='center'
            )
        ]
    )

    return fig


@st.cache_data(ttl=600)
def get_cached_shot_map(_client: bigquery.Client, team: str, competition: Optional[str] = None, match_id: Optional[int] = None) -> bytes:
    from bigquery_helpers import fig_to_png_bytes
    fig, ax = create_shot_map(_client, team, competition=competition, match_id=match_id)
    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes


@st.cache_data(ttl=600)
def get_cached_pass_network(_client: bigquery.Client, team: str, match_id: int, half: Optional[int] = None) -> bytes:
    from bigquery_helpers import fig_to_png_bytes
    fig, ax = create_pass_network(_client, team, match_id, half=half)
    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes


@st.cache_data(ttl=600)
def get_cached_touch_heatmap(_client: bigquery.Client, team: str, competition: Optional[str] = None, player: Optional[str] = None, match_id: Optional[int] = None) -> bytes:
    from bigquery_helpers import fig_to_png_bytes
    fig, ax = create_touch_heatmap(_client, team, competition=competition, player=player, match_id=match_id)
    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes


@st.cache_data(ttl=600)
def get_cached_attacking_passes(_client: bigquery.Client, team: str, competition: Optional[str] = None, match_id: Optional[int] = None) -> bytes:
    from bigquery_helpers import fig_to_png_bytes
    fig, axs = plot_attacking_passes(_client, team, competition=competition, match_id=match_id)
    png_bytes = fig_to_png_bytes(fig)
    plt.close(fig)
    return png_bytes

