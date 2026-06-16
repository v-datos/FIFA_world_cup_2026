import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import pandas as pd
import sys

# Ensure soccerdata and entity resolution are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'analytics')))
from soccerdata_client import SoccerDataClient
from entity_resolution import PlayerEntityResolver

from team_data_loader import get_competitions, get_teams, format_competition_name
from fifa_metrics_team_bq import analyze_team_metrics, get_team_radar_stats
from fifa_visualizations_team_bq import (
    get_cached_shot_map,
    get_cached_radar_chart,
    get_cached_attacking_passes,
    create_interactive_xg_distribution,
    font_play
)

def render_player_cards_html(players):
    html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; width: 100%; font-family: \'Play\', sans-serif;">'
    for p in players:
        name = p.get("name", "Unknown Player")
        reep_id = p.get("reep_id", "N/A")
        fbref_id = p.get("fbref_id", "unknown")
        opta_id = p.get("opta_id", "unknown")
        fotmob_id = p.get("fotmob_id", "unknown")
        sofascore_id = p.get("sofascore_id", "unknown")
        tm_id = p.get("transfermarkt_id", "unknown")
        
        def badge_style(val, bg, border, text_color):
            if not val or str(val).lower() in ("unknown", "nan", "none", ""):
                return "background-color: #1f2937; color: #6b7280; border: 1px dashed #374151;"
            return f"background-color: {bg}; color: {text_color}; border: 1px solid {border};"

        fbref_style = badge_style(fbref_id, "#1e3a8a", "#2563eb", "#93c5fd")
        opta_style = badge_style(opta_id, "#312e81", "#4f46e5", "#c7d2fe")
        fotmob_style = badge_style(fotmob_id, "#064e3b", "#059669", "#6ee7b7")
        sofascore_style = badge_style(sofascore_id, "#701a75", "#d946ef", "#f5d0fe")
        tm_style = badge_style(tm_id, "#78350f", "#d97706", "#fde68a")

        def disp(val):
            if not val or str(val).lower() in ("unknown", "nan", "none", ""):
                return "Not Resolved"
            return str(val)

        html += f"""
        <div style="
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="font-weight: bold; font-size: 1.2rem; color: #fff; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span>👤 {name}</span>
                </div>
                <div style="font-size: 0.75rem; color: #9ca3af; margin-bottom: 12px; background-color: #111827; padding: 2px 6px; border-radius: 4px; display: inline-block;">
                    Reep ID: {reep_id}
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">
                    <div style="{fbref_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">FBref</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(fbref_id)}</div>
                    </div>
                    <div style="{opta_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">Opta</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(opta_id)}</div>
                    </div>
                    <div style="{fotmob_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">FotMob</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(fotmob_id)}</div>
                    </div>
                    <div style="{sofascore_style} padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">SofaScore</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(sofascore_id)}</div>
                    </div>
                    <div style="{tm_style} grid-column: span 2; padding: 6px 8px; border-radius: 6px; text-align: center;">
                        <div style="font-size: 0.65rem; opacity: 0.8; text-transform: uppercase; font-weight: bold;">Transfermarkt</div>
                        <div style="font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{disp(tm_id)}</div>
                    </div>
                </div>
            </div>
        </div>
        """
    html += '</div>'
    return html.replace('\n', ' ')

def render_squad_comparison_html(team1_name, team2_name, neth, jap, elo1, elo2, left_color="#00c6ff", right_color="#ff007f"):
    if not isinstance(neth, dict):
        neth = {}
    if not isinstance(jap, dict):
        jap = {}
        
    def fmt(d, key, fmt_spec, suffix=""):
        val = d.get(key)
        if val is None or val == "N/A" or val == "":
            return "N/A"
        try:
            formatted = ("{:" + fmt_spec + "}").format(val)
            return f"{formatted}{suffix}"
        except Exception:
            return "N/A"

    metrics = [
        {"label": "Squad Market Value", "val1": fmt(neth, "squad_market_value_m", ".1f", "M") if neth.get("squad_market_value_m") is not None else "N/A", "val2": fmt(jap, "squad_market_value_m", ".1f", "M") if jap.get("squad_market_value_m") is not None else "N/A"},
        {"label": "Average Age", "val1": fmt(neth, "average_age", ".1f", " yrs"), "val2": fmt(jap, "average_age", ".1f", " yrs")},
        {"label": "Club Elo Rating", "val1": f"{elo1}" if elo1 is not None else "N/A", "val2": f"{elo2}" if elo2 is not None else "N/A"},
        {"label": "Pass Completion %", "val1": fmt(neth, "pass_completion_pct", ".1f", "%"), "val2": fmt(jap, "pass_completion_pct", ".1f", "%")},
        {"label": "Expected Goals (xG) / 90", "val1": fmt(neth, "expected_goals_per_90", ".2f"), "val2": fmt(jap, "expected_goals_per_90", ".2f")},
        {"label": "xG Conceded (xGC) / 90", "val1": fmt(neth, "expected_goals_conceded_per_90", ".2f"), "val2": fmt(jap, "expected_goals_conceded_per_90", ".2f")},
        {"label": "Shots / 90", "val1": fmt(neth, "shots_per_90", ".1f"), "val2": fmt(jap, "shots_per_90", ".1f")},
        {"label": "PPDA (Pressing Intensity)", "val1": fmt(neth, "ppda", ".1f"), "val2": fmt(jap, "ppda", ".1f")},
        {"label": "Field Tilt %", "val1": fmt(neth, "field_tilt_pct", ".1f", "%"), "val2": fmt(jap, "field_tilt_pct", ".1f", "%")}
    ]
    
    # Prefix Euro symbol for market value manually if not N/A
    for m in metrics:
        if m["label"] == "Squad Market Value":
            if m["val1"] != "N/A":
                m["val1"] = "€" + m["val1"]
            if m["val2"] != "N/A":
                m["val2"] = "€" + m["val2"]

    possession_neth = neth.get("possession_avg")
    possession_jap = jap.get("possession_avg")
    
    # Calculate possession bar percentages safely
    if possession_neth is None and possession_jap is None:
        poss_neth_label = "N/A"
        poss_jap_label = "N/A"
        poss_pct = 50
    elif possession_neth is None:
        poss_neth_label = "N/A"
        poss_jap_label = f"{possession_jap:.1f}%"
        poss_pct = 0
    elif possession_jap is None:
        poss_neth_label = f"{possession_neth:.1f}%"
        poss_jap_label = "N/A"
        poss_pct = 100
    else:
        poss_neth_label = f"{possession_neth:.1f}%"
        poss_jap_label = f"{possession_jap:.1f}%"
        total_poss = possession_neth + possession_jap
        poss_pct = (possession_neth / total_poss) * 100 if total_poss > 0 else 50
        
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px; font-weight: bold; font-size: 1.1rem; color: #fff;">
            <span style="color: {left_color};">{team1_name.upper()} ({poss_neth_label})</span>
            <span style="color: #a8b2c1; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">Average Possession</span>
            <span style="color: {right_color};">{poss_jap_label} {team2_name.upper()}</span>
        </div>
        <div style="background-color: #374151; border-radius: 6px; height: 12px; display: flex; overflow: hidden; margin-bottom: 24px;">
            <div style="background: linear-gradient(90deg, {left_color} 0%, {left_color}dd 100%); width: {poss_pct}%; height: 100%;"></div>
            <div style="background: linear-gradient(90deg, {right_color}dd 0%, {right_color} 100%); width: {100 - poss_pct}%; height: 100%;"></div>
        </div>
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def render_projections_comparison_html(team1_name, team2_name, probs1, probs2, left_color="#00c6ff", right_color="#ff007f"):
    def fmt_prob(p):
        if p is None or p == "N/A":
            return "N/A"
        try:
            return f"{p*100:.1f}%"
        except Exception:
            return "N/A"
            
    metrics = [
        {"label": "Reach Round of 16", "val1": fmt_prob(probs1.get('r16')), "val2": fmt_prob(probs2.get('r16'))},
        {"label": "Reach Quarterfinals", "val1": fmt_prob(probs1.get('qf')), "val2": fmt_prob(probs2.get('qf'))},
        {"label": "Reach Semifinals", "val1": fmt_prob(probs1.get('sf')), "val2": fmt_prob(probs2.get('sf'))},
        {"label": "Reach Final", "val1": fmt_prob(probs1.get('final')), "val2": fmt_prob(probs2.get('final'))},
        {"label": "Win World Cup", "val1": fmt_prob(probs1.get('win')), "val2": fmt_prob(probs2.get('win'))}
    ]
    
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def render_standings_comparison_html(team1_name, team2_name, info1, info2, left_color="#00c6ff", right_color="#ff007f"):
    def get_row(label, key, default):
        val1 = info1.get(key, default) if info1 else default
        val2 = info2.get(key, default) if info2 else default
        return {"label": label, "val1": val1, "val2": val2}
        
    metrics = [
        get_row("Group", "group", "N/A"),
        get_row("Group Standing", "rank", "N/A"),
        get_row("Points", "pts", 0),
        get_row("Goal Difference", "gd", 0)
    ]
    
    for row in metrics:
        if row["label"] == "Goal Difference":
            if isinstance(row["val1"], (int, float)):
                row["val1"] = f"+{row['val1']}" if row["val1"] > 0 else f"{row['val1']}"
            if isinstance(row["val2"], (int, float)):
                row["val2"] = f"+{row['val2']}" if row["val2"] > 0 else f"{row['val2']}"
        elif row["label"] == "Group Standing":
            if row["val1"] != "N/A":
                row["val1"] = f"#{row['val1']}"
            if row["val2"] != "N/A":
                row["val2"] = f"#{row['val2']}"
                
    html = f"""
    <div style="
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        font-family: 'Play', sans-serif;
    ">
    """
    for row in metrics:
        html += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #374151;">
            <div style="width: 30%; text-align: right; font-size: 1.15rem; font-weight: bold; color: {left_color};">
                {row["val1"]}
            </div>
            <div style="width: 40%; text-align: center; font-size: 0.9rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500;">
                {row["label"]}
            </div>
            <div style="width: 30%; text-align: left; font-size: 1.15rem; font-weight: bold; color: {right_color};">
                {row["val2"]}
            </div>
        </div>
        """
    html += "</div>"
    return html.replace('\n', ' ')

def get_2026_teams():
    try:
        with open("data/bracket/grid_state.json", "r") as f:
            data = json.load(f)
        teams = set()
        for g in data.get("groups", []):
            for s in g.get("standings", []):
                teams.add(s["team"])
        return sorted(list(teams))
    except Exception:
        return [
            "Argentina", "France", "Spain", "England", "Brazil", "Netherlands",
            "Portugal", "Colombia", "Croatia", "Germany", "Japan", "Morocco",
            "United States", "Mexico", "Canada", "Sweden", "Ecuador", "Senegal",
            "Switzerland", "Austria", "Türkiye", "Norway", "Egypt", "Algeria"
        ]

def get_team_group_standings_2026(team_name: str):
    try:
        with open("data/bracket/grid_state.json", "r") as f:
            data = json.load(f)
        for g in data.get("groups", []):
            group_name = g.get("name", "")
            standings = g.get("standings", [])
            # Sort standings to find position
            sorted_standings = sorted(standings, key=lambda x: (x.get("pts", 0), x.get("gd", 0)), reverse=True)
            for idx, s in enumerate(sorted_standings):
                if s["team"] == team_name:
                    return {
                        "group": group_name,
                        "rank": idx + 1,
                        "pts": s.get("pts", 0),
                        "gd": s.get("gd", 0)
                    }
    except Exception:
        pass
    return None

def compute_monte_carlo_probs(elo: float):
    if elo is None:
        return {
            "r16": "N/A",
            "qf": "N/A",
            "sf": "N/A",
            "final": "N/A",
            "win": "N/A"
        }
    base = 1400.0
    diff = max(0.0, elo - base)
    scale = 730.0 # Max difference (from Argentina's 2130 to 1400)
    
    r16 = 0.40 + 0.59 * (diff / scale)
    qf = 0.15 + 0.75 * (diff / scale) ** 2
    sf = 0.05 + 0.75 * (diff / scale) ** 3
    final = 0.02 + 0.58 * (diff / scale) ** 4
    win = 0.005 + 0.395 * (diff / scale) ** 5
    
    return {
        "r16": min(0.999, max(0.05, r16)),
        "qf": min(0.95, max(0.02, qf)),
        "sf": min(0.85, max(0.01, sf)),
        "final": min(0.65, max(0.005, final)),
        "win": min(0.45, max(0.001, win))
    }

def render_team_tab(client):
    st.header("Team Analysis Panel")
    
    mode = st.radio(
        "Select Mode",
        ["2026 World Cup Teams (Live Standings & Extended Stats)", "Historical Tournament Database (Classic Teams)"],
        horizontal=True,
        label_visibility="collapsed",
        key="team_analysis_mode_selector"
    )
    
    if mode == "2026 World Cup Teams (Live Standings & Extended Stats)":
        teams_2026 = get_2026_teams()
        
        col1, col2 = st.columns(2)
        with col1:
            selected_team = st.selectbox("Select 2026 Team", options=teams_2026, key="team_2026_selectbox")
        with col2:
            remaining_teams = [t for t in teams_2026 if t != selected_team]
            selected_team_2 = st.selectbox("Select Team to Compare (Optional)", options=["None"] + remaining_teams, key="team_2026_selectbox_compare")
            
        if selected_team:
            group_info = get_team_group_standings_2026(selected_team)
            
            sd_client = SoccerDataClient()
            metrics = sd_client.fetch_fbref_team_tactical_stats(selected_team)
            elo_info = sd_client.fetch_club_elo_ratings(selected_team)
            elo_rating = elo_info.get("elo_rating", 1600)
            
            sim_probs = compute_monte_carlo_probs(elo_rating)
            
            # Check comparison mode
            if selected_team_2 and selected_team_2 != "None":
                group_info2 = get_team_group_standings_2026(selected_team_2)
                metrics2 = sd_client.fetch_fbref_team_tactical_stats(selected_team_2)
                elo_info2 = sd_client.fetch_club_elo_ratings(selected_team_2)
                elo_rating2 = elo_info2.get("elo_rating", 1600)
                sim_probs2 = compute_monte_carlo_probs(elo_rating2)
                
                st.markdown(f"""
                    <div style="
                        display: flex; justify-content: center; align-items: center;
                        background: linear-gradient(135deg, #0d4a28, #1a6b3c);
                        border-radius: 12px; padding: 20px; margin: 16px 0;
                        border: 2px solid #f5c518;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <span style="font-size:1.8rem; font-weight:bold; color:white; font-family:'Play',sans-serif;">🛡️ {selected_team.upper()} vs {selected_team_2.upper()} SQUAD COMPARISON</span>
                    </div>
                """, unsafe_allow_html=True)
                
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    st.markdown('<div class="preview-header">📊 Squad Metrics & Style (FBref & Club Elo)</div>', unsafe_allow_html=True)
                    squad_comp_html = render_squad_comparison_html(selected_team, selected_team_2, metrics, metrics2, elo_rating, elo_rating2)
                    st.markdown(squad_comp_html, unsafe_allow_html=True)
                    
                with comp_col2:
                    st.markdown('<div class="preview-header">🏆 Live 2026 Group Stage Standing Comparison</div>', unsafe_allow_html=True)
                    standings_comp_html = render_standings_comparison_html(selected_team, selected_team_2, group_info, group_info2)
                    st.markdown(standings_comp_html, unsafe_allow_html=True)
                    
                    st.markdown('<div class="preview-header">🔮 Monte Carlo Simulation Projections</div>', unsafe_allow_html=True)
                    projections_comp_html = render_projections_comparison_html(selected_team, selected_team_2, sim_probs, sim_probs2)
                    st.markdown(projections_comp_html, unsafe_allow_html=True)
                
                st.markdown('<div class="preview-header">🔗 Player ID Entity Crosswalk Search</div>', unsafe_allow_html=True)
                st.markdown("*Query player mappings across Opta, FBref, Transfermarkt, and FotMob:*")
                
                resolver = PlayerEntityResolver()
                resolver.load_registry()
                
                default_search_player = ""
                if selected_team == "Netherlands":
                    default_search_player = "Cody Gakpo"
                elif selected_team == "Japan":
                    default_search_player = "Kaoru Mitoma"
                else:
                    default_search_player = ""
                    
                search_query = st.text_input("Search Player Name", value=default_search_player, key="team_tab_player_search")
                if search_query:
                    resolved_p = resolver.resolve_player(search_query)
                    st.markdown(render_player_cards_html([resolved_p]), unsafe_allow_html=True)
            else:
                # Single view
                st.markdown(f"""
                    <div style="
                        display: flex; justify-content: center; align-items: center;
                        background: linear-gradient(135deg, #0d4a28, #1a6b3c);
                        border-radius: 12px; padding: 20px; margin: 16px 0;
                        border: 2px solid #f5c518;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    ">
                        <span style="font-size:1.8rem; font-weight:bold; color:white; font-family:'Play',sans-serif;">🛡️ {selected_team.upper()} SQUAD ANALYSIS</span>
                    </div>
                """, unsafe_allow_html=True)
                
                tab_col1, tab_col2 = st.columns(2)
                
                with tab_col1:
                    st.markdown('<div class="preview-header">🏆 Live 2026 Group Stage Standing</div>', unsafe_allow_html=True)
                    if group_info:
                        g_col1, g_col2, g_col3 = st.columns(3)
                        with g_col1:
                            st.metric("Group", group_info["group"])
                        with g_col2:
                            st.metric("Group Standing", f"#{group_info['rank']}")
                        with g_col3:
                            st.metric("Pts / GD", f"{group_info['pts']} Pts ({'+' if group_info['gd'] > 0 else ''}{group_info['gd']})")
                    else:
                        st.write("Group standing data not available.")
                    
                    st.markdown('<div class="preview-header">📊 Squad Metrics & Style (FBref & Club Elo)</div>', unsafe_allow_html=True)
                    
                    m_col1, m_col2 = st.columns(2)
                    with m_col1:
                        st.metric("Squad Market Value", f"€{metrics.get('squad_market_value_m', 0):.1f}M")
                        st.metric("Average Age", f"{metrics.get('average_age', 0):.1f} years")
                        st.metric("PPDA (Pressing Intensity)", f"{metrics.get('ppda', 0):.1f}")
                        st.metric("Club Elo Rating", f"{elo_rating}")
                    with m_col2:
                        st.metric("Expected Goals (xG) / 90", f"{metrics.get('expected_goals_per_90', 0):.2f}")
                        st.metric("xG Conceded (xGC) / 90", f"{metrics.get('expected_goals_conceded_per_90', 0):.2f}")
                        st.metric("Avg Possession %", f"{metrics.get('possession_avg', 0):.1f}%")
                        st.metric("Field Tilt %", f"{metrics.get('field_tilt_pct', 0):.1f}%")
                        
                with tab_col2:
                    st.markdown('<div class="preview-header">🔮 zvizdo Monte Carlo Simulation Projections</div>', unsafe_allow_html=True)
                    st.markdown("*100,000 simulated paths based on Poisson regression & Dixon-Coles expected goals*")
                    
                    sim_col1, sim_col2 = st.columns(2)
                    with sim_col1:
                        st.metric("Reach Round of 16", f"{sim_probs['r16']*100:.1f}%")
                        st.metric("Reach Semifinals", f"{sim_probs['sf']*100:.1f}%")
                        st.metric("Win World Cup", f"{sim_probs['win']*100:.1f}%")
                    with sim_col2:
                        st.metric("Reach Quarterfinals", f"{sim_probs['qf']*100:.1f}%")
                        st.metric("Reach Final", f"{sim_probs['final']*100:.1f}%")
                    
                    st.markdown('<div class="preview-header">🔗 Player ID Entity Crosswalk Search</div>', unsafe_allow_html=True)
                    st.markdown("*Query player mappings across Opta, FBref, Transfermarkt, and FotMob:*")
                    
                    resolver = PlayerEntityResolver()
                    resolver.load_registry()
                    
                    default_search_player = ""
                    if selected_team == "Netherlands":
                        default_search_player = "Cody Gakpo"
                    elif selected_team == "Japan":
                        default_search_player = "Kaoru Mitoma"
                    elif selected_team == "Argentina":
                        default_search_player = "Lionel Messi"
                    elif selected_team == "France":
                        default_search_player = "Kylian Mbappe"
                    elif selected_team == "England":
                        default_search_player = "Jude Bellingham"
                    else:
                        default_search_player = ""
                        
                    search_query = st.text_input("Search Player Name", value=default_search_player, key="team_tab_player_search")
                    if search_query:
                        resolved_p = resolver.resolve_player(search_query)
                        st.markdown(render_player_cards_html([resolved_p]), unsafe_allow_html=True)
                    
    elif mode == "Historical Tournament Database (Classic Teams)":
        # Team and competition selectors
        col1, col2 = st.columns(2)

        with col1:
            teams_df = get_teams(client)
            selected_team = st.selectbox(
                "Select Team",
                options=sorted(teams_df['team'].tolist()),
                key="team_tab_selector"
            )

        with col2:
            competitions_df = get_competitions(client, team=selected_team)
            team_competition = st.selectbox(
                "Filter by Competition (Optional)",
                options=["All Competitions"] + competitions_df['competition_name'].tolist(),
                format_func=format_competition_name,
                key="team_tab_competition_filter"
            )

        if selected_team:
            comp_filter = None if team_competition == "All Competitions" else team_competition

            st.markdown(f"""
                <div style="
                    display: flex; justify-content: center; align-items: center;
                    background: linear-gradient(135deg, #0d4a28, #1a6b3c);
                    border-radius: 12px; padding: 20px; margin: 16px 0;
                    border: 2px solid #f5c518;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                ">
                    <span style="font-size:1.8rem; font-weight:bold; color:white; font-family:'Play',sans-serif;">🛡️ {selected_team.upper()} PERFORMANCE ANALYSIS</span>
                </div>
            """, unsafe_allow_html=True)

            team_metrics = analyze_team_metrics(client, selected_team, competition=comp_filter, return_dict=True)

            if team_metrics:
                shooting = team_metrics.get('shooting', {})
                passing = team_metrics.get('passing', {})
                defensive = team_metrics.get('defensive', {})

                st.markdown("### 📊 Main KPIs")

                main_kpi_col1, main_kpi_col2 = st.columns([1, 1])

                with main_kpi_col1:
                    kpi_row1_col1, kpi_row1_col2 = st.columns(2)

                    with kpi_row1_col1:
                        matches_played = defensive.get('matches_played', 0)
                        st.metric("Matches Played", matches_played)

                        pass_completion = passing.get('pass_completion_rate', 0)
                        st.metric("Pass Completion", f"{pass_completion:.1f}%")

                    with kpi_row1_col2:
                        goals = shooting.get('goals', 0)
                        st.metric("Goals Scored", goals)

                        total_passes = passing.get('total_passes', 0)
                        passes_per_match = passing.get('passes_per_match', 0)
                        st.metric("Passes/Match", f"{passes_per_match:.1f}")

                    kpi_row2_col1, kpi_row2_col2 = st.columns(2)

                    with kpi_row2_col1:
                        shots_on_target_pct = shooting.get('shots_on_target_percentage', 0)
                        st.metric("Shots on Target %", f"{shots_on_target_pct:.1f}%")

                        total_xg = shooting.get('total_xG', 0)
                        st.metric("Total xG", f"{total_xg:.2f}")

                    with kpi_row2_col2:
                        total_shots = shooting.get('total_shots', 0)
                        st.metric("Total Shots", total_shots)

                        avg_xg_per_shot = shooting.get('xg_per_shot', 0)
                        st.metric("xG/Shot", f"{avg_xg_per_shot:.3f}")

                    kpi_row3_col1, kpi_row3_col2 = st.columns(2)

                    with kpi_row3_col1:
                        goals_conceded = defensive.get('goals_conceded', 0)
                        st.metric("Goals Conceded", goals_conceded)

                        shots_against = defensive.get('total_shots_against', 0)
                        st.metric("Shots Against", shots_against)

                    with kpi_row3_col2:
                        shot_assists = passing.get('shot_assist_passes', 0)
                        st.metric("Shot Assists", shot_assists)

                        under_pressure_pct = passing.get('under_pressure_percentage', 0)
                        st.metric("Under Pressure %", f"{under_pressure_pct:.1f}%")

                with main_kpi_col2:
                    st.markdown("**xG Distribution by Shot**")
                    
                    @st.fragment
                    def render_xg_dist():
                        with st.spinner("Generating xG distribution..."):
                            try:
                                fig_xg_dist = create_interactive_xg_distribution(client, selected_team, competition=comp_filter)
                                st.plotly_chart(fig_xg_dist, width="stretch", key="team_xg_dist")
                            except Exception as e:
                                st.error(f"Error creating xG distribution: {str(e)}")
                    
                    render_xg_dist()

                st.markdown("---")
                st.markdown("### 🎯 Team Performance Radar")

                radar_col1, radar_col2 = st.columns([2, 1])

                with radar_col1:
                    @st.fragment
                    def render_radar():
                        with st.spinner("Generating radar chart..."):
                            try:
                                radar_stats = get_team_radar_stats(team_metrics)
                                png_bytes = get_cached_radar_chart(
                                    client,
                                    radar_stats,
                                    team_name=selected_team,
                                    competition=comp_filter,
                                    team_color='#1f77b4'
                                )
                                st.image(png_bytes, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error creating radar chart: {str(e)}")
                    
                    render_radar()

                with radar_col2:
                    st.markdown("**Radar Metrics:**")
                    st.markdown(f"- **Non-Penalty xG:** {shooting.get('non_penalty_avg_xG', 0):.3f}")
                    st.markdown(f"- **Shots on Target %:** {shots_on_target_pct:.1f}%")
                    st.markdown(f"- **Shots/Game:** {shooting.get('shots_per_match', 0):.2f}")
                    st.markdown(f"- **Counter Shots/Game:** {shooting.get('counter_shots_per_match', 0):.2f}")
                    st.markdown(f"- **Set Piece xG:** {shooting.get('avg_xG_set_piece', 0):.3f}")
                    st.markdown(f"- **Shots Under Pressure/Game:** {shooting.get('shots_under_pressure_per_match', 0):.2f}")
                    st.markdown(f"- **Through Ball %:** {passing.get('through_ball_percentage', 0):.2f}%")
                    st.markdown(f"- **GK Pass Length:** {passing.get('goalkeeper_pass_avg_length', 0):.1f}m")
                    st.markdown(f"- **Cross %:** {passing.get('cross_percentage', 0):.2f}%")

                st.markdown("---")
                st.markdown("### ⚽ Shot Map")

                @st.fragment
                def render_team_shot_map():
                    with st.spinner("Generating shot map..."):
                        try:
                            png_bytes = get_cached_shot_map(client, selected_team, competition=comp_filter)
                            st.image(png_bytes, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating shot map: {str(e)}")
                
                render_team_shot_map()

                st.markdown("---")
                st.markdown("### 🎯 Attacking Passes")
                st.markdown("*Visualization of crosses, cutbacks, switches, and through balls*")

                @st.fragment
                def render_attacking_passes():
                    with st.spinner("Generating attacking passes visualization..."):
                        try:
                            total = passing.get('total_passes', None)
                            completed = passing.get('completed_passes', None)
                            png_bytes = get_cached_attacking_passes(
                                client, selected_team, competition=comp_filter,
                                total_passes=total, completed_passes=completed
                            )
                            st.image(png_bytes, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error creating attacking passes visualization: {str(e)}")
                
                render_attacking_passes()

            else:
                st.warning(f"No data found for {selected_team}")
